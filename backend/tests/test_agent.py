"""Agent 引擎测试 — Skill 注册表、图编译、节点逻辑、端到端集成。"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.models import (
    ActionStatus,
    ActionType,
    Channel,
    SessionStatus,
    SkillDefinition,
)
from app.store.memory import MemoryStore


# === Fixtures ===


@pytest.fixture
def fresh_store(monkeypatch):
    """创建新的 MemoryStore 实例并替换全局单例。"""
    new_store = MemoryStore()
    monkeypatch.setattr("app.store.memory.store", new_store)
    monkeypatch.setattr("app.agent.engine.store", new_store)
    monkeypatch.setattr("app.agent.tools.message_send.store", new_store)
    monkeypatch.setattr("app.mock.upstream.store", new_store)
    return new_store


# === Task 1: Skill 注册表测试 ===


class TestSkillRegistry:
    """测试 Skill 注册表的自动发现和查询功能。"""

    def test_early_checkout_skill_loaded(self):
        """系统启动后 early_checkout Skill 应自动加载。"""
        from app.agent.skills import get_skill

        skill = get_skill("early_checkout")
        assert skill is not None
        assert isinstance(skill, SkillDefinition)
        assert skill.skill_id == "early_checkout"

    def test_early_checkout_skill_name(self):
        """early_checkout Skill 的 name 应为"提前离店"。"""
        from app.agent.skills import get_skill

        skill = get_skill("early_checkout")
        assert skill is not None
        assert skill.name == "提前离店"

    def test_early_checkout_skill_has_description(self):
        """early_checkout Skill 应有非空描述。"""
        from app.agent.skills import get_skill

        skill = get_skill("early_checkout")
        assert skill is not None
        assert len(skill.description) > 0

    def test_early_checkout_skill_content_has_steps(self):
        """early_checkout Skill 内容应包含流程步骤关键词。"""
        from app.agent.skills import get_skill

        skill = get_skill("early_checkout")
        assert skill is not None
        assert "order_query" in skill.content
        assert "message_send" in skill.content
        assert "refund" in skill.content

    def test_get_skill_not_found(self):
        """查询不存在的 Skill 应返回 None。"""
        from app.agent.skills import get_skill

        result = get_skill("nonexistent_skill")
        assert result is None

    def test_get_all_skills_includes_early_checkout(self):
        """get_all_skills 应包含 early_checkout。"""
        from app.agent.skills import get_all_skills

        skills = get_all_skills()
        assert len(skills) >= 1
        skill_ids = [s.skill_id for s in skills]
        assert "early_checkout" in skill_ids

    def test_get_all_skills_returns_skill_definitions(self):
        """get_all_skills 返回的每个元素应为 SkillDefinition。"""
        from app.agent.skills import get_all_skills

        skills = get_all_skills()
        for skill in skills:
            assert isinstance(skill, SkillDefinition)


# === Task 2: AgentGraphState 和图编译测试 ===


class TestAgentGraphState:
    """测试 AgentGraphState 类型定义和图编译。"""

    def test_agent_graph_state_is_typed_dict(self):
        """AgentGraphState 应为 TypedDict。"""
        from app.agent.engine import AgentGraphState

        # TypedDict 创建的类可实例化为 dict
        state: AgentGraphState = {
            "session_id": "test-123",
            "trigger_message": "测试消息",
            "matched_intent": None,
            "matched_skill": None,
            "error_message": None,
        }
        assert state["session_id"] == "test-123"
        assert state["trigger_message"] == "测试消息"

    def test_graph_compiled_successfully(self):
        """LangGraph 状态图应编译成功。"""
        from app.agent.engine import _graph

        assert _graph is not None

    def test_graph_has_expected_nodes(self):
        """编译后的图应包含 4 个节点。"""
        from app.agent.engine import _graph

        nodes = _graph.nodes
        assert "intent_recognition" in nodes
        assert "skill_loading" in nodes
        assert "tool_chain_execution" in nodes
        assert "completion" in nodes


# === Task 3: 意图识别节点测试 ===


class TestIntentRecognitionNode:
    """测试意图识别节点。"""

    def test_intent_recognition_success(self, fresh_store):
        """成功识别意图时应返回 matched_intent 并记录 ActionLogEntry。"""
        from app.agent.engine import intent_recognition_node

        fresh_store.create_session()

        mock_response = MagicMock()
        mock_response.content = "early_checkout"

        with patch("app.agent.engine._llm") as mock_llm:
            mock_llm.invoke.return_value = mock_response
            result = intent_recognition_node(
                {
                    "session_id": "test-1",
                    "trigger_message": "订单号 HT20260301001 的客人申请提前离店",
                    "matched_intent": None,
                    "matched_skill": None,
                    "error_message": None,
                }
            )

        assert result["matched_intent"] == "early_checkout"
        actions = fresh_store.get_actions()
        assert len(actions) == 1
        assert actions[0].action_type == ActionType.intent_recognition
        assert actions[0].status == ActionStatus.success
        assert actions[0].detail["intent"] == "early_checkout"

    def test_intent_recognition_error(self, fresh_store):
        """LLM 调用失败时应记录 error 状态。"""
        from app.agent.engine import intent_recognition_node

        fresh_store.create_session()

        with patch("app.agent.engine._llm") as mock_llm:
            mock_llm.invoke.side_effect = Exception("API Error")
            result = intent_recognition_node(
                {
                    "session_id": "test-1",
                    "trigger_message": "测试",
                    "matched_intent": None,
                    "matched_skill": None,
                    "error_message": None,
                }
            )

        assert result["matched_intent"] is None
        assert "API Error" in result["error_message"]
        actions = fresh_store.get_actions()
        assert actions[0].status == ActionStatus.error

    def test_intent_recognition_records_running_then_success(self, fresh_store):
        """意图识别应先记录 running 状态，完成后更新为 success。"""
        from app.agent.engine import intent_recognition_node

        fresh_store.create_session()

        mock_response = MagicMock()
        mock_response.content = "early_checkout"

        with patch("app.agent.engine._llm") as mock_llm:
            mock_llm.invoke.return_value = mock_response
            intent_recognition_node(
                {
                    "session_id": "test-1",
                    "trigger_message": "提前离店",
                    "matched_intent": None,
                    "matched_skill": None,
                    "error_message": None,
                }
            )

        actions = fresh_store.get_actions()
        # 最终状态应为 success（running → success 更新）
        assert actions[0].status == ActionStatus.success


# === Task 4: Skill 加载节点测试 ===


class TestSkillLoadingNode:
    """测试 Skill 加载节点。"""

    def test_skill_loading_success(self, fresh_store):
        """匹配到 Skill 时应返回 matched_skill 并记录成功。"""
        from app.agent.engine import skill_loading_node

        fresh_store.create_session()
        result = skill_loading_node(
            {
                "session_id": "test-1",
                "trigger_message": "提前离店",
                "matched_intent": "early_checkout",
                "matched_skill": None,
                "error_message": None,
            }
        )

        assert result["matched_skill"] == "early_checkout"
        actions = fresh_store.get_actions()
        assert len(actions) == 1
        assert actions[0].action_type == ActionType.skill_loaded
        assert actions[0].status == ActionStatus.success
        assert "提前离店" in actions[0].summary

    def test_skill_loading_not_found(self, fresh_store):
        """未匹配到 Skill 时应返回 None 并设置友好回复。"""
        from app.agent.engine import skill_loading_node

        fresh_store.create_session()
        result = skill_loading_node(
            {
                "session_id": "test-1",
                "trigger_message": "随便聊聊",
                "matched_intent": "unknown",
                "matched_skill": None,
                "error_message": None,
            }
        )

        assert result["matched_skill"] is None
        actions = fresh_store.get_actions()
        assert actions[0].status == ActionStatus.error
        # 应设置了友好回复
        session = fresh_store.get_session()
        assert session.final_reply is not None
        assert "无法处理" in session.final_reply
        # [M2 修复] 回复也应写入 chat 频道
        chat_msgs = fresh_store.get_messages(Channel.chat)
        assert len(chat_msgs) == 1
        assert chat_msgs[0].sender == "agent"
        assert "无法处理" in chat_msgs[0].content

    def test_skill_loading_with_none_intent(self, fresh_store):
        """intent 为 None 时应视为未匹配。"""
        from app.agent.engine import skill_loading_node

        fresh_store.create_session()
        result = skill_loading_node(
            {
                "session_id": "test-1",
                "trigger_message": "测试",
                "matched_intent": None,
                "matched_skill": None,
                "error_message": None,
            }
        )

        assert result["matched_skill"] is None


# === Task 6: 完成节点测试 ===


class TestCompletionNode:
    """测试流程完成节点。"""

    def test_completion_success(self, fresh_store):
        """无错误时应设置 completed 状态并记录成功。"""
        from app.agent.engine import completion_node

        fresh_store.create_session()
        completion_node(
            {
                "session_id": "test-1",
                "trigger_message": "提前离店",
                "matched_intent": "early_checkout",
                "matched_skill": "early_checkout",
                "error_message": None,
            }
        )

        session = fresh_store.get_session()
        assert session.status == SessionStatus.completed
        actions = fresh_store.get_actions()
        assert actions[-1].action_type == ActionType.completed
        assert actions[-1].status == ActionStatus.success

    def test_completion_error(self, fresh_store):
        """有错误时应设置 error 状态。"""
        from app.agent.engine import completion_node

        fresh_store.create_session()
        completion_node(
            {
                "session_id": "test-1",
                "trigger_message": "测试",
                "matched_intent": None,
                "matched_skill": None,
                "error_message": "Some error",
            }
        )

        session = fresh_store.get_session()
        assert session.status == SessionStatus.error
        actions = fresh_store.get_actions()
        assert actions[-1].status == ActionStatus.error

    def test_completion_saves_history(self, fresh_store):
        """完成节点应保存执行历史。"""
        from app.agent.engine import completion_node

        fresh_store.create_session()
        completion_node(
            {
                "session_id": "test-1",
                "trigger_message": "订单号 HT20260301001 提前离店",
                "matched_intent": "early_checkout",
                "matched_skill": "early_checkout",
                "error_message": None,
            }
        )

        history = fresh_store.get_history_list()
        assert len(history) == 1
        assert history[0].trigger_message == "订单号 HT20260301001 提前离店"
        assert history[0].skill_name == "提前离店"

    def test_completion_saves_history_with_no_skill(self, fresh_store):
        """未匹配 Skill 时历史记录的 skill_name 应为 None。"""
        from app.agent.engine import completion_node

        fresh_store.create_session()
        completion_node(
            {
                "session_id": "test-1",
                "trigger_message": "无意义消息",
                "matched_intent": "unknown",
                "matched_skill": None,
                "error_message": None,
            }
        )

        history = fresh_store.get_history_list()
        assert history[0].skill_name is None


# === Task 7: 路由函数测试 ===


class TestRouting:
    """测试条件路由逻辑。"""

    def test_route_to_tool_chain_when_skill_matched(self):
        """匹配到 Skill 时应路由到 tool_chain_execution。"""
        from app.agent.engine import _route_after_skill_loading

        result = _route_after_skill_loading(
            {
                "session_id": "test",
                "trigger_message": "test",
                "matched_intent": "early_checkout",
                "matched_skill": "early_checkout",
                "error_message": None,
            }
        )
        assert result == "tool_chain_execution"

    def test_route_to_completion_when_no_skill(self):
        """未匹配 Skill 时应路由到 completion。"""
        from app.agent.engine import _route_after_skill_loading

        result = _route_after_skill_loading(
            {
                "session_id": "test",
                "trigger_message": "test",
                "matched_intent": "unknown",
                "matched_skill": None,
                "error_message": None,
            }
        )
        assert result == "completion"


# === Task 8: run_agent 入口函数测试 ===


class TestRunAgent:
    """测试 Agent 执行入口函数。"""

    @pytest.mark.asyncio
    async def test_run_agent_sets_running_status(self, fresh_store):
        """run_agent 应将会话状态设为 running。"""
        from app.agent.engine import run_agent

        fresh_store.create_session()

        # Mock 整个图执行
        with patch("app.agent.engine._graph") as mock_graph:
            mock_graph.ainvoke = AsyncMock(return_value={})
            await run_agent("test-session", "测试消息")

        # 验证会话状态变化（最终由 graph 中的 completion 节点设置）
        # 这里 graph 被 mock 了，所以状态应保持 running
        session = fresh_store.get_session()
        assert session.status == SessionStatus.running

    @pytest.mark.asyncio
    async def test_run_agent_records_user_message(self, fresh_store):
        """run_agent 应在 chat 频道记录用户消息。"""
        from app.agent.engine import run_agent

        fresh_store.create_session()

        with patch("app.agent.engine._graph") as mock_graph:
            mock_graph.ainvoke = AsyncMock(return_value={})
            await run_agent("test-session", "订单号 HT20260301001 提前离店")

        messages = fresh_store.get_messages(Channel.chat)
        assert len(messages) == 1
        assert messages[0].sender == "user"
        assert "HT20260301001" in messages[0].content

    @pytest.mark.asyncio
    async def test_run_agent_handles_exception(self, fresh_store):
        """run_agent 应捕获未处理异常并设置 error 状态。"""
        from app.agent.engine import run_agent

        fresh_store.create_session()

        with patch("app.agent.engine._graph") as mock_graph:
            mock_graph.ainvoke = AsyncMock(side_effect=Exception("Unexpected"))
            await run_agent("test-session", "测试")

        session = fresh_store.get_session()
        assert session.status == SessionStatus.error
        assert "系统错误" in session.final_reply


# === Task 9: 端到端集成测试 ===


class TestEndToEndIntegration:
    """端到端集成测试 — mock LLM 跑完提前离店完整流程。"""

    @pytest.mark.asyncio
    async def test_early_checkout_full_flow(self, fresh_store):
        """完整提前离店流程：意图识别 → Skill 加载 → 工具调用链 → 完成。"""
        from app.agent.engine import run_agent

        fresh_store.create_session()

        # 构建 mock LLM 响应序列
        # 第 1 次调用：意图识别
        intent_response = MagicMock()
        intent_response.content = "early_checkout"

        # 第 2 次调用：LLM 决定调用 order_query
        tool_call_1 = MagicMock()
        tool_call_1.content = ""
        tool_call_1.tool_calls = [
            {
                "name": "order_query",
                "args": {"order_id": "HT20260301001"},
                "id": "call_1",
            }
        ]

        # 第 3 次调用：LLM 决定调用 message_send → upstream
        tool_call_2 = MagicMock()
        tool_call_2.content = ""
        tool_call_2.tool_calls = [
            {
                "name": "message_send",
                "args": {
                    "channel": "upstream",
                    "content": "供应商订单 SUP-88901，客人申请提前离店",
                },
                "id": "call_2",
            }
        ]

        # 第 4 次调用：LLM 决定调用 refund
        tool_call_3 = MagicMock()
        tool_call_3.content = ""
        tool_call_3.tool_calls = [
            {
                "name": "refund",
                "args": {"order_id": "HT20260301001"},
                "id": "call_3",
            }
        ]

        # 第 5 次调用：LLM 决定调用 message_send → downstream
        tool_call_4 = MagicMock()
        tool_call_4.content = ""
        tool_call_4.tool_calls = [
            {
                "name": "message_send",
                "args": {
                    "channel": "downstream",
                    "content": "客人订单 HT20260301001 的提前离店请求已处理完成，退款已登记。",
                },
                "id": "call_4",
            }
        ]

        # 第 6 次调用：LLM 返回最终回复（无 tool_calls）
        final_response = MagicMock()
        final_response.content = "您的提前离店请求已处理完成，退款已登记。"
        final_response.tool_calls = []

        # 设置 mock LLM 调用序列
        call_count = 0

        def mock_invoke(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return intent_response
            elif call_count == 2:
                return tool_call_1
            elif call_count == 3:
                return tool_call_2
            elif call_count == 4:
                return tool_call_3
            elif call_count == 5:
                return tool_call_4
            else:
                return final_response

        mock_llm = MagicMock()
        mock_llm.invoke = mock_invoke
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)

        with patch("app.agent.engine._llm", mock_llm):
            await run_agent("test-session", "订单号 HT20260301001 的客人申请提前离店")

        # 验证会话状态
        session = fresh_store.get_session()
        assert session.status == SessionStatus.completed
        assert session.final_reply is not None

        # 验证 ActionLogEntry 序列
        actions = fresh_store.get_actions()
        action_types = [a.action_type for a in actions]

        # 应包含：intent_recognition, skill_loaded, tool_call(s), waiting, completed
        assert ActionType.intent_recognition in action_types
        assert ActionType.skill_loaded in action_types
        assert ActionType.tool_call in action_types
        assert ActionType.waiting in action_types
        assert ActionType.completed in action_types

        # 验证所有动作最终为 success 或 error
        for action in actions:
            assert action.status in (ActionStatus.success, ActionStatus.error)

        # 验证消息频道
        chat_msgs = fresh_store.get_messages(Channel.chat)
        assert len(chat_msgs) >= 1  # 至少有用户消息
        assert chat_msgs[0].sender == "user"

        upstream_msgs = fresh_store.get_messages(Channel.upstream)
        assert len(upstream_msgs) >= 1  # Agent 发给上游的消息

        downstream_msgs = fresh_store.get_messages(Channel.downstream)
        assert len(downstream_msgs) >= 1  # Agent 发给下游的消息

        # 验证历史记录已保存
        history = fresh_store.get_history_list()
        assert len(history) == 1
        assert history[0].skill_name == "提前离店"

    @pytest.mark.asyncio
    async def test_unmatched_intent_flow(self, fresh_store):
        """未匹配意图时应直接完成并返回友好提示。"""
        from app.agent.engine import run_agent

        fresh_store.create_session()

        mock_response = MagicMock()
        mock_response.content = "unknown"

        mock_llm = MagicMock()
        mock_llm.invoke = MagicMock(return_value=mock_response)

        with patch("app.agent.engine._llm", mock_llm):
            await run_agent("test-session", "今天天气怎么样")

        session = fresh_store.get_session()
        # 由 completion_node 设置最终状态
        assert session.status in (SessionStatus.completed, SessionStatus.error)
        assert session.final_reply is not None
        assert "无法处理" in session.final_reply

        # 验证 ActionLogEntry 序列 — 意图识别 + Skill 加载失败 + 完成
        actions = fresh_store.get_actions()
        action_types = [a.action_type for a in actions]
        assert ActionType.intent_recognition in action_types
        assert ActionType.skill_loaded in action_types
        assert ActionType.completed in action_types
        # 不应有 tool_call
        assert ActionType.tool_call not in action_types

    @pytest.mark.asyncio
    async def test_tool_error_graceful_termination(self, fresh_store):
        """工具调用返回错误时应优雅终止流程（FR33）。"""
        from app.agent.engine import run_agent

        fresh_store.create_session()

        # 意图识别返回 early_checkout
        intent_response = MagicMock()
        intent_response.content = "early_checkout"

        # LLM 调用 order_query 但使用无效订单号
        tool_call_1 = MagicMock()
        tool_call_1.content = ""
        tool_call_1.tool_calls = [
            {
                "name": "order_query",
                "args": {"order_id": "INVALID_ORDER"},
                "id": "call_1",
            }
        ]

        call_count = 0

        def mock_invoke(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return intent_response
            else:
                return tool_call_1

        mock_llm = MagicMock()
        mock_llm.invoke = mock_invoke
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)

        with patch("app.agent.engine._llm", mock_llm):
            await run_agent("test-session", "订单号 INVALID_ORDER 提前离店")

        session = fresh_store.get_session()
        assert session.status == SessionStatus.error

        # 验证有工具调用的 error 记录
        actions = fresh_store.get_actions()
        tool_actions = [a for a in actions if a.action_type == ActionType.tool_call]
        assert any(a.status == ActionStatus.error for a in tool_actions)


# === Code Review 修复验证测试 ===


class TestCodeReviewFixes:
    """验证 Code Review 发现的问题已修复。"""

    def test_h1_langchain_tools_have_args_schema(self):
        """[H1] _build_langchain_tools 应为每个工具生成正确的 args_schema。"""
        from app.agent.engine import _build_langchain_tools

        lc_tools = _build_langchain_tools()
        assert len(lc_tools) >= 3  # order_query, message_send, refund

        # 验证 order_query 工具有 order_id 参数 schema
        oq_tool = next((t for t in lc_tools if t.name == "order_query"), None)
        assert oq_tool is not None
        assert oq_tool.args_schema is not None
        schema = oq_tool.args_schema.model_json_schema()
        assert "order_id" in schema.get("properties", {})

    def test_h2_max_iterations_constant_exists(self):
        """[H2] MAX_TOOL_ITERATIONS 常量应存在且为正整数。"""
        from app.agent.engine import MAX_TOOL_ITERATIONS

        assert isinstance(MAX_TOOL_ITERATIONS, int)
        assert MAX_TOOL_ITERATIONS > 0

    @pytest.mark.asyncio
    async def test_h2_tool_chain_respects_max_iterations(self, fresh_store):
        """[H2] 工具调用链应在超过最大迭代次数时优雅终止。"""
        from app.agent.engine import MAX_TOOL_ITERATIONS, run_agent

        fresh_store.create_session()

        # 意图识别返回 early_checkout
        intent_response = MagicMock()
        intent_response.content = "early_checkout"

        # LLM 持续返回工具调用（永不停止）
        infinite_tool_call = MagicMock()
        infinite_tool_call.content = ""
        infinite_tool_call.tool_calls = [
            {
                "name": "order_query",
                "args": {"order_id": "HT20260301001"},
                "id": "call_loop",
            }
        ]

        call_count = 0

        def mock_invoke(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return intent_response
            return infinite_tool_call

        mock_llm = MagicMock()
        mock_llm.invoke = mock_invoke
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)

        with patch("app.agent.engine._llm", mock_llm):
            await run_agent("test-session", "提前离店 HT20260301001")

        session = fresh_store.get_session()
        assert session.status == SessionStatus.error
        assert "超过最大迭代次数" in session.final_reply

    @pytest.mark.asyncio
    async def test_h3_upstream_reply_injected_into_messages(self, fresh_store):
        """[H3] 上游回复应注入 LLM 消息历史。"""
        from app.agent.engine import tool_chain_execution_node

        fresh_store.create_session()

        # 模拟 order_query → message_send(upstream) → refund → message_send(downstream) → 完成
        tool_call_order_query = MagicMock()
        tool_call_order_query.content = ""
        tool_call_order_query.tool_calls = [
            {"name": "order_query", "args": {"order_id": "HT20260301001"}, "id": "c1"}
        ]

        tool_call_msg_upstream = MagicMock()
        tool_call_msg_upstream.content = ""
        tool_call_msg_upstream.tool_calls = [
            {"name": "message_send", "args": {"channel": "upstream", "content": "请处理"}, "id": "c2"}
        ]

        tool_call_refund = MagicMock()
        tool_call_refund.content = ""
        tool_call_refund.tool_calls = [
            {"name": "refund", "args": {"order_id": "HT20260301001"}, "id": "c3"}
        ]

        tool_call_msg_downstream = MagicMock()
        tool_call_msg_downstream.content = ""
        tool_call_msg_downstream.tool_calls = [
            {"name": "message_send", "args": {"channel": "downstream", "content": "已处理"}, "id": "c4"}
        ]

        final_resp = MagicMock()
        final_resp.content = "处理完成"
        final_resp.tool_calls = []

        call_count = 0
        captured_messages = []

        def mock_invoke(messages):
            nonlocal call_count
            call_count += 1
            # 捕获传给 LLM 的 messages 以验证上游回复是否被注入
            captured_messages.append(list(messages))
            if call_count == 1:
                return tool_call_order_query
            elif call_count == 2:
                return tool_call_msg_upstream
            elif call_count == 3:
                return tool_call_refund
            elif call_count == 4:
                return tool_call_msg_downstream
            else:
                return final_resp

        mock_llm = MagicMock()
        mock_llm.invoke = mock_invoke
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)

        with patch("app.agent.engine._llm", mock_llm):
            tool_chain_execution_node(
                {
                    "session_id": "test-1",
                    "trigger_message": "提前离店 HT20260301001",
                    "matched_intent": "early_checkout",
                    "matched_skill": "early_checkout",
                    "error_message": None,
                }
            )

        # 第 3 次 LLM 调用（refund 决策）的 messages 应包含上游回复
        assert call_count >= 3
        refund_call_messages = captured_messages[2]  # 第 3 次调用
        message_contents = [str(m.content) for m in refund_call_messages if hasattr(m, "content")]
        assert any("上游供应商回复" in c for c in message_contents), \
            "上游回复未注入到 LLM 消息历史中"

    def test_m2_unmatched_intent_reply_in_chat(self, fresh_store):
        """[M2] 未匹配意图时 Agent 回复应同时写入 chat 频道和 final_reply。"""
        from app.agent.engine import skill_loading_node

        fresh_store.create_session()
        skill_loading_node(
            {
                "session_id": "test-1",
                "trigger_message": "今天天气怎么样",
                "matched_intent": "unknown",
                "matched_skill": None,
                "error_message": None,
            }
        )

        # final_reply 和 chat 消息应一致
        session = fresh_store.get_session()
        chat_msgs = fresh_store.get_messages(Channel.chat)
        assert len(chat_msgs) == 1
        assert chat_msgs[0].content == session.final_reply
