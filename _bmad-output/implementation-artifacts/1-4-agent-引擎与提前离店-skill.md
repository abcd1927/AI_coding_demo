# Story 1.4: Agent 引擎与提前离店 Skill

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a 开发者,
I want 搭建基于 LangGraph 的 Agent 引擎，实现意图识别、Skill 路由和提前离店 Skill 的完整工具调用链,
so that Agent 可以接收消息、识别意图、加载 Skill 并逐步执行完整的提前离店流程。

## Acceptance Criteria

1. **Given** agent/engine.py **When** 定义 LangGraph 状态图 **Then** 包含意图识别、Skill 加载、工具调用链执行、流程完成等节点

2. **Given** Agent 引擎收到消息 "订单号 HT20260301001 的客人申请提前离店" **When** 执行意图识别 **Then** 通过 Gemini LLM 识别为"提前离店"意图，并记录 ActionLogEntry（action_type=intent_recognition）（FR4）

3. **Given** 意图识别为"提前离店" **When** Skill 路由 **Then** 自动加载 early_checkout Skill，记录 ActionLogEntry（action_type=skill_loaded）（FR5）

4. **Given** Skill 已加载 **When** 执行工具调用链 **Then** 按顺序执行：提取订单号(FR7) → 查询订单(FR8) → 发送上游消息(FR9) → 等待上游回复(FR10) → 退款登记(FR11) → 发送下游回复(FR12)，每步记录 ActionLogEntry

5. **Given** 每次工具调用 **When** 执行完成 **Then** 记录 ActionLogEntry 包含 action_type、title、summary、输入输出详情、状态和时间戳（FR16, FR17）

6. **Given** agent/skills/early_checkout.md **When** 查看内容 **Then** 包含提前离店场景的自然语言流程描述（NFR4）

7. **Given** agent/skills/__init__.py **When** 系统启动 **Then** 自动扫描 skills/ 目录加载所有 .md Skill 文件并注册到 Skill 列表（FR35）

8. **Given** Agent 工具调用返回错误 **When** 处理错误 **Then** 记录错误 ActionLogEntry（status=error）并优雅终止当前流程（FR33）

9. **Given** 完整流程执行 **When** 从接收消息到最终回复 **Then** 在 30 秒内完成（NFR1）

## Tasks / Subtasks

- [x] Task 1: 创建 Skill 注册表和提前离店 Skill 文件 (AC: #6, #7)
  - [x] 1.1 在 `backend/app/agent/skills/early_checkout.md` 中编写提前离店场景的自然语言流程描述
  - [x] 1.2 在 `backend/app/agent/skills/__init__.py` 中实现 Skill 注册表：扫描 `skills/` 目录的 `.md` 文件，解析为 `SkillDefinition`
  - [x] 1.3 提供 `get_skill(skill_id: str) -> SkillDefinition | None` 按 ID 查找
  - [x] 1.4 提供 `get_all_skills() -> list[SkillDefinition]` 获取全部 Skill

- [x] Task 2: 定义 Agent 图状态和 LLM 客户端 (AC: #1)
  - [x] 2.1 在 `backend/app/agent/engine.py` 中定义轻量级 `AgentGraphState(TypedDict)` 用于图内部路由
  - [x] 2.2 初始化 `ChatGoogleGenerativeAI` 客户端（model="gemini-2.0-flash", temperature=0）
  - [x] 2.3 LLM 客户端使用 `os.environ.get("GOOGLE_API_KEY")` 读取 API Key

- [x] Task 3: 实现意图识别节点 (AC: #2)
  - [x] 3.1 创建 `intent_recognition_node(state: AgentGraphState) -> dict` 函数
  - [x] 3.2 调用 `store.add_action(action_type=ActionType.intent_recognition, status=ActionStatus.running)` 记录开始
  - [x] 3.3 构建 SystemMessage，列出所有已注册 Skill 名称供 LLM 选择
  - [x] 3.4 调用 Gemini LLM 识别意图，返回 skill_id 字符串
  - [x] 3.5 调用 `store.update_action_status()` 更新为 success 或 error
  - [x] 3.6 返回 `{"matched_intent": intent}` 更新图状态

- [x] Task 4: 实现 Skill 加载节点 (AC: #3)
  - [x] 4.1 创建 `skill_loading_node(state: AgentGraphState) -> dict` 函数
  - [x] 4.2 根据 `state["matched_intent"]` 查找 Skill 注册表
  - [x] 4.3 匹配成功：记录 ActionLogEntry(action_type=skill_loaded, status=success)
  - [x] 4.4 匹配失败：记录 ActionLogEntry(status=error)，设置未匹配回复消息
  - [x] 4.5 返回 `{"matched_skill": skill_id}` 或 `{"matched_skill": None}`

- [x] Task 5: 实现工具调用链执行节点 (AC: #4, #5, #8)
  - [x] 5.1 创建 `tool_chain_execution_node(state: AgentGraphState) -> dict` 函数
  - [x] 5.2 将已注册的 `BaseTool` 实例包装为 LangChain `StructuredTool`（仅供 LLM schema 绑定）
  - [x] 5.3 使用 `llm.bind_tools(tools)` 让 Gemini 驱动工具选择
  - [x] 5.4 将 Skill .md 内容作为 SystemMessage、触发消息作为 HumanMessage 传入 LLM
  - [x] 5.5 循环处理 LLM 响应：有 tool_calls 时执行工具，无 tool_calls 时提取最终回复
  - [x] 5.6 每次工具调用记录 ActionLogEntry(action_type=tool_call)，含 running → success/error 状态更新
  - [x] 5.7 每次工具调用在 detail 中记录 input（工具参数）和 output（工具返回值）
  - [x] 5.8 工具调用返回错误时记录 error 状态并优雅终止（FR33）
  - [x] 5.9 在 "发送上游消息" 步骤后，调用 `simulate_upstream_reply()` 模拟上游回复（FR10, FR22）
  - [x] 5.10 记录 waiting ActionLogEntry 表示等待上游回复，收到后更新为 success

- [x] Task 6: 实现流程完成节点 (AC: #1)
  - [x] 6.1 创建 `completion_node(state: AgentGraphState) -> dict` 函数
  - [x] 6.2 检查是否有错误：有则设置 `SessionStatus.error`
  - [x] 6.3 无错误：设置 `SessionStatus.completed`，记录 completed ActionLogEntry
  - [x] 6.4 调用 `store.save_execution_history()` 保存执行历史快照

- [x] Task 7: 构建和编译 LangGraph 状态图 (AC: #1)
  - [x] 7.1 使用 `StateGraph(AgentGraphState)` 创建图构建器
  - [x] 7.2 注册 4 个节点：intent_recognition、skill_loading、tool_chain_execution、completion
  - [x] 7.3 添加边：START → intent_recognition → skill_loading
  - [x] 7.4 添加条件边：skill_loading → (matched_skill ? tool_chain_execution : completion)
  - [x] 7.5 添加边：tool_chain_execution → completion → END
  - [x] 7.6 编译为模块级单例 `_graph = builder.compile()`

- [x] Task 8: 实现 Agent 公开入口函数 (AC: #9)
  - [x] 8.1 创建 `async def run_agent(session_id: str, trigger_message: str) -> None`
  - [x] 8.2 设置 session 状态为 running
  - [x] 8.3 构建初始 AgentGraphState 并调用 `await _graph.ainvoke(initial_state)`
  - [x] 8.4 外层 try/except 捕获未处理异常，设置 SessionStatus.error 和错误回复
  - [x] 8.5 在 chat 频道添加用户消息（store.add_message）

- [x] Task 9: 编写单元测试 (AC: #1-#9)
  - [x] 9.1 测试 Skill 注册表：自动发现 .md 文件、按 ID 查找、获取全部 Skill
  - [x] 9.2 测试 early_checkout.md 内容完整性（包含名称、描述、流程步骤）
  - [x] 9.3 测试 AgentGraphState 类型定义
  - [x] 9.4 测试图编译成功（_graph 不为 None）
  - [x] 9.5 测试意图识别节点（mock LLM 返回，验证 store.add_action 调用）
  - [x] 9.6 测试 Skill 加载节点（匹配/未匹配两种路径）
  - [x] 9.7 测试完成节点（success/error 两种路径）
  - [x] 9.8 测试 run_agent 入口函数错误处理
  - [x] 9.9 集成测试：mock LLM 后端到端跑完提前离店流程，验证 ActionLogEntry 序列

## Dev Notes

### 核心架构：LangGraph 状态图 + MemoryStore 侧效应模式

本 Story 的核心设计决策是**轻量图状态 + MemoryStore 侧效应**模式：

- **AgentGraphState（TypedDict）**：仅携带路由决策所需的最小信息（session_id、trigger_message、matched_intent、matched_skill、error_message）
- **MemoryStore（store 单例）**：作为唯一的状态权威来源。图节点通过 `store.add_action()`、`store.update_action_status()` 等方法记录每步执行详情
- **理由**：LangGraph 默认覆盖（overwrite）状态字段，若将 `actions: list` 放入图状态会导致列表管理复杂度。MemoryStore 已实现完整的增量查询 API（`get_actions(after_index=N)`），前端轮询直接从 store 读取

```python
# ✅ 正确模式 — 图状态轻量，store 管理详情
class AgentGraphState(TypedDict):
    session_id: str
    trigger_message: str
    matched_intent: str | None
    matched_skill: str | None
    error_message: str | None

# 节点中通过 store 记录动作
def intent_recognition_node(state: AgentGraphState) -> dict:
    action = store.add_action(...)  # 侧效应写入 store
    # ... LLM 调用 ...
    store.update_action_status(action.index, ...)
    return {"matched_intent": "early_checkout"}  # 只返回路由信号
```

```python
# ❌ 错误模式 — 不要把 actions 列表放入图状态
class AgentGraphState(TypedDict):
    actions: list[ActionLogEntry]  # 不要这样做！LangGraph 默认覆盖列表
```

### LLM 集成：ChatGoogleGenerativeAI

```python
from langchain_google_genai import ChatGoogleGenerativeAI

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.environ.get("GOOGLE_API_KEY", ""),
    temperature=0,  # 确定性路由
)
```

- **model**: 使用 `gemini-2.0-flash`（快速、低延迟，满足 NFR1 ≤30 秒）
- **temperature=0**: 意图识别需要确定性结果
- **API Key**: 从环境变量 `GOOGLE_API_KEY` 读取，.env 文件已在 Story 1.1 创建

### 意图识别节点设计

意图识别使用结构化 prompt 让 LLM 从已注册 Skill 列表中选择匹配项：

```python
from langchain_core.messages import SystemMessage, HumanMessage

def intent_recognition_node(state: AgentGraphState) -> dict:
    skills = get_all_skills()
    skill_list = "\n".join([f"- {s.skill_id}: {s.name} — {s.description}" for s in skills])

    system_prompt = f"""你是一个意图分类器。根据用户消息，识别业务意图。

可用意图（skill_id: 名称 — 描述）：
{skill_list}

规则：
1. 如果消息匹配某个意图，只返回对应的 skill_id（如 early_checkout）
2. 如果无法匹配任何意图，返回 unknown
3. 只返回 skill_id，不要其他内容"""

    response = _llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["trigger_message"]),
    ])
    intent = response.content.strip()
    return {"matched_intent": intent}
```

### 工具调用链：LLM 驱动 + BaseTool 包装

将已注册的 `BaseTool` 实例包装为 LangChain `@tool` 函数，让 Gemini 通过 `bind_tools` 自主驱动工具选择：

```python
from langchain_core.tools import tool as langchain_tool

def _build_langchain_tools():
    """将 BaseTool 实例包装为 LangChain @tool 函数"""
    from app.agent.tools import get_all_tools

    lc_tools = []
    for base_tool in get_all_tools():
        # 用闭包捕获 base_tool 实例
        def make_tool_fn(bt):
            @langchain_tool
            def tool_fn(**kwargs) -> dict:
                """动态工具函数"""
                return bt.execute(**kwargs)
            tool_fn.name = bt.name
            tool_fn.__doc__ = bt.description
            return tool_fn
        lc_tools.append(make_tool_fn(base_tool))
    return lc_tools
```

**关键：** Skill .md 文件的完整内容作为 SystemMessage 传入 LLM，给予 LLM 逐步执行指引。LLM 根据 Skill 流程描述自主决定调用哪些工具、以什么顺序。

### 上游回复模拟的集成

在工具调用链中，当 LLM 调用 `message_send` 工具向 upstream 频道发送消息后，需要：

1. 记录 waiting ActionLogEntry（action_type=waiting, status=running）
2. 调用 `simulate_upstream_reply(supplier_order_id)` 模拟上游自动回复
3. 更新 waiting ActionLogEntry 状态为 success
4. 将上游回复内容作为 ToolMessage 返回给 LLM，让 LLM 继续后续步骤

```python
from app.mock.upstream import simulate_upstream_reply

# 在工具调用循环中检测 message_send 到 upstream 的情况
if tool_name == "message_send" and tool_args.get("channel") == "upstream":
    # 记录等待状态
    wait_action = store.add_action(
        action_type=ActionType.waiting,
        title="等待上游回复",
        summary="等待供应商处理…",
        status=ActionStatus.running,
    )
    # 模拟上游回复
    reply = simulate_upstream_reply(supplier_order_id)
    store.update_action_status(wait_action.index, ActionStatus.success,
                               {"reply": reply})
```

### Skill 注册表设计

镜像工具注册表的模式，在 `__init__.py` 中自动扫描 `.md` 文件：

```python
# agent/skills/__init__.py
from pathlib import Path
from app.schemas.models import SkillDefinition

_skill_registry: dict[str, SkillDefinition] = {}

def _load_skills() -> None:
    skills_dir = Path(__file__).parent
    for md_file in skills_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        skill_id = md_file.stem  # 文件名去掉 .md 后缀
        lines = content.strip().splitlines()
        name = lines[0].lstrip("#").strip() if lines else skill_id
        # 第一个非空非标题行作为描述
        description = ""
        for line in lines[1:]:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                description = stripped
                break
        _skill_registry[skill_id] = SkillDefinition(
            skill_id=skill_id,
            name=name,
            description=description,
            content=content,
        )

_load_skills()

def get_skill(skill_id: str) -> SkillDefinition | None:
    return _skill_registry.get(skill_id)

def get_all_skills() -> list[SkillDefinition]:
    return list(_skill_registry.values())
```

### early_checkout.md Skill 文件内容

```markdown
# 提前离店

处理酒店客人申请提前离店的客服请求。

## 处理流程

你需要按以下步骤处理提前离店请求：

1. 从用户消息中提取订单号和客户诉求信息
2. 调用 order_query 工具，传入订单号，查询对应的供应商订单号
3. 调用 message_send 工具，向 upstream 频道发送消息，内容包含供应商订单号和客户的提前离店诉求
4. 等待上游供应商回复处理结果
5. 根据上游回复，调用 refund 工具执行退款登记
6. 调用 message_send 工具，向 downstream 频道回复最终处理结果，告知客人退款已登记

## 注意事项

- 每一步都要使用对应的工具完成操作
- 如果订单查询失败，直接告知用户订单不存在并终止流程
- 最终回复需包含处理结果摘要
```

### 条件路由：Skill 匹配 vs 未匹配

```python
from typing import Literal

def _route_after_skill_loading(
    state: AgentGraphState,
) -> Literal["tool_chain_execution", "completion"]:
    if state.get("matched_skill"):
        return "tool_chain_execution"
    return "completion"  # 未匹配 → 直接完成（回复友好提示）

builder.add_conditional_edges(
    "skill_loading",
    _route_after_skill_loading,
    {
        "tool_chain_execution": "tool_chain_execution",
        "completion": "completion",
    },
)
```

### 异步执行模式

Agent 引擎通过 `async def run_agent()` 入口函数异步执行。Story 1.5 的 `/api/chat` 路由将使用 FastAPI `BackgroundTasks` 调用此函数：

```python
async def run_agent(session_id: str, trigger_message: str) -> None:
    """Agent 执行入口。由 /api/chat 路由作为后台任务调用。"""
    store.update_session_status(SessionStatus.running)
    # 在 chat 频道记录用户消息
    store.add_message(channel=Channel.chat, sender="user", content=trigger_message)

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
```

### 错误处理策略（FR33）

三层错误防护：

1. **节点级**：每个节点内部 try/except 捕获 LLM 或工具调用异常，记录 error ActionLogEntry，设置 `error_message` 到图状态
2. **路由级**：completion 节点检查 `state["error_message"]`，有错误时设置 `SessionStatus.error`
3. **入口级**：`run_agent()` 外层 try/except 捕获图执行中任何未处理异常

### 前一个 Story (1.3) 关键成果

- **BaseTool 抽象基类**：ABC + @abstractmethod，4 个抽象成员（name、description、execute、_get_parameters）
- **3 个工具**：OrderQueryTool（order_query）、MessageSendTool（message_send）、RefundTool（refund）
- **工具注册表**：`get_tool(name)`、`get_all_tools()`、`get_tool_definitions()` — 使用 pkgutil 自动发现 + __subclasses__() 注册
- **工具返回格式**：成功 `{"success": True, "data": {...}}`，失败 `{"error": True, "error_type": "...", "message": "..."}`
- **模拟数据**：3 条订单（HT20260301001→SUP-88901, HT20260301002→SUP-88902, HT20260301003→SUP-88903）
- **上游模拟**：`simulate_upstream_reply(supplier_order_id)` → 添加 upstream 频道消息 + 标记未读
- **MemoryStore**：`from app.store.memory import store` 导入单例
- **Code Review 修复**：RefundTool 增加订单验证、MessageSendTool 空内容校验、注册表改用后扫描模式
- **93 个单元测试全部通过**

### Git 智能

最近 5 个 commits：
```
4a4106c Complete Story 1.3: 模拟工具与模拟数据
2104e42 Complete Story 1.2: 数据模型与内存存储
dca5dfc Complete Story 1.1: 项目初始化与开发环境搭建
994b11f Add BMAD framework, planning artifacts and Claude Code config
8ac2dc2 Initial commit
```

代码模式观察：
- Python 文件使用 snake_case 命名
- 类使用 PascalCase
- 所有注释和文档字符串使用中文
- 测试文件集中在 `backend/tests/` 目录
- 每个 Story 完成后单独 commit
- store 单例通过模块级实例直接导入使用

### LangGraph 1.0.7 技术要点

| 项目 | 说明 |
|------|------|
| 版本 | langgraph==1.0.7（已安装） |
| 状态类型 | 支持 TypedDict 或 Pydantic BaseModel（推荐 TypedDict 用于轻量路由） |
| 节点定义 | 普通 Python 函数（sync/async），接收状态，返回 dict 部分更新 |
| 边定义 | `add_edge(A, B)` 无条件边，`add_conditional_edges(A, fn, mapping)` 条件边 |
| 编译 | `builder.compile()` → 可调用的 graph 对象 |
| 异步调用 | `await graph.ainvoke(state)` |
| 特殊节点 | `START` 和 `END` 从 `langgraph.graph` 导入 |
| 条件路由函数 | 返回 `Literal["nodeA", "nodeB"]` 类型 |
| checkpointer | 本项目不需要（单会话 Demo，store 管理状态） |

### langchain-google-genai 4.0.0 技术要点

| 项目 | 说明 |
|------|------|
| 版本 | langchain-google-genai==4.0.0（已安装） |
| 类 | `ChatGoogleGenerativeAI` |
| 模型 | `gemini-2.0-flash`（快速）或 `gemini-1.5-pro`（更强） |
| 调用 | `llm.invoke([SystemMessage, HumanMessage])` → AIMessage |
| 工具绑定 | `llm.bind_tools(tools)` → 支持 function calling |
| 工具调用 | `response.tool_calls` → list of `{"name": ..., "args": ..., "id": ...}` |
| 消息类型 | SystemMessage、HumanMessage、AIMessage、ToolMessage |
| ToolMessage | `ToolMessage(content=str, tool_call_id=id)` 返回工具结果 |

### Project Structure Notes

本 Story 涉及的文件：

```
backend/app/
├── agent/
│   ├── __init__.py             # 已存在（空文件，保持空）
│   ├── engine.py               # 新增：LangGraph 状态图 + Agent 调度核心
│   ├── skills/
│   │   ├── __init__.py         # 修改：Skill 注册表（扫描 .md 文件）
│   │   └── early_checkout.md   # 新增：提前离店 Skill（自然语言流程描述）
│   └── tools/
│       ├── __init__.py         # 只读引用（get_tool、get_all_tools）
│       ├── base.py             # 只读引用（BaseTool 接口）
│       ├── order_query.py      # 只读引用
│       ├── message_send.py     # 只读引用
│       └── refund.py           # 只读引用
├── mock/
│   └── upstream.py             # 只读引用（simulate_upstream_reply）
├── schemas/
│   └── models.py               # 只读引用（所有枚举和模型）
└── store/
    └── memory.py               # 只读引用（store 单例）

backend/tests/
└── test_agent.py               # 新增：Agent 引擎测试
```

### 架构边界提醒

**只做：**
- 创建 LangGraph 状态图和 Agent 引擎（engine.py）
- 创建 Skill 注册表（skills/__init__.py）
- 创建提前离店 Skill 文件（early_checkout.md）
- 实现 `run_agent()` 异步入口函数
- 编写 Agent 引擎相关测试

**禁止：**
- 创建任何 API 路由（Story 1.5 负责）
- 修改 main.py（Story 1.5 负责）
- 创建订单取消 Skill order_cancel.md（Story 2.1 负责）
- 创建前端文件
- 修改已有的 tools/ 文件或 store/memory.py
- 修改 mock/data.py 或 mock/upstream.py

### 命名规范

| 场景 | 规则 | 示例 |
|------|------|------|
| 模块文件名 | snake_case | `engine.py`, `early_checkout.md` |
| 类名 | PascalCase | `AgentGraphState`（TypedDict） |
| 函数名 | snake_case | `run_agent`, `intent_recognition_node` |
| Skill ID | snake_case | `early_checkout` |
| 图节点名 | snake_case | `"intent_recognition"`, `"skill_loading"` |
| 常量 | UPPER_SNAKE_CASE | `_graph`（模块级单例用小写加前缀下划线） |

### 测试策略

- 使用 `unittest.mock.patch` mock LLM 调用（不依赖真实 API Key）
- 使用 `monkeypatch` 替换 store 单例确保测试隔离
- 测试 Skill 注册表独立于 LLM
- 测试图编译独立于 LLM
- 集成测试 mock 整个 LLM 返回序列，验证 ActionLogEntry 序列
- 保持与前 Story 测试风格一致（pytest + fixture + monkeypatch）

### MemoryStore API 速查表（供 engine.py 使用）

```python
from app.store.memory import store

# 会话管理
store.create_session() -> AgentExecutionState
store.update_session_status(SessionStatus.running)
store.set_final_reply("处理完成...")

# 动作记录
action = store.add_action(
    action_type=ActionType.tool_call,
    title="调用工具：查询订单",
    summary="查询订单号 HT20260301001",
    status=ActionStatus.running,
    detail={"input": {...}},
)
store.update_action_status(action.index, ActionStatus.success, {"output": {...}})

# 消息管理
store.add_message(channel=Channel.chat, sender="user", content="...")
store.mark_channel_unread("upstream")

# 历史记录
store.save_execution_history(trigger_message="...", skill_name="提前离店")
```

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Core Architectural Decisions] — Agent 引擎为唯一调用 Skills 和 Tools 的入口
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns] — 后端目录结构，agent/engine.py 和 agent/skills/ 位置
- [Source: _bmad-output/planning-artifacts/architecture.md#Communication Patterns] — action_type 枚举值、status 枚举值、频道标识符
- [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns] — 轮询机制和错误处理标准
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture] — 6 个核心数据模型定义
- [Source: _bmad-output/planning-artifacts/architecture.md#Starter Template Evaluation] — LangGraph 1.0.7、langchain-google-genai 4.0.0
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4] — 验收标准（8 条 AC + NFR1 性能要求）
- [Source: _bmad-output/planning-artifacts/prd.md#意图识别与 Skill 路由] — FR4-FR6
- [Source: _bmad-output/planning-artifacts/prd.md#提前离店场景] — FR7-FR12
- [Source: _bmad-output/planning-artifacts/prd.md#工作流可视化] — FR16-FR19
- [Source: _bmad-output/planning-artifacts/prd.md#系统管理] — FR33 错误处理、FR35 自动加载配置
- [Source: _bmad-output/planning-artifacts/prd.md#Non-Functional Requirements] — NFR1 ≤30秒、NFR4 新增 Skill 无需改核心代码
- [Source: _bmad-output/implementation-artifacts/1-3-模拟工具与模拟数据.md] — BaseTool 接口、工具注册表、模拟数据、上游回复模拟、store API 用法
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#User Journey Flows] — 完整提前离店旅程的用户体验流

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

- 初始集成测试失败 2 个：`_build_langchain_tools` 使用 `@langchain_tool` 装饰器 + 默认参数 `bt_ref=bt` 导致 LangChain 参数解析异常。修复方案：改用 `StructuredTool.from_function()` 仅供 LLM schema 绑定，工具执行直接通过 `get_tool(name).execute(**args)` 调用 BaseTool
- `fresh_store` fixture 尝试 monkeypatch `app.agent.tools.refund.store`，但 refund.py 不导入 store。已移除

### Completion Notes List

- Task 1: 创建 `early_checkout.md`（6 步自然语言流程描述）和 `skills/__init__.py`（_load_skills 扫描 .md → SkillDefinition，get_skill/get_all_skills API）
- Task 2: 定义 `AgentGraphState(TypedDict)` 含 5 个字段（session_id, trigger_message, matched_intent, matched_skill, error_message），初始化 `ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)`
- Task 3: `intent_recognition_node` — 构建意图分类 prompt 含全部 Skill 列表，LLM 返回 skill_id，记录 intent_recognition ActionLogEntry（running→success/error）
- Task 4: `skill_loading_node` — 按 matched_intent 查找 Skill 注册表，匹配成功记录 skill_loaded/success，未匹配记录 error 并设置友好回复（列出已支持场景）
- Task 5: `tool_chain_execution_node` — StructuredTool 仅供 bind_tools schema 绑定，实际执行通过 BaseTool.execute()。循环处理 LLM tool_calls，每次记录 tool_call ActionLogEntry（running→success/error）。检测 upstream 消息发送后触发 simulate_upstream_reply 并记录 waiting ActionLogEntry。工具错误时优雅终止（FR33）
- Task 6: `completion_node` — 检查 error_message 设置 SessionStatus，记录 completed ActionLogEntry，调用 save_execution_history
- Task 7: StateGraph 编译 — 4 节点（intent_recognition, skill_loading, tool_chain_execution, completion），条件边 skill_loading→(matched_skill ? tool_chain : completion)
- Task 8: `async run_agent()` — 设置 running 状态，chat 频道记录用户消息，ainvoke 图，外层 try/except 捕获未处理异常
- Task 9: 28 个测试 — TestSkillRegistry(7)、TestAgentGraphState(3)、TestIntentRecognitionNode(3)、TestSkillLoadingNode(3)、TestCompletionNode(4)、TestRouting(2)、TestRunAgent(3)、TestEndToEndIntegration(3)

### File List

**新增文件:**
- backend/app/agent/engine.py
- backend/app/agent/skills/early_checkout.md
- backend/tests/test_agent.py

**修改文件:**
- backend/app/agent/skills/__init__.py（从空文件改为 Skill 注册表）
- backend/app/agent/engine.py（Code Review 修复：args_schema、迭代防护、上游回复注入、chat 频道一致性）
- backend/Pipfile（新增 pytest-asyncio dev 依赖）
- backend/Pipfile.lock（依赖锁定更新）

## Change Log

- 2026-02-27: 完成 Story 1.4 全部 9 个 Task — LangGraph 状态图（4 节点 + 条件路由）、Skill 注册表（.md 自动扫描）、提前离店 Skill、Agent 引擎（意图识别 → Skill 加载 → 工具调用链 → 完成）、async run_agent 入口函数。编写 28 个测试全部通过，加上已有 93 个测试共 121 个测试零回归。
- 2026-02-27: Code Review 修复 — [H1] _build_langchain_tools 使用 _get_parameters() 动态构建 args_schema；[H2] 添加 MAX_TOOL_ITERATIONS=20 防止工具调用链无限循环；[H3] 上游回复注入 LLM 消息历史供后续决策；[M1] File List 补充 Pipfile/Pipfile.lock；[M2] 未匹配意图回复写入 chat 频道；[M3] 删除根目录误建的空 Pipfile。新增 5 个验证测试，共 126 个测试全部通过。
