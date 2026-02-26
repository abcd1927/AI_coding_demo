---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-02-26'
inputDocuments:
  - prd.md
  - prd-validation-report.md
  - ux-design-specification.md
workflowType: 'architecture'
project_name: 'AI_coding_demo'
user_name: 'Admin'
date: '2026-02-26'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

35 条 FR 覆盖 8 个能力域，架构含义如下：

| 能力域 | FR 范围 | 架构含义 |
|--------|---------|---------|
| 消息输入与交互 | FR1-FR3 | 前端消息输入组件 + API 通信层 |
| 意图识别与 Skill 路由 | FR4-FR6 | Agent 核心调度逻辑，LLM 集成点 |
| 提前离店场景 | FR7-FR12 | Skill 1 定义 + 6 步工具调用链 + 异步等待 |
| 订单取消场景 | FR13-FR15 | Skill 2 定义 + 3 步工具调用链 |
| 工作流可视化 | FR16-FR19 | 前端实时状态渲染 + 轮询机制 |
| 模拟系统 | FR20-FR26 | 模拟层接口抽象 + 模拟数据管理 |
| 管理视角 | FR27-FR29 | Skill/工具注册表 + 管理 API |
| 系统管理 | FR30-FR35 | 轮询 API + 会话管理 + 历史记录 + 配置加载 |

**Non-Functional Requirements:**

| NFR 类别 | 指标 | 架构驱动力 |
|---------|------|----------|
| 性能 - 流程执行 | ≤30 秒完整流程 | LLM 调用延迟管理、工具调用并行化考量 |
| 性能 - 状态更新 | ≤1 秒延迟 | 轮询频率设计、状态存储效率 |
| 性能 - 页面加载 | ≤3 秒 | 前端构建优化、代码分割 |
| 可维护性 - Skill 扩展 | 新增 Skill 无需改核心代码 | Skill 注册机制、配置驱动架构 |
| 可维护性 - 工具扩展 | 新增工具遵循统一接口 | 工具接口规范、注册表模式 |
| 可维护性 - 模拟层替换 | 模拟与业务逻辑分离 | 接口抽象层、依赖注入 |
| 可维护性 - 可调试性 | 代码结构清晰 | 分层架构、日志追踪 |

**Scale & Complexity:**

- Primary domain: 全栈（React SPA + Python AI Agent 后端）
- Complexity level: 中等
- Estimated architectural components: ~8-10 个核心模块（Agent 引擎、Skill 注册、工具注册、模拟层、消息管理、状态同步、前端视图层、管理模块）

### Technical Constraints & Dependencies

| 约束 | 来源 | 架构影响 |
|------|------|---------|
| LangGraph 管理 Agent 工作流 | PRD 技术需求 | 后端架构围绕 LangGraph 状态图构建 |
| Gemini (ChatGoogleGenerative) 作为 LLM | PRD 技术需求 | LLM 集成层需支持模型切换（预留备选方案） |
| Ant Design + React 前端 | UX 设计规格 | 前端技术栈已锁定 |
| 本地运行 (localhost) | PRD 技术需求 | 无需部署架构、无需认证授权 |
| 单用户单会话 | PRD 技术需求 | 无并发、无会话管理、状态可内存存储 |
| 前后端轮询通信 | PRD 技术需求 | REST API + 轮询，非 WebSocket |
| 硬编码模拟数据，无数据库 | PRD 技术需求 | 内存数据存储，重启即重置 |
| 桌面浏览器 (Chrome/Edge) | PRD/UX | 无需跨浏览器、跨平台适配 |

### Cross-Cutting Concerns Identified

1. **Agent 执行状态的实时同步** — 贯穿 Agent 引擎、状态存储、轮询 API、前端渲染。Agent 每执行一步，状态需立即可被前端轮询获取
2. **模拟层接口抽象** — 所有工具（订单查询、消息发送、退款登记、订单取消）需定义统一接口，模拟实现与未来真实实现遵循相同契约
3. **步骤级可观测性** — Agent 的意图识别、Skill 加载、每次工具调用的输入/输出/耗时都需记录，供前端可视化和历史回放使用
4. **Skill 配置驱动** — Skill 定义和工具注册需要配置化管理，支持系统启动时自动加载，新增 Skill/工具无需修改核心代码
5. **多频道消息路由** — 消息需路由到正确的频道（对话/下游群/上游群），前端需维护频道未读状态

## Starter Template Evaluation

### Primary Technology Domain

全栈应用（React SPA 前端 + Python AI Agent 后端），前后端分离架构。

### Technical Preferences

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 前端框架 | React + TypeScript | Ant Design 生态最佳搭配，UX 设计已锁定 |
| 前端构建 | Vite (react-ts 模板) | 最快的构建工具，零配置，SWC 编译 |
| UI 组件库 | Ant Design v6 | UX 设计已锁定，企业级组件开箱即用 |
| 前端包管理 | npm | 最简单，零额外配置 |
| 后端框架 | FastAPI | 异步原生、自动 API 文档、轻量简洁 |
| 后端语言 | Python 3.12+ | LangGraph 生态要求 |
| Python 环境 | pipenv | 用户指定 |
| AI Agent 框架 | LangGraph 1.0.7 | PRD 指定，管理 Agent 工作流状态图 |
| LLM 集成 | langchain-google-genai 4.0.0 | ChatGoogleGenerativeAI，支持 Gemini 模型 |
| ASGI 服务器 | Uvicorn | FastAPI 标准搭配 |

### Starter Options Considered

**前端：**

| 方案 | 评估 |
|------|------|
| Vite + react-ts 模板 | ✅ 选中 — 最轻量，零多余依赖，构建最快 |
| Create React App | ❌ 排除 — 已废弃，不再维护 |
| Next.js | ❌ 排除 — SSR/SSG 能力对本地 SPA Demo 过度 |

**后端：**

| 方案 | 评估 |
|------|------|
| FastAPI 手动结构 | ✅ 选中 — 按需组织，避免多余生成代码 |
| fastapi-new CLI | ❌ 排除 — 生成内容过多（DB、认证等），本项目不需要 |
| Flask | ❌ 排除 — 缺少原生异步支持和自动 API 文档 |

### Selected Starters

#### Frontend: Vite + React + TypeScript

**Initialization Command:**

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install antd
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
- TypeScript 5.x，严格模式
- React 18+，函数组件 + Hooks

**Styling Solution:**
- Ant Design v6 CSS-in-JS（CSS Variables 模式）
- 无需额外 CSS 框架

**Build Tooling:**
- Vite 构建 + SWC 编译
- 开发热更新（HMR）

**Code Organization:**
- `src/` 目录，Vite 默认结构
- 按功能模块组织（将在架构决策阶段细化）

#### Backend: FastAPI + LangGraph (Manual Structure)

**Initialization Command:**

```bash
mkdir backend && cd backend
pipenv install fastapi "uvicorn[standard]" langgraph langchain-google-genai
```

**Architectural Decisions:**

**Language & Runtime:**
- Python 3.12+，类型注解
- 异步 (async/await) 为主

**Web Framework:**
- FastAPI 0.133.1，自动 Swagger API 文档
- Uvicorn ASGI 服务器

**AI Agent Stack:**
- LangGraph 1.0.7 管理 Agent 状态图
- langchain-google-genai 4.0.0（ChatGoogleGenerativeAI）集成 Gemini

**Development Experience:**
- FastAPI 自动交互式 API 文档（/docs）
- Uvicorn 热重载（--reload）
- pipenv 虚拟环境隔离

**Note:** 项目初始化应作为第一个实施 Story 执行。

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- 数据模型定义（Pydantic Models + 内存存储）
- REST API 端点设计（9 个端点覆盖全部 FR）
- 前端状态管理（React Context + Hooks）
- 前端组件组织（按功能模块）
- 前端路由策略（React Router，3 个视图）

**Important Decisions (Shape Architecture):**
- 轮询机制设计（1 秒间隔，增量返回，自动停止）
- 错误处理标准（统一 JSON 错误格式）
- CORS 配置（localhost 跨域）

**Deferred Decisions (Post-MVP):**
- 数据库持久化（Phase 2 接入真实系统时决定）
- 认证授权（Phase 2 生产环境时引入）
- CI/CD 流水线（Phase 2 部署时建立）
- 监控与日志（Phase 3 生产级部署时完善）
- 扩展与并发策略（Phase 3 多用户场景时决定）

### Data Architecture

| 决策 | 选择 | 版本 | 理由 | 影响范围 |
|------|------|------|------|---------|
| 数据验证 | Pydantic Models | Pydantic 2.x（FastAPI 内置） | FastAPI 天然集成，类型安全 | 全部 API 请求/响应 |
| 状态存储 | Python 内存（dict/list） | N/A | 无数据库，Demo 场景重启可清空 | Agent 状态、消息、历史 |
| 历史记录 | 内存列表，每次执行完整快照 | N/A | FR34 要求回放，内存存储足够 | 历史记录 API |

**核心数据模型：**
- `AgentExecutionState` — Agent 执行状态（步骤列表、当前步骤、完成状态）
- `ActionLogEntry` — 单步动作记录（动作类型、标题、输入、输出、状态、时间戳）
- `ChannelMessage` — 频道消息（频道标识、发送者、内容、时间戳）
- `SkillDefinition` — Skill 定义（名称、描述、流程步骤文本）
- `ToolDefinition` — 工具定义（名称、说明、参数描述）
- `ExecutionHistory` — 历史执行记录（执行 ID、触发消息、完整动作日志快照、时间戳）

### Authentication & Security

**不适用。** 本地运行的 PoC Demo，无需认证授权。

- 无用户登录/注册
- 无 API 密钥保护（除 Gemini API Key 通过环境变量管理）
- 无数据加密需求
- Phase 2 接入真实系统时再引入安全机制

### API & Communication Patterns

**API 设计风格：** RESTful JSON API

| 端点 | 方法 | 用途 | 对应 FR |
|------|------|------|---------|
| `/api/chat` | POST | 发送用户消息，触发 Agent 处理 | FR1-FR2 |
| `/api/status/{session_id}` | GET | 轮询获取 Agent 执行状态和动作日志 | FR16-FR19, FR30 |
| `/api/messages/{channel}` | GET | 获取指定频道的消息列表 | FR3, FR20-FR21 |
| `/api/skills` | GET | 获取 Skill 列表 | FR27 |
| `/api/skills/{skill_id}` | GET | 获取 Skill 详情内容 | FR28 |
| `/api/tools` | GET | 获取工具列表 | FR29 |
| `/api/session` | DELETE | 清空当前会话 | FR31 |
| `/api/history` | GET | 获取历史执行记录列表 | FR34 |
| `/api/history/{execution_id}` | GET | 获取某次执行的完整回放数据 | FR34 |

**错误处理标准：**
- 统一 JSON 错误响应：`{ "error": true, "error_type": "ERROR_CODE", "message": "描述" }`
- HTTP 状态码：400（请求错误）、404（未找到）、500（服务器错误）

**轮询机制：**
- 前端每 1 秒轮询 `/api/status/{session_id}`
- 返回增量数据（上次轮询后的新动作），避免重复传输
- Agent 执行完成后前端自动停止轮询

**CORS 配置：**
- 开发阶段允许 `localhost:5173`（Vite）访问 `localhost:8000`（FastAPI）

### Frontend Architecture

**State Management:**

| 决策 | 选择 | 理由 |
|------|------|------|
| 状态管理方案 | React Context + useState/useReducer | 单用户单会话，状态简单，无需外部库 |
| 外部状态库 | 不使用 | PoC Demo 复杂度不需要 Redux/Zustand |

**Component Organization:**

```
src/
├── components/          # 通用组件
│   ├── ActionLogItem/   # 动作日志条目（核心自定义组件）
│   ├── ChatBubble/      # 聊天气泡
│   └── ChannelTab/      # 带红点频道 Tab
├── views/               # 页面级视图
│   ├── DemoView/        # 演示视图（左右分屏）
│   ├── AdminView/       # 管理视图（Skill/工具列表）
│   └── HistoryView/     # 历史记录视图
├── hooks/               # 自定义 Hooks
│   ├── usePolling.ts    # 轮询逻辑
│   └── useSession.ts    # 会话管理
├── services/            # API 调用层
│   └── api.ts           # 封装所有后端 API 调用
├── types/               # TypeScript 类型定义
│   └── index.ts
├── App.tsx              # 根组件 + 路由
└── main.tsx             # 入口
```

**Routing:**

| 路由 | 视图 | 说明 |
|------|------|------|
| `/` | DemoView | 演示视图（左右分屏：消息频道 + 动作日志） |
| `/admin` | AdminView | 管理视图（Skill 列表 + 工具列表） |
| `/history` | HistoryView | 历史执行记录列表 + 回放 |

**依赖：** react-router-dom（路由管理）

**Polling Implementation:**
- 自定义 `usePolling` Hook 封装 setInterval + fetch
- 组件挂载时启动，卸载时自动清理
- Agent 执行完成后自动停止轮询

### Infrastructure & Deployment

**不适用。** 本地 Demo 运行，最小化配置。

| 配置项 | 方案 |
|--------|------|
| 运行环境 | localhost（前端 :5173，后端 :8000） |
| 环境变量 | `.env` 文件管理 Gemini API Key |
| 前端启动 | `npm run dev`（Vite 开发服务器） |
| 后端启动 | `pipenv run uvicorn app.main:app --reload` |

### Decision Impact Analysis

**Implementation Sequence:**
1. 项目初始化（前端 Vite + 后端 FastAPI 骨架）
2. 数据模型定义（Pydantic Models）
3. 模拟层实现（工具接口 + 模拟数据）
4. Agent 引擎搭建（LangGraph 状态图 + Skill/工具注册）
5. REST API 层（FastAPI 端点）
6. 前端基础框架（路由 + 布局 + Context）
7. 核心交互（消息发送 + 轮询 + 动作日志渲染）
8. 管理视图 + 历史记录

**Cross-Component Dependencies:**
- Agent 引擎的状态输出格式 → 决定轮询 API 响应结构 → 决定前端 ActionLogItem 渲染逻辑
- 模拟层工具接口 → 被 Agent 引擎调用 → 产生 ActionLogEntry → 前端展示
- Skill 定义格式 → 同时被 Agent 引擎（路由执行）和管理 API（展示）使用
- 频道消息模型 → 被 Agent 工具调用产生 → 通过消息 API 返回 → 前端频道 Tab 展示

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** 5 大类别中 AI Agent 可能做出不同选择的区域

### Naming Patterns

**Python 代码命名：**

| 元素 | 规则 | 示例 |
|------|------|------|
| 变量/函数 | snake_case | `get_order_info`, `skill_name` |
| 类名 | PascalCase | `AgentExecutionState`, `SkillDefinition` |
| 文件名 | snake_case | `agent_engine.py`, `mock_tools.py` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |

**TypeScript 代码命名：**

| 元素 | 规则 | 示例 |
|------|------|------|
| 变量/函数 | camelCase | `getOrderInfo`, `skillName` |
| 类型/接口 | PascalCase | `ActionLogEntry`, `ChannelMessage` |
| 组件文件 | PascalCase.tsx | `ActionLogItem.tsx`, `ChatBubble.tsx` |
| 非组件文件 | camelCase.ts | `usePolling.ts`, `api.ts` |

**API 命名：**

| 元素 | 规则 | 示例 |
|------|------|------|
| 端点路径 | kebab-case 复数名词 | `/api/skills`, `/api/history` |
| JSON 字段 | snake_case | `{ "session_id": "...", "skill_name": "..." }` |
| 查询参数 | snake_case | `?after_index=3` |

**JSON 字段统一 snake_case 理由：** FastAPI + Pydantic 默认输出 snake_case，前端统一适配，避免双向转换复杂度。前端通过 TypeScript 接口定义做类型映射。

### Structure Patterns

**后端项目组织：**

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口，CORS，路由挂载
│   ├── routers/             # API 路由层
│   │   ├── __init__.py
│   │   ├── chat.py          # /api/chat
│   │   ├── status.py        # /api/status
│   │   ├── messages.py      # /api/messages
│   │   ├── skills.py        # /api/skills
│   │   ├── tools.py         # /api/tools
│   │   ├── session.py       # /api/session
│   │   └── history.py       # /api/history
│   ├── schemas/             # Pydantic 数据模型
│   │   └── models.py
│   ├── agent/               # Agent 引擎核心
│   │   ├── __init__.py
│   │   ├── engine.py        # LangGraph 状态图定义
│   │   ├── skills/          # Skill 定义文件
│   │   │   ├── __init__.py
│   │   │   ├── early_checkout.py
│   │   │   └── order_cancel.py
│   │   └── tools/           # 工具定义
│   │       ├── __init__.py
│   │       ├── base.py      # 工具基类/接口
│   │       ├── order_query.py
│   │       ├── message_send.py
│   │       ├── refund.py
│   │       └── order_cancel.py
│   ├── mock/                # 模拟层
│   │   ├── __init__.py
│   │   ├── data.py          # 硬编码模拟数据
│   │   └── upstream.py      # 上游自动回复模拟
│   └── store/               # 内存状态存储
│       ├── __init__.py
│       └── memory.py        # 会话、消息、历史的内存管理
├── tests/                   # 测试文件集中存放
├── Pipfile
├── Pipfile.lock
└── .env                     # Gemini API Key
```

**前端项目组织：** （已在 Core Architectural Decisions 中定义，此处不重复）

**测试文件位置：**
- 后端：`backend/tests/` 目录集中存放（与 `app/` 平级）
- 前端：组件同目录下 `*.test.tsx` 共存（Vite 默认支持）

### Format Patterns

**API 成功响应 — 直接返回数据（不使用 wrapper）：**

```json
// GET /api/skills
[
  { "skill_id": "early_checkout", "name": "提前离店", "description": "..." },
  { "skill_id": "order_cancel", "name": "订单取消", "description": "..." }
]
```

**API 错误响应 — 统一结构：**

```json
{
  "error": true,
  "error_type": "SKILL_NOT_FOUND",
  "message": "无法匹配任何已注册的 Skill"
}
```

**日期时间格式：** ISO 8601 字符串（`"2026-02-26T14:30:00Z"`）

### Communication Patterns

**轮询状态响应结构：**

```json
// GET /api/status/{session_id}?after_index=3
{
  "session_id": "xxx",
  "status": "running",
  "new_actions": [
    {
      "index": 4,
      "action_type": "tool_call",
      "title": "调用工具：查询订单",
      "summary": "查询订单号 HT20260301001",
      "status": "success",
      "detail": { "input": {...}, "output": {...} },
      "timestamp": "2026-02-26T14:30:01Z"
    }
  ],
  "unread_channels": ["upstream"],
  "final_reply": null
}
```

**action_type 枚举值：**
- `intent_recognition` — 意图识别
- `skill_loaded` — Skill 加载
- `tool_call` — 工具调用
- `waiting` — 等待外部回复
- `message_sent` — 消息发送
- `completed` — 流程完成

**status 枚举值（动作级）：**
- `running` — 执行中
- `success` — 成功
- `error` — 失败

**status 枚举值（会话级）：**
- `idle` — 空闲
- `running` — Agent 执行中
- `completed` — 流程完成
- `error` — 流程异常终止

**频道标识符：**
- `chat` — 对话频道
- `downstream` — 下游群
- `upstream` — 上游群

### Process Patterns

**前端错误处理：**
- API 调用统一在 `services/api.ts` 中 try/catch
- 错误通过 Ant Design `message.error()` 全局提示
- 不使用 React Error Boundary（Demo 复杂度不需要）

**前端 Loading 状态：**
- 使用 React state 布尔值
- 命名统一：`isLoading`、`isSending`
- 加载中显示 Ant Design `Spin` 组件

**后端错误处理：**
- FastAPI 异常处理器统一捕获并格式化错误响应
- Agent 工具调用失败记录到 ActionLogEntry（status: error），不中断 API 响应

### Enforcement Guidelines

**All AI Agents MUST:**

1. 遵循上述命名规则——Python snake_case、TypeScript camelCase、API JSON snake_case
2. 新增文件放在对应模块目录中——不在根目录创建孤立文件
3. 新增 API 端点遵循 RESTful 命名和响应格式
4. 新增工具继承统一基类/接口
5. 新增 Skill 放在 `agent/skills/` 目录并注册到 Skill 注册表

**Anti-Patterns（禁止）：**
- 在 API JSON 中混用 camelCase 和 snake_case
- 在前端组件中直接调用 fetch，绕过 `services/api.ts`
- 在后端路由中直接写业务逻辑，绕过 Agent 引擎
- 硬编码模拟数据散落在各处，不集中在 `mock/` 目录

## Project Structure & Boundaries

### Complete Project Directory Structure

```
AI_coding_demo/
├── frontend/                          # React SPA 前端
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── .gitignore
│   ├── public/
│   └── src/
│       ├── main.tsx                   # 应用入口
│       ├── App.tsx                    # 根组件 + React Router
│       ├── App.css                    # 全局样式（最小化）
│       ├── types/
│       │   └── index.ts              # 全局 TypeScript 类型定义
│       ├── services/
│       │   └── api.ts                # 所有后端 API 调用封装
│       ├── hooks/
│       │   ├── usePolling.ts         # 轮询逻辑 Hook
│       │   └── useSession.ts         # 会话状态管理 Hook
│       ├── context/
│       │   └── AppContext.tsx         # React Context 全局状态
│       ├── components/
│       │   ├── ActionLogItem/
│       │   │   ├── ActionLogItem.tsx  # 动作日志条目组件
│       │   │   └── ActionLogItem.css
│       │   ├── ChatBubble/
│       │   │   ├── ChatBubble.tsx     # 聊天气泡组件
│       │   │   └── ChatBubble.css
│       │   └── ChannelTab/
│       │       └── ChannelTab.tsx     # 带红点频道 Tab 组件
│       └── views/
│           ├── DemoView/
│           │   ├── DemoView.tsx       # 演示视图（左右分屏主页面）
│           │   ├── MessagePanel.tsx   # 左侧消息面板（含三频道）
│           │   └── ActionLogPanel.tsx # 右侧动作日志面板
│           ├── AdminView/
│           │   └── AdminView.tsx      # 管理视图（Skill/工具列表）
│           └── HistoryView/
│               └── HistoryView.tsx    # 历史记录视图
│
├── backend/                           # Python FastAPI 后端
│   ├── Pipfile
│   ├── Pipfile.lock
│   ├── .env                          # Gemini API Key（不提交 git）
│   ├── .env.example                  # 环境变量模板
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 入口，CORS，路由挂载
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py               # POST /api/chat
│   │   │   ├── status.py             # GET  /api/status/{session_id}
│   │   │   ├── messages.py           # GET  /api/messages/{channel}
│   │   │   ├── skills.py             # GET  /api/skills, /api/skills/{skill_id}
│   │   │   ├── tools.py              # GET  /api/tools
│   │   │   ├── session.py            # DELETE /api/session
│   │   │   └── history.py            # GET  /api/history, /api/history/{execution_id}
│   │   ├── schemas/
│   │   │   └── models.py             # Pydantic 数据模型（全部集中定义）
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py             # LangGraph 状态图 + Agent 调度核心
│   │   │   ├── skills/
│   │   │   │   ├── __init__.py       # Skill 注册表（扫描并加载 .md 文件）
│   │   │   │   ├── early_checkout.md # Skill 1：提前离店（自然语言流程描述）
│   │   │   │   └── order_cancel.md   # Skill 2：订单取消（自然语言流程描述）
│   │   │   └── tools/
│   │   │       ├── __init__.py       # 工具注册表（自动发现和注册）
│   │   │       ├── base.py           # 工具基类/接口定义
│   │   │       ├── order_query.py    # 工具：订单查询
│   │   │       ├── message_send.py   # 工具：消息发送
│   │   │       ├── refund.py         # 工具：退款登记
│   │   │       └── order_cancel.py   # 工具：订单取消
│   │   ├── mock/
│   │   │   ├── __init__.py
│   │   │   ├── data.py               # 硬编码模拟数据（订单、供应商等）
│   │   │   └── upstream.py           # 上游自动回复模拟逻辑
│   │   └── store/
│   │       ├── __init__.py
│   │       └── memory.py             # 内存状态管理（会话、消息、历史）
│   └── tests/
│       ├── __init__.py
│       ├── test_routers.py           # API 端点测试
│       ├── test_agent.py             # Agent 引擎测试
│       └── test_tools.py             # 工具调用测试
│
├── _bmad/                             # BMAD 工作流（已存在）
├── _bmad-output/                      # 规划产出物（已存在）
├── .gitignore
└── README.md
```

### Architectural Boundaries

**API 边界（前后端分离点）：**

```
前端 (localhost:5173)  ←── REST JSON API ──→  后端 (localhost:8000)
     React SPA                                    FastAPI
```

- 前端只通过 `services/api.ts` 与后端通信
- 所有 API 端点统一 `/api/` 前缀
- JSON 字段统一 snake_case

**后端分层边界：**

```
Routers (API 层)
    ↓ 调用
Store (状态管理层) ←→ Agent Engine (业务逻辑层)
                          ↓ 调用
                    Skills (流程定义层)
                          ↓ 调用
                    Tools (工具执行层)
                          ↓ 调用
                    Mock (模拟数据层)
```

- **Routers** 只做请求解析和响应格式化，不含业务逻辑
- **Agent Engine** 是唯一调用 Skills 和 Tools 的入口
- **Tools** 通过基类接口访问 Mock 层，未来可替换为真实接口
- **Store** 是唯一的状态读写点，Routers 和 Engine 都通过它操作状态

**模拟层替换边界：**

```
Tools (base.py 定义接口)
    ├── 当前：调用 mock/ 目录下的模拟实现
    └── 未来：替换为真实 API 调用（仅改 Tools 实现，不动 Engine/Routers）
```

### Requirements to Structure Mapping

| FR 范围 | 前端文件 | 后端文件 |
|---------|---------|---------|
| FR1-FR3 消息输入 | `MessagePanel.tsx`, `ChatBubble/` | `routers/chat.py` |
| FR4-FR6 意图识别 | `ActionLogItem/`（展示结果） | `agent/engine.py`, `agent/skills/__init__.py` |
| FR7-FR12 提前离店 | （通过动作日志展示） | `agent/skills/early_checkout.md`, `agent/tools/*` |
| FR13-FR15 订单取消 | （通过动作日志展示） | `agent/skills/order_cancel.md`, `agent/tools/*` |
| FR16-FR19 工作流可视化 | `ActionLogPanel.tsx`, `ActionLogItem/` | `routers/status.py`, `store/memory.py` |
| FR20-FR26 模拟系统 | — | `mock/data.py`, `mock/upstream.py`, `agent/tools/*` |
| FR27-FR29 管理视角 | `AdminView/` | `routers/skills.py`, `routers/tools.py` |
| FR30 状态轮询 | `hooks/usePolling.ts` | `routers/status.py` |
| FR31 清空会话 | `App.tsx`（按钮） | `routers/session.py`, `store/memory.py` |
| FR32 视图切换 | `App.tsx`（React Router） | — |
| FR33 错误处理 | `services/api.ts` | `agent/engine.py` |
| FR34 历史记录 | `HistoryView/` | `routers/history.py`, `store/memory.py` |
| FR35 配置加载 | — | `agent/skills/__init__.py`, `agent/tools/__init__.py` |

### Data Flow

```
用户输入消息
    ↓
前端 POST /api/chat
    ↓
后端 chat router → Agent Engine 启动（异步）
    ↓
Agent Engine: 意图识别 → Skill 加载 → 工具调用链
    ↓ (每一步写入 Store)
Store.memory 记录 ActionLogEntry + ChannelMessage
    ↓
前端 GET /api/status (每秒轮询)
    ↓
Store 返回增量 new_actions
    ↓
前端 ActionLogPanel 逐条渲染
    ↓
流程完成 → 前端停止轮询 → 展示最终回复
```

### Development Workflow

| 操作 | 命令 |
|------|------|
| 启动前端开发服务器 | `cd frontend && npm run dev` |
| 启动后端开发服务器 | `cd backend && pipenv run uvicorn app.main:app --reload` |
| 安装前端依赖 | `cd frontend && npm install` |
| 安装后端依赖 | `cd backend && pipenv install` |
| 运行后端测试 | `cd backend && pipenv run pytest` |

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:** 所有技术选型经过版本验证，无兼容性冲突。React 18+ / Ant Design v6 / Vite / TypeScript 5.x 前端栈完全兼容；Python 3.12+ / FastAPI 0.133.x / LangGraph 1.0.7 / langchain-google-genai 4.0.0 后端栈完全兼容。

**Pattern Consistency:** 命名规则在前端（camelCase）、后端（snake_case）、API 边界（snake_case JSON）三层各自一致，无混用风险。

**Structure Alignment:** 后端四层架构（Routers → Engine → Skills/Tools → Mock）边界清晰，模拟层替换边界在 Tools 基类接口层。前端三层（Views → Components → Hooks/Services）职责明确。

### Requirements Coverage Validation ✅

**Functional Requirements:** 35/35 全部有对应的架构组件和文件支持。每条 FR 已映射到具体的前端文件和/或后端文件。

**Non-Functional Requirements:** 7/7 全部通过架构手段满足。性能指标通过异步执行 + 轮询机制 + Vite 构建保障；可维护性通过 Skill .md 文件 + 工具基类接口 + 分层架构保障。

### Implementation Readiness Validation ✅

**Decision Completeness:** 所有关键技术选型已确定并带版本号。实现模式有具体示例和反例。一致性规则覆盖命名、结构、格式、通信、过程五大类别。

**Structure Completeness:** 完整目录树具体到文件级别，每个文件有用途说明。FR → 文件映射表确保开发时可直接定位。

**Pattern Completeness:** 轮询协议有完整 JSON 结构定义。错误响应有统一格式。action_type / status / channel 枚举值已全部定义。

### Validation Issues Addressed

| 问题 | 优先级 | 解决方案 | 状态 |
|------|--------|---------|------|
| Skill 文件格式错误定义为 .py | Critical | 修正为 .md 文件，Skill 注册表扫描并加载 .md 内容 | ✅ 已修正 |

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] 项目上下文深入分析
- [x] 规模和复杂度评估（中等）
- [x] 技术约束识别（8 项）
- [x] 横切关注点映射（5 项）

**✅ Architectural Decisions**
- [x] 关键决策带版本号文档化
- [x] 技术栈完整指定（前端 + 后端 + AI Agent）
- [x] API 集成模式定义（9 个端点）
- [x] 性能考量已纳入

**✅ Implementation Patterns**
- [x] 命名规则建立（Python / TypeScript / API 三层）
- [x] 结构模式定义（前后端目录组织）
- [x] 通信模式指定（轮询协议 + JSON 结构）
- [x] 过程模式文档化（错误处理 + Loading 状态）

**✅ Project Structure**
- [x] 完整目录结构定义（具体到文件）
- [x] 组件边界建立（4 层后端 + 3 层前端）
- [x] 集成点映射（API 边界 + 模拟层替换边界）
- [x] FR → 文件映射完成（35 条 FR 全覆盖）

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
1. 技术栈全部经过版本验证，无兼容性风险
2. Skill 采用 .md 文件设计，完美实现"新增场景无需改代码"的核心价值
3. 模拟层替换边界在 Tools 基类接口层，Phase 2 接入真实系统改动最小化
4. 轮询协议和数据模型定义具体到 JSON 字段级别，前后端开发可并行
5. 35 条 FR 全部映射到具体文件，开发时可直接定位

**Areas for Future Enhancement:**
- LangGraph 状态图节点设计在实施阶段细化
- Phase 2 时引入认证授权和数据库持久化
- Phase 3 时建立 CI/CD 和监控体系

### Implementation Handoff

**AI Agent Guidelines:**
- 严格遵循所有架构决策和命名规则
- 新增文件放入对应模块目录
- 前端所有 API 调用通过 `services/api.ts`
- 后端所有业务逻辑通过 Agent Engine
- Skill 文件为 .md 格式，新增 Skill 只需新增 .md 文件并注册

**First Implementation Priority:**
1. 前端：`npm create vite@latest frontend -- --template react-ts && cd frontend && npm install antd react-router-dom`
2. 后端：`mkdir backend && cd backend && pipenv install fastapi "uvicorn[standard]" langgraph langchain-google-genai`
3. 建立项目骨架（目录结构 + 入口文件）
