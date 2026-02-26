"""Core Pydantic data models and enums for AI Agent Demo."""

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


# === Enums ===


class ActionType(str, Enum):
    """动作类型枚举。"""

    intent_recognition = "intent_recognition"
    skill_loaded = "skill_loaded"
    tool_call = "tool_call"
    waiting = "waiting"
    message_sent = "message_sent"
    completed = "completed"


class ActionStatus(str, Enum):
    """动作状态枚举。"""

    running = "running"
    success = "success"
    error = "error"


class SessionStatus(str, Enum):
    """会话状态枚举。"""

    idle = "idle"
    running = "running"
    completed = "completed"
    error = "error"


class Channel(str, Enum):
    """频道标识枚举。"""

    chat = "chat"
    downstream = "downstream"
    upstream = "upstream"


# === Data Models ===


class ActionLogEntry(BaseModel):
    """单步动作记录。"""

    index: int
    action_type: ActionType
    title: str
    summary: str
    status: ActionStatus
    detail: dict | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChannelMessage(BaseModel):
    """频道消息。"""

    channel: Channel
    sender: str
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentExecutionState(BaseModel):
    """Agent 执行状态。"""

    session_id: str
    status: SessionStatus = SessionStatus.idle
    actions: list[ActionLogEntry] = Field(default_factory=list)
    final_reply: str | None = None
    unread_channels: list[str] = Field(default_factory=list)


class SkillDefinition(BaseModel):
    """Skill 定义。"""

    skill_id: str
    name: str
    description: str
    content: str


class ToolDefinition(BaseModel):
    """工具定义。"""

    name: str
    description: str
    parameters: dict


class ExecutionHistory(BaseModel):
    """历史执行记录。"""

    execution_id: str
    trigger_message: str
    skill_name: str | None = None
    status: SessionStatus
    actions: list[ActionLogEntry]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# === API Request/Response Models ===


class ChatRequest(BaseModel):
    """POST /api/chat 请求体。"""

    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    """POST /api/chat 响应体。"""

    session_id: str


class ErrorResponse(BaseModel):
    """统一错误响应格式。"""

    error: bool = True
    error_type: str
    message: str


class StatusResponse(BaseModel):
    """GET /api/status/{session_id} 响应体。支持完整模式和增量模式。"""

    session_id: str
    status: SessionStatus
    new_actions: list[ActionLogEntry] | None = None
    actions: list[ActionLogEntry] | None = None
    unread_channels: list[str]
    final_reply: str | None = None
