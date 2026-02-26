"""Tests for Pydantic data models and enums."""

from datetime import UTC, datetime

from app.schemas.models import (
    ActionLogEntry,
    ActionStatus,
    ActionType,
    AgentExecutionState,
    Channel,
    ChannelMessage,
    ExecutionHistory,
    SessionStatus,
    SkillDefinition,
    ToolDefinition,
)


# === Task 1: Enum Tests ===


class TestActionType:
    def test_all_values_exist(self):
        assert ActionType.intent_recognition == "intent_recognition"
        assert ActionType.skill_loaded == "skill_loaded"
        assert ActionType.tool_call == "tool_call"
        assert ActionType.waiting == "waiting"
        assert ActionType.message_sent == "message_sent"
        assert ActionType.completed == "completed"

    def test_has_exactly_six_values(self):
        assert len(ActionType) == 6


class TestActionStatus:
    def test_all_values_exist(self):
        assert ActionStatus.running == "running"
        assert ActionStatus.success == "success"
        assert ActionStatus.error == "error"

    def test_has_exactly_three_values(self):
        assert len(ActionStatus) == 3


class TestSessionStatus:
    def test_all_values_exist(self):
        assert SessionStatus.idle == "idle"
        assert SessionStatus.running == "running"
        assert SessionStatus.completed == "completed"
        assert SessionStatus.error == "error"

    def test_has_exactly_four_values(self):
        assert len(SessionStatus) == 4


class TestChannel:
    def test_all_values_exist(self):
        assert Channel.chat == "chat"
        assert Channel.downstream == "downstream"
        assert Channel.upstream == "upstream"

    def test_has_exactly_three_values(self):
        assert len(Channel) == 3


# === Task 2: Model Tests ===


class TestActionLogEntry:
    def test_create_with_required_fields(self):
        entry = ActionLogEntry(
            index=0,
            action_type=ActionType.intent_recognition,
            title="意图识别",
            summary="识别为提前离店",
            status=ActionStatus.running,
        )
        assert entry.index == 0
        assert entry.action_type == ActionType.intent_recognition
        assert entry.title == "意图识别"
        assert entry.summary == "识别为提前离店"
        assert entry.status == ActionStatus.running
        assert entry.detail is None
        assert isinstance(entry.timestamp, datetime)

    def test_timestamp_is_utc(self):
        """M1 fix: timestamps must be UTC per architecture spec."""
        entry = ActionLogEntry(
            index=0,
            action_type=ActionType.intent_recognition,
            title="t",
            summary="s",
            status=ActionStatus.running,
        )
        assert entry.timestamp.tzinfo is UTC

    def test_create_with_detail(self):
        detail = {"input": {"order_id": "HT001"}, "output": {"supplier_id": "SUP-001"}}
        entry = ActionLogEntry(
            index=1,
            action_type=ActionType.tool_call,
            title="查询订单",
            summary="查询订单号 HT001",
            status=ActionStatus.success,
            detail=detail,
        )
        assert entry.detail == detail

    def test_serialization_snake_case(self):
        entry = ActionLogEntry(
            index=0,
            action_type=ActionType.tool_call,
            title="test",
            summary="test",
            status=ActionStatus.success,
        )
        data = entry.model_dump()
        assert "action_type" in data
        assert data["action_type"] == "tool_call"
        assert data["status"] == "success"


class TestChannelMessage:
    def test_create_message(self):
        msg = ChannelMessage(
            channel=Channel.chat,
            sender="user",
            content="订单号 HT20260301001 的客人申请提前离店",
        )
        assert msg.channel == Channel.chat
        assert msg.sender == "user"
        assert msg.content == "订单号 HT20260301001 的客人申请提前离店"
        assert isinstance(msg.timestamp, datetime)

    def test_serialization(self):
        msg = ChannelMessage(
            channel=Channel.downstream,
            sender="agent",
            content="处理完成",
        )
        data = msg.model_dump()
        assert data["channel"] == "downstream"
        assert data["sender"] == "agent"


class TestAgentExecutionState:
    def test_create_default(self):
        state = AgentExecutionState(session_id="test-session-1")
        assert state.session_id == "test-session-1"
        assert state.status == SessionStatus.idle
        assert state.actions == []
        assert state.final_reply is None
        assert state.unread_channels == []

    def test_create_with_actions(self):
        action = ActionLogEntry(
            index=0,
            action_type=ActionType.intent_recognition,
            title="意图识别",
            summary="识别意图",
            status=ActionStatus.success,
        )
        state = AgentExecutionState(
            session_id="test-session-2",
            status=SessionStatus.running,
            actions=[action],
            unread_channels=["upstream"],
        )
        assert len(state.actions) == 1
        assert state.unread_channels == ["upstream"]

    def test_serialization(self):
        state = AgentExecutionState(session_id="s1")
        data = state.model_dump()
        assert data["session_id"] == "s1"
        assert data["status"] == "idle"
        assert data["actions"] == []
        assert data["final_reply"] is None


class TestSkillDefinition:
    def test_create(self):
        skill = SkillDefinition(
            skill_id="early_checkout",
            name="提前离店",
            description="处理提前离店请求",
            content="# 提前离店流程\n1. 查询订单\n2. 通知上游",
        )
        assert skill.skill_id == "early_checkout"
        assert skill.name == "提前离店"
        assert skill.content.startswith("# 提前离店流程")


class TestToolDefinition:
    def test_create(self):
        tool = ToolDefinition(
            name="order_query",
            description="查询订单信息",
            parameters={"order_id": {"type": "string", "description": "订单号"}},
        )
        assert tool.name == "order_query"
        assert "order_id" in tool.parameters


class TestExecutionHistory:
    def test_create(self):
        action = ActionLogEntry(
            index=0,
            action_type=ActionType.completed,
            title="完成",
            summary="流程完成",
            status=ActionStatus.success,
        )
        history = ExecutionHistory(
            execution_id="exec-1",
            trigger_message="订单号 HT001 提前离店",
            skill_name="提前离店",
            status=SessionStatus.completed,
            actions=[action],
        )
        assert history.execution_id == "exec-1"
        assert history.trigger_message == "订单号 HT001 提前离店"
        assert history.skill_name == "提前离店"
        assert len(history.actions) == 1
        assert isinstance(history.created_at, datetime)

    def test_create_without_skill(self):
        history = ExecutionHistory(
            execution_id="exec-2",
            trigger_message="今天天气怎么样",
            status=SessionStatus.completed,
            actions=[],
        )
        assert history.skill_name is None
