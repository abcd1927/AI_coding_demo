# Story 1.5: 后端 REST API 与通信层

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a 操作者,
I want 通过 REST API 发送消息给 Agent 并轮询获取执行状态和频道消息,
so that 前端可以与后端通信，实时展示 Agent 的工作过程。

## Acceptance Criteria

1. **Given** POST /api/chat **When** 发送 {"message": "订单号 HT20260301001 的客人申请提前离店"} **Then** 返回 {"session_id": "xxx"}，Agent 在后台异步启动处理（FR2）

2. **Given** GET /api/status/{session_id} **When** 不带 after_index 参数 **Then** 返回完整的 AgentExecutionState 包含所有 actions（FR30）

3. **Given** GET /api/status/{session_id}?after_index=3 **When** 轮询 **Then** 只返回 index > 3 的增量 new_actions，避免重复传输

4. **Given** GET /api/messages/{channel} **When** channel 分别为 chat、downstream、upstream **Then** 返回对应频道的消息列表（FR3, FR20, FR21）

5. **Given** API 请求出错 **When** 返回错误响应 **Then** 格式统一为 {"error": true, "error_type": "ERROR_CODE", "message": "描述"}

6. **Given** FastAPI 应用 **When** 配置 CORS **Then** 允许 localhost:5173 来源的请求访问所有 /api/ 端点

## Tasks / Subtasks

- [x] Task 1: 创建 Chat 路由 (AC: #1)
  - [x] 1.1 创建 `backend/app/routers/chat.py`，定义 POST /api/chat 端点
  - [x] 1.2 接收 `{"message": "..."}` 请求体，使用 Pydantic 模型验证
  - [x] 1.3 调用 `store.create_session()` 创建新会话
  - [x] 1.4 使用 FastAPI `BackgroundTasks` 异步调用 `run_agent(session_id, message)`
  - [x] 1.5 立即返回 `{"session_id": "xxx"}` 响应

- [x] Task 2: 创建 Status 路由 (AC: #2, #3)
  - [x] 2.1 创建 `backend/app/routers/status.py`，定义 GET /api/status/{session_id} 端点
  - [x] 2.2 接收可选查询参数 `after_index: int | None = None`
  - [x] 2.3 无 after_index 时：返回完整 `AgentExecutionState`（包含所有 actions）
  - [x] 2.4 有 after_index 时：返回精简响应，`new_actions` 仅包含 index > after_index 的增量动作
  - [x] 2.5 响应始终包含 session_id、status、unread_channels、final_reply 字段
  - [x] 2.6 session_id 不存在时返回 404 错误

- [x] Task 3: 创建 Messages 路由 (AC: #4)
  - [x] 3.1 创建 `backend/app/routers/messages.py`，定义 GET /api/messages/{channel} 端点
  - [x] 3.2 验证 channel 参数为有效枚举值（chat、downstream、upstream）
  - [x] 3.3 调用 `store.get_messages(channel)` 返回消息列表
  - [x] 3.4 无效 channel 返回 400 错误

- [x] Task 4: 统一错误处理 (AC: #5)
  - [x] 4.1 创建统一错误响应模型 `ErrorResponse`（Pydantic）
  - [x] 4.2 在 main.py 中添加 FastAPI 异常处理器，统一捕获 HTTPException 并格式化为 `{"error": true, "error_type": "...", "message": "..."}`
  - [x] 4.3 在 main.py 中添加通用 Exception 处理器，捕获未预期错误返回 500

- [x] Task 5: 路由挂载与 CORS 验证 (AC: #6)
  - [x] 5.1 在 main.py 中导入并挂载所有路由模块（chat、status、messages）
  - [x] 5.2 验证 CORS 配置已正确允许 localhost:5173（已在 Story 1.1 配置）
  - [x] 5.3 删除已有的 /api/health 端点（已不需要，可选保留）

- [x] Task 6: 编写测试 (AC: #1-#6)
  - [x] 6.1 使用 FastAPI TestClient 测试 POST /api/chat（正常请求、空消息）
  - [x] 6.2 测试 GET /api/status/{session_id}（完整响应、增量响应、无效 session_id）
  - [x] 6.3 测试 GET /api/messages/{channel}（各频道、无效频道）
  - [x] 6.4 测试统一错误响应格式
  - [x] 6.5 测试 CORS headers
  - [x] 6.6 所有测试在 mock agent 情况下运行（不依赖 LLM）

## Dev Notes

### 核心设计：薄路由层 + MemoryStore 直连

本 Story 的核心设计原则是**路由层尽可能薄**——Routers 只做请求解析和响应格式化，不含业务逻辑。所有状态读写通过 `store` 单例操作，Agent 执行通过 `run_agent()` 异步入口调用。

```python
# ✅ 正确模式 — 路由层只做 I/O 桥接
@router.post("/api/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    session = store.create_session()
    background_tasks.add_task(run_agent, session.session_id, request.message)
    return {"session_id": session.session_id}
```

```python
# ❌ 错误模式 — 不要在路由中写业务逻辑
@router.post("/api/chat")
async def chat(request: ChatRequest):
    # 不要在这里直接操作 agent 引擎内部逻辑
    # 不要在这里直接修改 store 状态
```

### 异步 Agent 执行：BackgroundTasks

POST /api/chat 使用 FastAPI `BackgroundTasks` 实现异步执行。关键点：

```python
from fastapi import BackgroundTasks

@router.post("/api/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    session = store.create_session()
    background_tasks.add_task(run_agent, session.session_id, request.message)
    return {"session_id": session.session_id}
```

- `background_tasks.add_task()` 将 `run_agent` 注册为后台任务
- `run_agent` 是 async 函数，FastAPI BackgroundTasks 支持 async 函数
- 客户端立即收到 session_id 响应，不等待 Agent 执行完成
- 前端随后通过轮询 GET /api/status 获取执行进度

### 轮询状态端点：增量返回机制

GET /api/status/{session_id} 支持两种模式：

**完整模式（无 after_index）：**
```json
{
  "session_id": "xxx",
  "status": "running",
  "actions": [
    {"index": 0, "action_type": "intent_recognition", ...},
    {"index": 1, "action_type": "skill_loaded", ...},
    {"index": 2, "action_type": "tool_call", ...}
  ],
  "unread_channels": ["upstream"],
  "final_reply": null
}
```

**增量模式（after_index=2）：**
```json
{
  "session_id": "xxx",
  "status": "running",
  "new_actions": [
    {"index": 3, "action_type": "tool_call", ...}
  ],
  "unread_channels": [],
  "final_reply": null
}
```

增量模式使用 `store.get_actions(after_index=N)` 只返回 index > N 的新动作，避免重复传输。

### 请求/响应 Pydantic 模型

需要新增的 API 专用模型（建议在各 router 文件中定义，或在 schemas/models.py 中集中定义）：

```python
# 请求模型
class ChatRequest(BaseModel):
    message: str

# 响应模型
class ChatResponse(BaseModel):
    session_id: str

# 错误响应模型
class ErrorResponse(BaseModel):
    error: bool = True
    error_type: str
    message: str

# 增量状态响应模型
class StatusResponse(BaseModel):
    session_id: str
    status: SessionStatus
    new_actions: list[ActionLogEntry] | None = None
    actions: list[ActionLogEntry] | None = None
    unread_channels: list[str]
    final_reply: str | None = None
```

### CORS 配置（已存在，验证即可）

main.py 中 Story 1.1 已配置的 CORS：

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 统一错误处理

使用 FastAPI 异常处理器统一错误格式：

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_type": exc.detail if isinstance(exc.detail, str) else "HTTP_ERROR",
            "message": str(exc.detail),
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "error_type": "INTERNAL_ERROR",
            "message": "服务器内部错误",
        },
    )
```

### 前一个 Story (1.4) 关键成果

- **Agent 引擎完整实现**：`run_agent(session_id, trigger_message)` async 入口函数
- **LangGraph 状态图**：4 节点（intent_recognition → skill_loading → tool_chain_execution → completion）
- **MemoryStore 单例**：`from app.store.memory import store`，完整 API 已就绪
- **Skill 注册表**：自动扫描 .md 文件，`get_all_skills()` / `get_skill(id)` 可用
- **工具注册表**：自动发现 BaseTool 子类，`get_all_tools()` / `get_tool(name)` 可用
- **126 个测试全部通过**

### MemoryStore API 速查表（供路由使用）

```python
from app.store.memory import store

# 会话管理
session = store.create_session()        # → AgentExecutionState
session = store.get_session()           # → AgentExecutionState | None
store.clear_session()                   # 清空当前会话

# 增量动作查询
actions = store.get_actions(after_index=N)  # → list[ActionLogEntry]（index > N）

# 消息查询
messages = store.get_messages(Channel.chat)  # → list[ChannelMessage]

# 未读管理
store.clear_channel_unread("upstream")
```

### Agent 引擎入口（供 chat 路由调用）

```python
from app.agent.engine import run_agent

# async 函数，通过 BackgroundTasks 调用
await run_agent(session_id="xxx", trigger_message="用户消息内容")
```

### Git 智能

最近 commits：
```
dc7dcff Complete Story 1.4: Agent 引擎与提前离店 Skill
4a4106c Complete Story 1.3: 模拟工具与模拟数据
2104e42 Complete Story 1.2: 数据模型与内存存储
dca5dfc Complete Story 1.1: 项目初始化与开发环境搭建
```

代码模式观察：
- Python 文件使用 snake_case 命名
- 类使用 PascalCase
- 所有注释和文档字符串使用中文
- 测试文件集中在 `backend/tests/` 目录
- 每个 Story 完成后单独 commit
- store 单例通过模块级实例直接导入

### FastAPI 0.133.1 路由模式

```python
# routers/chat.py
from fastapi import APIRouter, BackgroundTasks

router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat")
async def send_message(request: ChatRequest, background_tasks: BackgroundTasks):
    ...
```

```python
# main.py 挂载路由
from app.routers import chat, status, messages

app.include_router(chat.router)
app.include_router(status.router)
app.include_router(messages.router)
```

### 关键技术点

| 项目 | 说明 |
|------|------|
| FastAPI BackgroundTasks | 支持 async 函数，注册后立即返回响应 |
| 路由前缀 | 使用 `APIRouter(prefix="/api")` 统一 /api 前缀 |
| 查询参数 | `after_index: int | None = None` 使用 Python 3.10+ 联合类型 |
| 路径参数验证 | channel 使用 Channel 枚举自动验证 |
| JSON 序列化 | Pydantic 模型自动序列化为 snake_case JSON |
| 异常处理 | 全局 exception_handler 统一错误格式 |

### Project Structure Notes

本 Story 涉及的文件：

```
backend/app/
├── main.py                   # 修改：挂载路由、添加异常处理器
├── routers/
│   ├── __init__.py           # 已存在（空文件，保持空）
│   ├── chat.py               # 新增：POST /api/chat
│   ├── status.py             # 新增：GET /api/status/{session_id}
│   └── messages.py           # 新增：GET /api/messages/{channel}
├── schemas/
│   └── models.py             # 修改：新增 ChatRequest、ChatResponse、ErrorResponse、StatusResponse
├── agent/
│   └── engine.py             # 只读引用（run_agent）
└── store/
    └── memory.py             # 只读引用（store 单例）

backend/tests/
└── test_routers.py           # 新增：API 端点测试
```

### 架构边界提醒

**只做：**
- 创建 3 个路由文件（chat.py、status.py、messages.py）
- 新增 API 请求/响应 Pydantic 模型
- 在 main.py 挂载路由并添加异常处理器
- 编写 API 端点测试

**禁止：**
- 创建 skills.py、tools.py、session.py、history.py 路由（后续 Story 负责）
- 修改 agent/engine.py 或 store/memory.py 的核心逻辑
- 修改已有工具或 Skill 文件
- 创建前端文件
- 添加 WebSocket 通信（架构决定使用轮询）

### 命名规范

| 场景 | 规则 | 示例 |
|------|------|------|
| 路由文件名 | snake_case | `chat.py`, `status.py`, `messages.py` |
| 端点路径 | 小写 + 名词 | `/api/chat`, `/api/status/{session_id}` |
| 查询参数 | snake_case | `after_index` |
| JSON 字段 | snake_case | `session_id`, `new_actions`, `error_type` |
| 请求/响应模型 | PascalCase | `ChatRequest`, `StatusResponse` |

### 测试策略

- 使用 FastAPI `TestClient` 进行同步 API 测试
- Mock `run_agent` 函数（不依赖真实 LLM）
- 预填充 store 数据测试状态查询和消息查询
- 测试错误场景（无效 session_id、无效 channel、空消息）
- 验证 CORS headers
- 保持与前 Story 测试风格一致（pytest + fixture + monkeypatch）

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns] — 9 个 REST 端点定义、错误处理标准、轮询机制
- [Source: _bmad-output/planning-artifacts/architecture.md#Communication Patterns] — 轮询状态响应 JSON 结构、action_type/status/channel 枚举
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns] — 后端目录结构，routers/ 目录位置
- [Source: _bmad-output/planning-artifacts/architecture.md#Architectural Boundaries] — 后端四层架构边界（Routers → Store/Engine）
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.5] — 验收标准（6 条 AC）
- [Source: _bmad-output/planning-artifacts/prd.md#消息输入与交互] — FR1-FR3
- [Source: _bmad-output/planning-artifacts/prd.md#工作流可视化] — FR16-FR19, FR30 轮询
- [Source: _bmad-output/planning-artifacts/prd.md#模拟系统] — FR20-FR21 频道消息
- [Source: _bmad-output/implementation-artifacts/1-4-agent-引擎与提前离店-skill.md] — Agent 引擎、run_agent 入口、store API 用法、Skill 注册表

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

- 无异常。所有路由和测试一次通过，无需调试修复。

### Completion Notes List

- Task 1: 创建 `routers/chat.py` — POST /api/chat 端点，接收 ChatRequest，调用 store.create_session() 创建会话，使用 BackgroundTasks 异步调用 run_agent，立即返回 ChatResponse(session_id)
- Task 2: 创建 `routers/status.py` — GET /api/status/{session_id} 端点，支持完整模式（返回所有 actions）和增量模式（after_index 参数返回 new_actions），session_id 不匹配返回 404
- Task 3: 创建 `routers/messages.py` — GET /api/messages/{channel} 端点，验证 channel 枚举值，调用 store.get_messages 返回消息列表，无效 channel 返回 400
- Task 4: 在 schemas/models.py 新增 ChatRequest、ChatResponse、ErrorResponse、StatusResponse 四个 API 模型。在 main.py 添加 HTTPException 和通用 Exception 两个全局异常处理器，统一错误响应格式 {"error": true, "error_type": "...", "message": "..."}
- Task 5: 在 main.py 导入并挂载 chat.router、status.router、messages.router。CORS 配置沿用 Story 1.1，已验证允许 localhost:5173。保留 /api/health 健康检查端点
- Task 6: 编写 23 个测试 — TestChatEndpoint(5): 正常发送/创建会话/触发 agent/空请求体/无请求体；TestStatusEndpoint(7): 完整响应/增量响应/无新动作/unread_channels/final_reply/无效 session/无会话；TestMessagesEndpoint(6): chat/downstream/upstream/空频道/无效频道/频道过滤；TestErrorResponse(2): 404+400 格式验证；TestCORS(2): 允许/阻止来源；TestHealthCheck(1)

### File List

**新增文件:**
- backend/app/routers/chat.py
- backend/app/routers/status.py
- backend/app/routers/messages.py
- backend/tests/test_routers.py

**修改文件:**
- backend/app/main.py（挂载路由 + 全局异常处理器）
- backend/app/schemas/models.py（新增 ChatRequest、ChatResponse、ErrorResponse、StatusResponse）

## Change Log

- 2026-02-27: 完成 Story 1.5 全部 6 个 Task — 3 个 REST API 路由（chat/status/messages）、4 个 API Pydantic 模型、统一错误处理、路由挂载。编写 23 个新测试全部通过，加上已有 126 个测试共 149 个测试零回归。
- 2026-02-27: Code Review 修复 6 项 — [H1] 添加 RequestValidationError 处理器完善 AC5 统一错误格式；[M1] ChatRequest.message 添加 min_length=1 拒绝空字符串；[M2] 移除 messages.py 多余 f-string；[M3] 新增 422 统一格式测试；[L1] 移除未使用的 store 导入；[L2] 新增空字符串消息测试。总计 151 测试通过。
