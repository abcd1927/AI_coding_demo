---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - prd.md
  - prd-validation-report.md
  - architecture.md
  - ux-design-specification.md
---

# AI_coding_demo - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for AI_coding_demo, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**消息输入与交互**

- FR1: 操作者可以在输入框中输入自由文本消息模拟下游客服请求
- FR2: 操作者可以发送消息触发 Agent 处理流程
- FR3: 操作者可以查看 Agent 最终回复给下游的处理结果

**意图识别与 Skill 路由**

- FR4: Agent 可以分析接收到的消息内容并识别业务意图
- FR5: Agent 可以根据识别到的意图自动匹配并加载对应的 Skill
- FR6: Agent 在无法匹配任何 Skill 时可以返回友好提示并展示当前已支持的场景列表

**提前离店场景（Skill 1）**

- FR7: Agent 可以从用户消息中提取订单号和客户诉求信息
- FR8: Agent 可以调用订单查询工具，根据订单号获取对应的供应商订单号
- FR9: Agent 可以调用消息发送工具，向上游群发送供应商订单号和客户诉求
- FR10: Agent 可以等待模拟上游的自动回复并接收处理结果
- FR11: Agent 可以调用退款登记工具，根据上游回复执行退款操作
- FR12: Agent 可以调用消息发送工具，向下游群回复最终处理结果

**订单取消场景（Skill 2）**

- FR13: Agent 可以从用户消息中提取订单号和取消请求信息
- FR14: Agent 可以调用订单取消工具执行取消操作
- FR15: Agent 可以向下游回复取消结果（成功或失败）

**工作流可视化**

- FR16: 操作者可以实时查看 Agent 当前正在执行的步骤
- FR17: 操作者可以查看每一步的工具名称、输入参数和返回结果
- FR18: 操作者可以查看 Agent 的意图识别结果和加载的 Skill 名称
- FR19: 操作者可以查看 Agent 执行过程中的完整信息流（从接收消息到最终回复）

**模拟系统**

- FR20: 系统可以模拟企微下游群消息的接收
- FR21: 系统可以模拟企微上游群消息的发送和接收
- FR22: 系统可以模拟上游供应商的自动回复（处理完成）
- FR23: 系统可以模拟业务系统的订单查询功能（根据订单号返回供应商订单号）
- FR24: 系统可以模拟业务系统的退款登记功能（返回退款成功/失败）
- FR25: 系统可以模拟业务系统的订单取消功能（返回取消成功/失败）
- FR26: 模拟系统对无效输入数据（如不存在的订单号）可以返回合理的错误信息

**管理视角**

- FR27: 操作者可以查看当前系统中所有已注册的 Skill 列表
- FR28: 操作者可以查看每个 Skill 的自然语言流程描述内容
- FR29: 操作者可以查看当前系统中所有已注册的工具列表及其说明

**系统管理**

- FR30: 前端可以通过轮询方式获取 Agent 的最新执行状态和步骤信息
- FR31: 操作者可以清空当前会话并重新开始新一轮演示
- FR32: 操作者可以在演示视图和管理视图之间自由切换
- FR33: Agent 在工具调用返回错误时可以展示错误信息并优雅地结束当前流程
- FR34: 操作者可以查看历史执行记录，并可选择回放某一次的完整执行过程
- FR35: 系统启动时可以从配置中自动加载 Skill 定义和工具定义

### NonFunctional Requirements

**性能**

- NFR1: Agent 单次完整流程执行（从接收消息到最终回复）应在 30 秒内完成
- NFR2: 前端轮询间隔不超过 1 秒，确保可视化面板更新流畅
- NFR3: 页面首次加载在 3 秒内完成

**可维护性**

- NFR4: 新增 Skill 只需添加 Skill 配置文件，无需修改核心代码逻辑
- NFR5: 新增模拟工具只需注册工具定义，遵循统一的工具接口规范
- NFR6: 模拟数据与业务逻辑分离，便于后续替换为真实接口
- NFR7: 代码结构清晰，便于单人调试和迭代

### Additional Requirements

**来自架构文档：**

- **Starter Template**: 前端使用 Vite + react-ts 模板初始化，后端使用 FastAPI + LangGraph 手动结构初始化（影响 Epic 1 Story 1）
- LangGraph 1.0.7 状态图管理 Agent 工作流和状态
- Pydantic 2.x 数据模型定义（6 个核心模型：AgentExecutionState、ActionLogEntry、ChannelMessage、SkillDefinition、ToolDefinition、ExecutionHistory）
- 内存存储（Python dict/list），无数据库，重启即重置
- 9 个 REST API 端点覆盖全部 FR
- 轮询机制：1 秒间隔、增量返回（after_index 参数）、Agent 完成后自动停止
- CORS 配置：允许 localhost:5173 访问 localhost:8000
- 后端四层架构：Routers → Store/Engine → Skills/Tools → Mock
- Skill 文件为 .md 格式，注册表自动扫描加载
- 工具基类接口定义（base.py），统一工具注册和发现
- 统一命名规则：Python snake_case、TypeScript camelCase、API JSON snake_case
- 统一错误响应格式：`{ "error": true, "error_type": "...", "message": "..." }`
- action_type 枚举值：intent_recognition、skill_loaded、tool_call、waiting、message_sent、completed
- status 枚举值（动作级）：running、success、error
- status 枚举值（会话级）：idle、running、completed、error
- 频道标识符：chat、downstream、upstream
- 前端 React Context + useState/useReducer 状态管理
- React Router 三路由：/（演示）、/admin（管理）、/history（历史）
- 前端所有 API 调用通过 services/api.ts 封装
- 后端测试集中在 backend/tests/ 目录

**来自 UX 设计文档：**

- 左右分屏布局（左侧 35% 消息面板 + 右侧 65% 动作日志面板）
- 三频道消息系统：对话（可写）、下游群（只读）、上游群（只读）
- 动作日志为实时追加模式（非预设流程图），只展示已发生的动作
- 频道 Tab 红点未读提示（Badge dot 模式）
- 3 个核心自定义组件：ActionLogItem（Timeline+Collapse）、ChatBubble（自定义CSS）、ChannelTab（Tabs+Badge）
- 状态色彩系统：蓝色#1677FF=执行中、绿色#52C41A=成功、红色#FF4D4F=失败、橙色#FAAD14=等待
- 渐进式信息披露：步骤默认折叠，点击可展开查看输入/输出详情
- 投屏友好字号：页面标题24px、区域标题18px、步骤标题16px、正文14px
- 空状态设计：动作日志欢迎提示、频道无消息提示、历史记录为空提示
- 顶部导航栏 56px：演示 | 管理 | 历史 + 清空会话按钮
- 新动作追加时 fadeIn + slideUp 入场动画，自动滚动到底部
- Ant Design ConfigProvider 统一配色

### FR Coverage Map

| FR | Epic | 描述 |
|----|------|------|
| FR1 | Epic 1 | 输入自由文本消息 |
| FR2 | Epic 1 | 发送消息触发 Agent |
| FR3 | Epic 1 | 查看 Agent 最终回复 |
| FR4 | Epic 1 | 分析消息识别意图 |
| FR5 | Epic 1 | 匹配并加载 Skill |
| FR6 | Epic 2 | 未匹配时友好提示 |
| FR7 | Epic 1 | 提取订单号和诉求 |
| FR8 | Epic 1 | 调用订单查询工具 |
| FR9 | Epic 1 | 向上游群发送消息 |
| FR10 | Epic 1 | 等待上游自动回复 |
| FR11 | Epic 1 | 调用退款登记工具 |
| FR12 | Epic 1 | 向下游群回复结果 |
| FR13 | Epic 2 | 提取取消请求信息 |
| FR14 | Epic 2 | 调用订单取消工具 |
| FR15 | Epic 2 | 回复取消结果 |
| FR16 | Epic 1 | 实时查看执行步骤 |
| FR17 | Epic 1 | 查看工具名称和参数 |
| FR18 | Epic 1 | 查看意图识别结果 |
| FR19 | Epic 1 | 查看完整信息流 |
| FR20 | Epic 1 | 模拟下游群消息接收 |
| FR21 | Epic 1 | 模拟上游群消息收发 |
| FR22 | Epic 1 | 模拟上游自动回复 |
| FR23 | Epic 1 | 模拟订单查询 |
| FR24 | Epic 1 | 模拟退款登记 |
| FR25 | Epic 2 | 模拟订单取消 |
| FR26 | Epic 1 | 无效输入错误信息 |
| FR27 | Epic 3 | 查看 Skill 列表 |
| FR28 | Epic 3 | 查看 Skill 内容 |
| FR29 | Epic 3 | 查看工具列表 |
| FR30 | Epic 1 | 轮询获取执行状态 |
| FR31 | Epic 2 | 清空会话重新开始 |
| FR32 | Epic 3 | 视图切换 |
| FR33 | Epic 1 | 错误信息展示 |
| FR34 | Epic 3 | 历史记录与回放 |
| FR35 | Epic 1 | 自动加载 Skill/工具配置 |

**覆盖率：35/35 FR 全部映射，无遗漏。**

## Epic List

### Epic 1: 提前离店完整演示

用户可以打开页面，输入一条提前离店消息，亲眼看到 Agent 在可视化面板中逐步完成"意图识别 → 查询订单 → 通知上游 → 等待回复 → 退款登记 → 回复下游"的完整工作流程，同时在三个频道中看到消息的流转。

**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR7, FR8, FR9, FR10, FR11, FR12, FR16, FR17, FR18, FR19, FR20, FR21, FR22, FR23, FR24, FR26, FR30, FR33, FR35

### Epic 2: 多场景支持与异常处理

用户可以尝试输入订单取消请求，看到 Agent 走完全不同的流程路径，验证架构通用性；输入无效消息时看到 Agent 友好拒绝并展示已支持场景列表；一键清空会话重新开始演示。

**FRs covered:** FR6, FR13, FR14, FR15, FR25, FR31

### Epic 3: 管理视角与历史记录

用户可以切换到管理页面查看 Skill 列表和工具列表，点开 Skill 阅读自然语言流程描述；查看历史执行记录并回放某次完整流程。

**FRs covered:** FR27, FR28, FR29, FR32, FR34

## Epic 1: 提前离店完整演示

用户可以打开页面，输入一条提前离店消息，亲眼看到 Agent 在可视化面板中逐步完成"意图识别 → 查询订单 → 通知上游 → 等待回复 → 退款登记 → 回复下游"的完整工作流程，同时在三个频道中看到消息的流转。

### Story 1.1: 项目初始化与开发环境搭建

As a 开发者,
I want 使用 Vite + React + TypeScript 初始化前端项目，使用 FastAPI + LangGraph 初始化后端项目，并建立完整目录结构,
So that 拥有可运行的项目骨架，所有后续开发有统一的基础。

**Acceptance Criteria:**

**Given** 项目根目录
**When** 执行前端初始化命令 `npm create vite@latest frontend -- --template react-ts` 并安装 antd、react-router-dom
**Then** 前端开发服务器可在 localhost:5173 正常启动并显示默认页面

**Given** 前端项目已初始化
**When** 查看 package.json
**Then** 包含 react、react-dom、antd、react-router-dom 依赖

**Given** 项目根目录
**When** 执行后端初始化 `mkdir backend && cd backend && pipenv install fastapi "uvicorn[standard]" langgraph langchain-google-genai`
**Then** 后端 Pipfile 中包含所有指定依赖

**Given** 后端依赖已安装
**When** 创建 app/main.py 入口并启动 uvicorn
**Then** 后端服务可在 localhost:8000 正常启动，访问 /docs 可看到 FastAPI 自动文档

**Given** 前后端均可启动
**When** 查看项目目录结构
**Then** 前端 src/ 下包含 components/、views/、hooks/、services/、types/、context/ 目录；后端 app/ 下包含 routers/、schemas/、agent/（含 skills/、tools/）、mock/、store/ 目录

**Given** 后端项目
**When** 查看 .env.example
**Then** 包含 GOOGLE_API_KEY 环境变量模板

### Story 1.2: 数据模型与内存存储

As a 开发者,
I want 定义所有核心 Pydantic 数据模型和内存状态管理模块,
So that 后续的 Agent 引擎、API 层和前端都有统一的数据契约。

**Acceptance Criteria:**

**Given** schemas/models.py
**When** 定义数据模型
**Then** 包含以下 Pydantic 模型：AgentExecutionState、ActionLogEntry、ChannelMessage、SkillDefinition、ToolDefinition、ExecutionHistory

**Given** ActionLogEntry 模型
**When** 查看字段定义
**Then** 包含 index(int)、action_type(枚举：intent_recognition/skill_loaded/tool_call/waiting/message_sent/completed)、title(str)、summary(str)、status(枚举：running/success/error)、detail(dict, optional)、timestamp(datetime)

**Given** ChannelMessage 模型
**When** 查看字段定义
**Then** 包含 channel(枚举：chat/downstream/upstream)、sender(str)、content(str)、timestamp(datetime)

**Given** AgentExecutionState 模型
**When** 查看字段定义
**Then** 包含 session_id(str)、status(枚举：idle/running/completed/error)、actions(list[ActionLogEntry])、final_reply(str, optional)、unread_channels(list[str])

**Given** store/memory.py
**When** 实例化内存存储
**Then** 提供会话状态的创建/读取/更新、消息的添加/按频道查询、动作日志的追加/增量查询功能

**Given** 内存存储模块
**When** 调用 add_action 添加一条动作后以 get_actions(after_index=N) 查询
**Then** 仅返回 index > N 的增量动作记录

### Story 1.3: 模拟工具与模拟数据

As a 开发者,
I want 实现工具基类接口、3 个模拟工具（订单查询、消息发送、退款登记）以及硬编码模拟数据和上游自动回复逻辑,
So that Agent 引擎可以调用这些工具执行模拟业务操作，模拟完整的提前离店流程。

**Acceptance Criteria:**

**Given** agent/tools/base.py
**When** 定义工具基类
**Then** 包含统一接口：name(str)、description(str)、execute(input) → output，所有工具继承此基类（NFR5）

**Given** agent/tools/order_query.py
**When** 调用执行并传入有效订单号 "HT20260301001"
**Then** 返回对应的供应商订单号 "SUP-88901"（FR23）

**Given** agent/tools/order_query.py
**When** 调用执行并传入无效订单号
**Then** 返回合理的错误信息"订单不存在"（FR26）

**Given** agent/tools/message_send.py
**When** 调用执行并指定目标频道（downstream/upstream）和消息内容
**Then** 消息被添加到对应频道的内存存储中（FR20, FR21）

**Given** agent/tools/refund.py
**When** 调用执行并传入订单信息
**Then** 返回退款登记成功结果（FR24）

**Given** mock/data.py
**When** 查看模拟数据
**Then** 包含至少 3 条硬编码订单记录（订单号 → 供应商订单号映射）

**Given** mock/upstream.py
**When** 上游收到消息后
**Then** 自动生成模拟上游回复"已处理完成"并添加到 upstream 频道（FR22）

**Given** agent/tools/__init__.py
**When** 导入工具注册表
**Then** 自动发现并注册所有工具，提供按名称查找工具的能力（NFR5）

### Story 1.4: Agent 引擎与提前离店 Skill

As a 开发者,
I want 搭建基于 LangGraph 的 Agent 引擎，实现意图识别、Skill 路由和提前离店 Skill 的完整工具调用链,
So that Agent 可以接收消息、识别意图、加载 Skill 并逐步执行完整的提前离店流程。

**Acceptance Criteria:**

**Given** agent/engine.py
**When** 定义 LangGraph 状态图
**Then** 包含意图识别、Skill 加载、工具调用链执行、流程完成等节点

**Given** Agent 引擎收到消息 "订单号 HT20260301001 的客人申请提前离店"
**When** 执行意图识别
**Then** 通过 Gemini LLM 识别为"提前离店"意图，并记录 ActionLogEntry（action_type=intent_recognition）（FR4）

**Given** 意图识别为"提前离店"
**When** Skill 路由
**Then** 自动加载 early_checkout Skill，记录 ActionLogEntry（action_type=skill_loaded）（FR5）

**Given** Skill 已加载
**When** 执行工具调用链
**Then** 按顺序执行：提取订单号(FR7) → 查询订单(FR8) → 发送上游消息(FR9) → 等待上游回复(FR10) → 退款登记(FR11) → 发送下游回复(FR12)，每步记录 ActionLogEntry

**Given** 每次工具调用
**When** 执行完成
**Then** 记录 ActionLogEntry 包含 action_type、title、summary、输入输出详情、状态和时间戳（FR16, FR17）

**Given** agent/skills/early_checkout.md
**When** 查看内容
**Then** 包含提前离店场景的自然语言流程描述（NFR4）

**Given** agent/skills/__init__.py
**When** 系统启动
**Then** 自动扫描 skills/ 目录加载所有 .md Skill 文件并注册到 Skill 列表（FR35）

**Given** Agent 工具调用返回错误
**When** 处理错误
**Then** 记录错误 ActionLogEntry（status=error）并优雅终止当前流程（FR33）

**Given** 完整流程执行
**When** 从接收消息到最终回复
**Then** 在 30 秒内完成（NFR1）

### Story 1.5: 后端 REST API 与通信层

As a 操作者,
I want 通过 REST API 发送消息给 Agent 并轮询获取执行状态和频道消息,
So that 前端可以与后端通信，实时展示 Agent 的工作过程。

**Acceptance Criteria:**

**Given** POST /api/chat
**When** 发送 {"message": "订单号 HT20260301001 的客人申请提前离店"}
**Then** 返回 {"session_id": "xxx"}，Agent 在后台异步启动处理（FR2）

**Given** GET /api/status/{session_id}
**When** 不带 after_index 参数
**Then** 返回完整的 AgentExecutionState 包含所有 actions（FR30）

**Given** GET /api/status/{session_id}?after_index=3
**When** 轮询
**Then** 只返回 index > 3 的增量 new_actions，避免重复传输

**Given** GET /api/messages/{channel}
**When** channel 分别为 chat、downstream、upstream
**Then** 返回对应频道的消息列表（FR3, FR20, FR21）

**Given** API 请求出错
**When** 返回错误响应
**Then** 格式统一为 {"error": true, "error_type": "ERROR_CODE", "message": "描述"}

**Given** FastAPI 应用
**When** 配置 CORS
**Then** 允许 localhost:5173 来源的请求访问所有 /api/ 端点

### Story 1.6: 前端框架与演示视图布局

As a 操作者,
I want 打开页面看到清晰的演示界面布局——顶部导航栏、左侧消息面板、右侧动作日志面板,
So that 拥有专业的演示框架，为后续交互功能提供视觉容器。

**Acceptance Criteria:**

**Given** 用户打开 localhost:5173
**When** 页面加载
**Then** 看到顶部导航栏（56px），包含"演示"、"管理"、"历史"三个导航项（FR32）

**Given** 演示视图
**When** 查看布局
**Then** 左侧消息面板占 35% 宽度，右侧动作日志面板占 65% 宽度

**Given** 右侧动作日志面板
**When** 尚未发送消息
**Then** 显示欢迎提示"发送一条消息，观看 Agent 的工作过程"

**Given** src/types/index.ts
**When** 查看类型定义
**Then** 包含与后端 Pydantic 模型对应的 TypeScript 类型（ActionLogEntry、ChannelMessage、AgentExecutionState 等），JSON 字段为 snake_case

**Given** src/services/api.ts
**When** 查看 API 封装
**Then** 包含 sendMessage、pollStatus、getMessages 等函数，所有后端调用通过此模块

**Given** src/context/AppContext.tsx
**When** 查看全局状态
**Then** 使用 React Context 管理会话状态、当前频道、动作日志等

**Given** Ant Design ConfigProvider
**When** 查看配置
**Then** 使用蓝色 #1677FF 作为主色调

**Given** 页面首次加载
**When** 计时
**Then** 在 3 秒内完成（NFR3）

### Story 1.7: 消息交互与三频道系统

As a 操作者,
I want 在对话频道输入消息并发送，在三个频道 Tab 之间切换查看不同频道的消息，有新消息的频道显示红点提示,
So that 能发送消息触发 Agent 处理，并观察消息在操作者、下游群、上游群之间的流转。

**Acceptance Criteria:**

**Given** 对话频道
**When** 在输入框输入文字并按回车或点击发送按钮
**Then** 消息以蓝色气泡出现在对话区右侧，并调用 POST /api/chat 发送给后端（FR1, FR2）

**Given** 左侧面板顶部
**When** 查看频道 Tab
**Then** 显示三个 Tab：对话、下游群、上游群

**Given** 用户在"对话"频道
**When** Agent 在上游群发送消息
**Then** "上游群"Tab 出现红点 Badge 提示

**Given** "上游群"Tab 有红点
**When** 用户点击切换到上游群
**Then** 红点消失，显示该频道的消息列表

**Given** 下游群/上游群频道
**When** 查看界面
**Then** 频道为只读，无输入框

**Given** ChatBubble 组件
**When** 渲染用户消息
**Then** 右对齐、蓝色背景(#1677FF)、白色文字

**Given** ChatBubble 组件
**When** 渲染 Agent 消息
**Then** 左对齐、浅灰背景(#F5F5F5)、黑色文字

**Given** 频道有新消息
**When** 消息追加
**Then** 自动滚动到底部

### Story 1.8: 动作日志可视化与端到端联调

As a 操作者,
I want 在右侧面板实时看到 Agent 每一步操作的详情——意图识别、Skill 加载、工具调用——以时间线形式逐步展开，点击可查看输入输出详情,
So that 能完整理解 Agent 的工作过程，亲眼验证"AI 在做事而非回答问题"。

**Acceptance Criteria:**

**Given** 用户发送消息后
**When** 右侧面板更新
**Then** 动作日志以 Timeline 形式从上到下逐条追加 ActionLogItem（FR16）

**Given** ActionLogItem 组件
**When** 动作执行中
**Then** 显示 Spin 旋转动画 + 浅蓝背景(#E6F4FF)

**Given** ActionLogItem 组件
**When** 动作成功完成
**Then** 显示绿色勾号 + 浅绿背景(#F6FFED)，可展开查看详情

**Given** ActionLogItem 组件
**When** 动作失败
**Then** 显示红色叉号 + 浅红背景(#FFF2F0)，自动展开显示错误信息

**Given** ActionLogItem 展开详情
**When** 点击查看
**Then** 显示该步骤的工具名称、输入参数和返回结果（FR17）

**Given** 新 ActionLogItem 追加
**When** 出现新动作
**Then** 带 fadeIn + slideUp 入场动画，面板自动滚动到底部

**Given** usePolling hook
**When** Agent 执行中
**Then** 每 1 秒轮询 GET /api/status/{session_id}?after_index=N 获取增量动作（FR30, NFR2）

**Given** usePolling hook
**When** Agent 状态变为 completed 或 error
**Then** 自动停止轮询

**Given** 完整提前离店流程
**When** 从输入消息到流程完成
**Then** 动作日志依次展示：意图识别(FR18) → Skill 加载 → 查询订单 → 发送上游消息 → 等待上游回复 → 退款登记 → 发送下游回复 → 流程完成（FR19）

**Given** 流程完成
**When** 查看对话频道
**Then** 显示 Agent 最终回复消息（FR3）

## Epic 2: 多场景支持与异常处理

用户可以尝试输入订单取消请求，看到 Agent 走完全不同的流程路径，验证架构通用性；输入无效消息时看到 Agent 友好拒绝并展示已支持场景列表；一键清空会话重新开始演示。

### Story 2.1: 订单取消场景（Skill 2）

As a 操作者,
I want 输入一条订单取消请求后看到 Agent 走完全不同的处理流程,
So that 我能验证系统不是写死的，架构确实支持多场景自动路由。

**Acceptance Criteria:**

**Given** Agent 已支持提前离店场景
**When** 发送消息"请取消订单 HT20260301002"
**Then** Agent 识别意图为"订单取消"，加载 order_cancel Skill（FR13）

**Given** Agent 执行 order_cancel Skill
**When** 执行完成
**Then** 动作日志显示不同于提前离店的步骤序列：意图识别 → Skill 加载 → 提取订单号 → 调用取消工具 → 回复结果（FR14）

**Given** 订单取消工具（agent/tools/order_cancel.py）
**When** 传入有效订单号执行取消
**Then** 返回取消成功结果（FR25）

**Given** 订单取消工具
**When** 传入无效订单号执行取消
**Then** 返回合理的错误信息

**Given** 订单取消执行完成
**When** 查看对话频道
**Then** Agent 回复取消结果（成功或失败）（FR15）

**Given** agent/skills/order_cancel.md
**When** 查看内容
**Then** 包含订单取消场景的自然语言流程描述

**Given** 用户先执行提前离店、再执行订单取消
**When** 对比两次动作日志
**Then** 步骤数量和内容完全不同，验证 Skill 路由机制的通用性

### Story 2.2: 未匹配意图处理与会话重置

As a 操作者,
I want 输入无效消息时看到 Agent 友好拒绝并展示已支持场景，能一键清空会话重新开始演示,
So that 我确信 Agent 不会越界操作，且演示可以随时从头开始。

**Acceptance Criteria:**

**Given** Agent 已配置 Skill 列表
**When** 发送消息"今天天气怎么样"
**Then** Agent 无法匹配任何 Skill，动作日志仅显示 1 条记录（意图识别 → 未匹配）（FR6）

**Given** Agent 未匹配意图
**When** 查看对话频道的 Agent 回复
**Then** 包含"无法处理此请求"友好提示和当前已支持场景列表（提前离店、订单取消）（FR6）

**Given** 未匹配意图处理
**When** 整个流程完成
**Then** 在 2 秒内快速结束，不让用户等待

**Given** 已完成一次演示（有消息和动作日志）
**When** 点击顶部"清空会话"按钮
**Then** 弹出 Popconfirm 确认提示（FR31）

**Given** 确认清空
**When** 清空操作完成
**Then** 对话频道、动作日志、所有群消息全部清空，右侧面板恢复欢迎提示，顶部提示"会话已清空"（FR31）

**Given** 会话已清空
**When** 输入新消息发送
**Then** 可以开始全新一轮演示，所有状态完全重置

## Epic 3: 管理视角与历史记录

用户可以切换到管理页面查看 Skill 列表和工具列表，点开 Skill 阅读自然语言流程描述；查看历史执行记录并回放某次完整流程。

### Story 3.1: 管理视图 — Skill 与工具列表

As a 操作者,
I want 切换到管理页面查看系统中所有的 Skill 和工具，点击 Skill 可以阅读自然语言流程描述,
So that 我能理解系统的幕后配置，确认 Skill 是用自然语言写的、我也看得懂。

**Acceptance Criteria:**

**Given** 操作者在演示视图
**When** 点击顶部导航"管理"
**Then** 页面切换到管理视图（/admin），整个主内容区替换（FR32）

**Given** 管理视图已加载
**When** 查看页面内容
**Then** 显示两个区域：Skill 列表和工具列表

**Given** Skill 列表已加载
**When** 查看列表
**Then** 显示所有已注册的 Skill（提前离店、订单取消），每个包含名称和简要描述（FR27）

**Given** 操作者点击某个 Skill
**When** Drawer 侧拉抽屉打开
**Then** 显示该 Skill 的完整自然语言流程描述内容（FR28）

**Given** 工具列表已加载
**When** 查看列表
**Then** 显示所有已注册的工具（订单查询、消息发送、退款登记、订单取消），每个包含名称、功能说明和参数描述（FR29）

**Given** 管理视图的 Skill 列表和工具列表
**When** 通过 GET /api/skills 和 GET /api/tools 获取数据
**Then** 返回数据格式与架构文档定义一致

**Given** 操作者在管理视图
**When** 点击顶部导航"演示"
**Then** 返回演示视图，之前的会话状态保持不变

### Story 3.2: 历史记录与执行回放

As a 操作者,
I want 查看之前的执行记录列表并能回放某次完整流程,
So that 我可以回顾展示过的内容或向他人复现演示效果。

**Acceptance Criteria:**

**Given** 操作者已完成至少一次演示
**When** 点击顶部导航"历史"
**Then** 页面切换到历史视图（/history），显示执行记录列表（FR34）

**Given** 历史记录列表已加载
**When** 查看列表
**Then** 每条记录显示：触发消息摘要、执行时间、匹配的 Skill 名称、执行状态标签

**Given** 操作者点击某条历史记录
**When** 回放视图展开
**Then** 显示该次执行的完整动作日志（与执行时格式一致，含 ActionLogItem 可展开查看详情）（FR34）

**Given** 尚无历史执行记录
**When** 打开历史视图
**Then** 显示空状态提示"暂无执行记录，完成一次演示后将在此显示"

**Given** 后端 GET /api/history
**When** 请求历史记录列表
**Then** 返回所有已完成执行的摘要列表

**Given** 后端 GET /api/history/{execution_id}
**When** 请求某次执行详情
**Then** 返回该次执行的完整动作日志快照
