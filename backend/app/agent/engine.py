"""LangGraph Agent 引擎 — 意图识别、Skill 路由、工具调用链。"""

import json
import os
from typing import Literal

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from app.agent.skills import get_all_skills, get_skill
from app.agent.tools import get_all_tools, get_tool
from app.mock.upstream import simulate_upstream_reply
from app.schemas.models import (
    ActionStatus,
    ActionType,
    Channel,
    SessionStatus,
)
from app.store.memory import store


# ── 1. 轻量图状态 ──────────────────────────────────────────────────────────────


class AgentGraphState(TypedDict):
    """Agent 图内部路由状态。MemoryStore 管理完整执行详情。"""

    session_id: str
    trigger_message: str
    matched_intent: str | None
    matched_skill: str | None
    error_message: str | None


# ── 2. LLM 客户端 ──────────────────────────────────────────────────────────────


def _create_llm() -> ChatGoogleGenerativeAI:
    """创建 Gemini LLM 客户端。"""
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=os.environ.get("GOOGLE_API_KEY", ""),
        temperature=0,
    )


_llm = _create_llm()


# 工具调用链最大迭代次数（防止 LLM 无限循环）
MAX_TOOL_ITERATIONS = 20


# ── 3. 节点函数 ────────────────────────────────────────────────────────────────


def intent_recognition_node(state: AgentGraphState) -> dict:
    """节点：意图识别 — 调用 LLM 分析用户消息意图。"""
    action = store.add_action(
        action_type=ActionType.intent_recognition,
        title="意图识别",
        summary="正在分析消息意图…",
        status=ActionStatus.running,
    )
    try:
        skills = get_all_skills()
        skill_list = "\n".join(
            [f"- {s.skill_id}: {s.name} — {s.description}" for s in skills]
        )

        system_prompt = f"""你是一个意图分类器。根据用户消息，识别业务意图。

可用意图（skill_id: 名称 — 描述）：
{skill_list}

规则：
1. 如果消息匹配某个意图，只返回对应的 skill_id（如 early_checkout）
2. 如果无法匹配任何意图，返回 unknown
3. 只返回 skill_id，不要其他内容"""

        response = _llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=state["trigger_message"]),
            ]
        )
        intent = response.content.strip()

        store.update_action_status(
            action.index,
            ActionStatus.success,
            {"intent": intent},
        )
        return {"matched_intent": intent}
    except Exception as e:
        store.update_action_status(
            action.index,
            ActionStatus.error,
            {"error": str(e)},
        )
        return {"matched_intent": None, "error_message": str(e)}


def skill_loading_node(state: AgentGraphState) -> dict:
    """节点：Skill 加载 — 根据意图匹配并加载 Skill。"""
    intent = state.get("matched_intent") or ""
    skill = get_skill(intent)

    if not skill:
        # 未匹配 — 记录失败并设置友好回复
        store.add_action(
            action_type=ActionType.skill_loaded,
            title="Skill 加载",
            summary=f"未匹配到 Skill：{intent}",
            status=ActionStatus.error,
            detail={"intent": intent},
        )
        # 构建已支持场景列表
        all_skills = get_all_skills()
        supported = "、".join([s.name for s in all_skills]) if all_skills else "暂无"
        reply = f"无法处理此请求。当前已支持的场景：{supported}"
        store.set_final_reply(reply)
        store.add_message(
            channel=Channel.chat, sender="agent", content=reply
        )
        return {"matched_skill": None}

    store.add_action(
        action_type=ActionType.skill_loaded,
        title="Skill 加载",
        summary=f"已加载 Skill：{skill.name}",
        status=ActionStatus.success,
        detail={"skill_id": skill.skill_id, "skill_name": skill.name},
    )
    return {"matched_skill": skill.skill_id}


def _build_langchain_tools() -> list:
    """将已注册的 BaseTool 实例包装为 LangChain 工具（仅供 LLM schema 绑定）。"""
    from pydantic import BaseModel, Field, create_model
    from langchain_core.tools import StructuredTool

    # Python type 映射
    _type_map = {"string": str, "integer": int, "number": float, "boolean": bool}

    lc_tools = []
    for bt in get_all_tools():
        def _make_fn(tool_instance):
            def fn(**kwargs) -> str:
                return json.dumps(
                    tool_instance.execute(**kwargs), ensure_ascii=False
                )
            fn.__name__ = tool_instance.name
            fn.__doc__ = tool_instance.description
            return fn

        # 从 BaseTool._get_parameters() 动态构建 Pydantic args_schema
        params = bt._get_parameters()
        field_definitions = {}
        for param_name, param_info in params.items():
            py_type = _type_map.get(param_info.get("type", "string"), str)
            description = param_info.get("description", "")
            field_definitions[param_name] = (py_type, Field(description=description))

        args_schema = create_model(
            f"{bt.name}_schema", **field_definitions
        )

        lc_tools.append(
            StructuredTool.from_function(
                func=_make_fn(bt),
                name=bt.name,
                description=bt.description,
                args_schema=args_schema,
            )
        )
    return lc_tools


def tool_chain_execution_node(state: AgentGraphState) -> dict:
    """节点：工具调用链执行 — LLM 驱动的多步工具调用。"""
    skill = get_skill(state["matched_skill"])
    if not skill:
        return {"error_message": f"Skill {state['matched_skill']} not found"}

    lc_tools = _build_langchain_tools()
    llm_with_tools = _llm.bind_tools(lc_tools)

    messages: list = [
        SystemMessage(content=skill.content),
        HumanMessage(content=state["trigger_message"]),
    ]

    # 用于追踪 supplier_order_id（上游回复需要）
    supplier_order_id = None
    iteration_count = 0

    while True:
        iteration_count += 1
        if iteration_count > MAX_TOOL_ITERATIONS:
            error_msg = f"工具调用链超过最大迭代次数 {MAX_TOOL_ITERATIONS}"
            store.add_action(
                action_type=ActionType.tool_call,
                title="迭代超限",
                summary=error_msg,
                status=ActionStatus.error,
            )
            store.set_final_reply(f"处理失败：{error_msg}")
            store.add_message(
                channel=Channel.chat,
                sender="agent",
                content=f"处理失败：{error_msg}",
            )
            return {"error_message": error_msg}

        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            # LLM 完成工具调用 — 提取最终回复
            if response.content:
                store.set_final_reply(response.content)
                # 在 chat 频道记录 Agent 回复
                store.add_message(
                    channel=Channel.chat,
                    sender="agent",
                    content=response.content,
                )
            break

        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]

            # 记录工具调用开始
            action = store.add_action(
                action_type=ActionType.tool_call,
                title=f"调用工具：{tool_name}",
                summary=json.dumps(tool_args, ensure_ascii=False),
                status=ActionStatus.running,
                detail={"input": tool_args},
            )

            try:
                # 直接通过 BaseTool 执行（不经过 LangChain 包装）
                base_tool = get_tool(tool_name)
                if not base_tool:
                    raise ValueError(f"工具 {tool_name} 不存在")

                result = base_tool.execute(**tool_args)
                result_str = json.dumps(result, ensure_ascii=False)

                # 检查工具返回是否有错误
                if result.get("error"):
                    store.update_action_status(
                        action.index,
                        ActionStatus.error,
                        {"input": tool_args, "output": result},
                    )
                    # 工具错误 — 优雅终止（FR33）
                    error_msg = result.get("message", "工具调用失败")
                    store.set_final_reply(f"处理失败：{error_msg}")
                    store.add_message(
                        channel=Channel.chat,
                        sender="agent",
                        content=f"处理失败：{error_msg}",
                    )
                    messages.append(
                        ToolMessage(
                            content=result_str,
                            tool_call_id=tc["id"],
                        )
                    )
                    return {"error_message": error_msg}

                store.update_action_status(
                    action.index,
                    ActionStatus.success,
                    {"input": tool_args, "output": result},
                )

                # 追踪 supplier_order_id（从 order_query 结果提取）
                if tool_name == "order_query" and result.get("success"):
                    supplier_order_id = result["data"].get("supplier_order_id")

                # 检测是否向 upstream 发送消息 → 触发上游回复模拟
                if (
                    tool_name == "message_send"
                    and tool_args.get("channel") == "upstream"
                ):
                    # 记录等待动作
                    wait_action = store.add_action(
                        action_type=ActionType.waiting,
                        title="等待上游回复",
                        summary="等待供应商处理…",
                        status=ActionStatus.running,
                    )
                    # 模拟上游回复
                    reply_content = simulate_upstream_reply(
                        supplier_order_id or ""
                    )
                    store.update_action_status(
                        wait_action.index,
                        ActionStatus.success,
                        {"reply": reply_content},
                    )
                    # 将上游回复注入 LLM 上下文，供后续步骤决策
                    messages.append(
                        HumanMessage(
                            content=f"上游供应商回复：{reply_content}"
                        )
                    )

                messages.append(
                    ToolMessage(
                        content=result_str,
                        tool_call_id=tc["id"],
                    )
                )

            except Exception as e:
                store.update_action_status(
                    action.index,
                    ActionStatus.error,
                    {"input": tool_args, "error": str(e)},
                )
                messages.append(
                    ToolMessage(
                        content=json.dumps(
                            {"error": True, "message": str(e)},
                            ensure_ascii=False,
                        ),
                        tool_call_id=tc["id"],
                    )
                )
                return {"error_message": str(e)}

    return {}


def completion_node(state: AgentGraphState) -> dict:
    """节点：流程完成 — 更新会话状态并保存历史。"""
    if state.get("error_message"):
        store.update_session_status(SessionStatus.error)
        store.add_action(
            action_type=ActionType.completed,
            title="流程完成",
            summary=f"处理异常终止：{state['error_message']}",
            status=ActionStatus.error,
        )
    else:
        store.update_session_status(SessionStatus.completed)
        store.add_action(
            action_type=ActionType.completed,
            title="流程完成",
            summary="Agent 已完成处理",
            status=ActionStatus.success,
        )

    # 保存执行历史
    skill_name = None
    if state.get("matched_skill"):
        skill = get_skill(state["matched_skill"])
        skill_name = skill.name if skill else None

    store.save_execution_history(
        trigger_message=state["trigger_message"],
        skill_name=skill_name,
    )

    return {}


# ── 4. 路由函数 ────────────────────────────────────────────────────────────────


def _route_after_skill_loading(
    state: AgentGraphState,
) -> Literal["tool_chain_execution", "completion"]:
    """条件路由：Skill 匹配成功 → 工具调用链，否则 → 直接完成。"""
    if state.get("matched_skill"):
        return "tool_chain_execution"
    return "completion"


# ── 5. 构建和编译图 ────────────────────────────────────────────────────────────


def _build_graph() -> StateGraph:
    """构建 LangGraph 状态图。"""
    builder = StateGraph(AgentGraphState)

    builder.add_node("intent_recognition", intent_recognition_node)
    builder.add_node("skill_loading", skill_loading_node)
    builder.add_node("tool_chain_execution", tool_chain_execution_node)
    builder.add_node("completion", completion_node)

    builder.add_edge(START, "intent_recognition")
    builder.add_edge("intent_recognition", "skill_loading")
    builder.add_conditional_edges(
        "skill_loading",
        _route_after_skill_loading,
        {
            "tool_chain_execution": "tool_chain_execution",
            "completion": "completion",
        },
    )
    builder.add_edge("tool_chain_execution", "completion")
    builder.add_edge("completion", END)

    return builder.compile()


_graph = _build_graph()


# ── 6. 公开入口函数 ────────────────────────────────────────────────────────────


async def run_agent(session_id: str, trigger_message: str) -> None:
    """Agent 执行入口。由 /api/chat 路由作为后台任务调用。"""
    store.update_session_status(SessionStatus.running)
    # 在 chat 频道记录用户消息
    store.add_message(
        channel=Channel.chat, sender="user", content=trigger_message
    )

    initial_state: AgentGraphState = {
        "session_id": session_id,
        "trigger_message": trigger_message,
        "matched_intent": None,
        "matched_skill": None,
        "error_message": None,
    }
    try:
        await _graph.ainvoke(initial_state)
    except Exception as e:
        store.update_session_status(SessionStatus.error)
        store.set_final_reply(f"系统错误：{str(e)}")
