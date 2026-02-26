"""Tests for MemoryStore in-memory storage."""

import pytest

from app.schemas.models import (
    ActionStatus,
    ActionType,
    Channel,
    SessionStatus,
)
from app.store.memory import MemoryStore


class TestSessionManagement:
    def test_create_session(self):
        store = MemoryStore()
        session = store.create_session()
        assert session.session_id
        assert session.status == SessionStatus.idle
        assert session.actions == []
        assert session.final_reply is None
        assert session.unread_channels == []

    def test_create_session_clears_old_messages(self):
        """H1 fix: create_session must clear messages from previous session."""
        store = MemoryStore()
        store.create_session()
        store.add_message(Channel.chat, "user", "old message")
        assert len(store.get_messages(Channel.chat)) == 1

        store.create_session()  # new session without clear_session
        assert store.get_messages(Channel.chat) == []

    def test_get_session(self):
        store = MemoryStore()
        store.create_session()
        session = store.get_session()
        assert session is not None

    def test_get_session_none_when_empty(self):
        store = MemoryStore()
        assert store.get_session() is None

    def test_update_session_status(self):
        store = MemoryStore()
        store.create_session()
        store.update_session_status(SessionStatus.running)
        session = store.get_session()
        assert session.status == SessionStatus.running

    def test_update_session_status_no_session_raises(self):
        """M2 fix: should raise ValueError when no session."""
        store = MemoryStore()
        with pytest.raises(ValueError, match="No active session"):
            store.update_session_status(SessionStatus.running)

    def test_set_final_reply(self):
        store = MemoryStore()
        store.create_session()
        store.set_final_reply("处理完成，退款成功")
        session = store.get_session()
        assert session.final_reply == "处理完成，退款成功"

    def test_set_final_reply_no_session_raises(self):
        """M2 fix: should raise ValueError when no session."""
        store = MemoryStore()
        with pytest.raises(ValueError, match="No active session"):
            store.set_final_reply("test")


class TestActionLogManagement:
    def test_add_action_auto_index(self):
        store = MemoryStore()
        store.create_session()
        action = store.add_action(
            action_type=ActionType.intent_recognition,
            title="意图识别",
            summary="识别为提前离店",
            status=ActionStatus.running,
        )
        assert action.index == 0

    def test_add_action_no_session_raises(self):
        """M2 fix: should raise ValueError when no session."""
        store = MemoryStore()
        with pytest.raises(ValueError, match="No active session"):
            store.add_action(ActionType.intent_recognition, "a", "b", ActionStatus.running)

    def test_add_multiple_actions_incremental_index(self):
        store = MemoryStore()
        store.create_session()
        a1 = store.add_action(
            action_type=ActionType.intent_recognition,
            title="意图识别",
            summary="识别意图",
            status=ActionStatus.success,
        )
        a2 = store.add_action(
            action_type=ActionType.tool_call,
            title="查询订单",
            summary="查询中",
            status=ActionStatus.running,
        )
        assert a1.index == 0
        assert a2.index == 1

    def test_add_action_with_detail(self):
        store = MemoryStore()
        store.create_session()
        detail = {"input": {"order_id": "HT001"}, "output": {"supplier_id": "SUP-001"}}
        action = store.add_action(
            action_type=ActionType.tool_call,
            title="查询订单",
            summary="查询订单号 HT001",
            status=ActionStatus.success,
            detail=detail,
        )
        assert action.detail == detail

    def test_update_action_status(self):
        store = MemoryStore()
        store.create_session()
        store.add_action(
            action_type=ActionType.tool_call,
            title="查询订单",
            summary="查询中",
            status=ActionStatus.running,
        )
        store.update_action_status(0, ActionStatus.success, detail={"result": "ok"})
        actions = store.get_actions()
        assert actions[0].status == ActionStatus.success
        assert actions[0].detail == {"result": "ok"}

    def test_update_action_status_no_session_raises(self):
        """M2 fix: should raise ValueError when no session."""
        store = MemoryStore()
        with pytest.raises(ValueError, match="No active session"):
            store.update_action_status(0, ActionStatus.success)

    def test_update_action_status_invalid_index_raises(self):
        """M2 fix: should raise ValueError for non-existent index."""
        store = MemoryStore()
        store.create_session()
        with pytest.raises(ValueError, match="not found"):
            store.update_action_status(99, ActionStatus.success)

    def test_get_actions_all(self):
        store = MemoryStore()
        store.create_session()
        store.add_action(ActionType.intent_recognition, "a", "b", ActionStatus.success)
        store.add_action(ActionType.tool_call, "c", "d", ActionStatus.success)
        actions = store.get_actions()
        assert len(actions) == 2

    def test_get_actions_incremental(self):
        store = MemoryStore()
        store.create_session()
        store.add_action(ActionType.intent_recognition, "a", "b", ActionStatus.success)
        store.add_action(ActionType.skill_loaded, "c", "d", ActionStatus.success)
        store.add_action(ActionType.tool_call, "e", "f", ActionStatus.running)

        # after_index=0 should return index 1 and 2
        actions = store.get_actions(after_index=0)
        assert len(actions) == 2
        assert actions[0].index == 1
        assert actions[1].index == 2

    def test_get_actions_incremental_none_new(self):
        store = MemoryStore()
        store.create_session()
        store.add_action(ActionType.intent_recognition, "a", "b", ActionStatus.success)
        actions = store.get_actions(after_index=0)
        assert len(actions) == 0

    def test_get_actions_incremental_after_minus_one(self):
        store = MemoryStore()
        store.create_session()
        store.add_action(ActionType.intent_recognition, "a", "b", ActionStatus.success)
        actions = store.get_actions(after_index=-1)
        assert len(actions) == 1


class TestMessageManagement:
    def test_add_message(self):
        store = MemoryStore()
        store.create_session()
        msg = store.add_message(
            channel=Channel.chat,
            sender="user",
            content="订单号 HT001 提前离店",
        )
        assert msg.channel == Channel.chat
        assert msg.sender == "user"

    def test_get_messages_by_channel(self):
        store = MemoryStore()
        store.create_session()
        store.add_message(Channel.chat, "user", "hello")
        store.add_message(Channel.upstream, "agent", "SUP-001")
        store.add_message(Channel.chat, "agent", "已收到")

        chat_msgs = store.get_messages(Channel.chat)
        assert len(chat_msgs) == 2

        upstream_msgs = store.get_messages(Channel.upstream)
        assert len(upstream_msgs) == 1

        downstream_msgs = store.get_messages(Channel.downstream)
        assert len(downstream_msgs) == 0


class TestUnreadChannels:
    def test_mark_channel_unread(self):
        store = MemoryStore()
        store.create_session()
        store.mark_channel_unread("upstream")
        session = store.get_session()
        assert "upstream" in session.unread_channels

    def test_mark_channel_unread_no_duplicate(self):
        store = MemoryStore()
        store.create_session()
        store.mark_channel_unread("upstream")
        store.mark_channel_unread("upstream")
        session = store.get_session()
        assert session.unread_channels.count("upstream") == 1

    def test_clear_channel_unread(self):
        store = MemoryStore()
        store.create_session()
        store.mark_channel_unread("upstream")
        store.mark_channel_unread("downstream")
        store.clear_channel_unread("upstream")
        session = store.get_session()
        assert "upstream" not in session.unread_channels
        assert "downstream" in session.unread_channels


class TestHistoryManagement:
    def test_save_execution_history(self):
        store = MemoryStore()
        store.create_session()
        store.add_action(ActionType.intent_recognition, "意图识别", "识别", ActionStatus.success)
        store.update_session_status(SessionStatus.completed)
        history = store.save_execution_history("订单号 HT001 提前离店")
        assert history.execution_id
        assert history.trigger_message == "订单号 HT001 提前离店"
        assert len(history.actions) == 1

    def test_save_history_with_explicit_skill_name(self):
        """M3 fix: skill_name should be provided by caller."""
        store = MemoryStore()
        store.create_session()
        store.update_session_status(SessionStatus.completed)
        history = store.save_execution_history("test", skill_name="提前离店")
        assert history.skill_name == "提前离店"

    def test_save_history_without_skill_name(self):
        """M3 fix: skill_name defaults to None when not provided."""
        store = MemoryStore()
        store.create_session()
        store.update_session_status(SessionStatus.completed)
        history = store.save_execution_history("test")
        assert history.skill_name is None

    def test_save_history_is_snapshot(self):
        """History actions should be a deep copy, not affected by later changes."""
        store = MemoryStore()
        store.create_session()
        store.add_action(ActionType.intent_recognition, "a", "b", ActionStatus.success)
        store.save_execution_history("test")
        # Add more actions after saving history
        store.add_action(ActionType.tool_call, "c", "d", ActionStatus.success)
        history_list = store.get_history_list()
        assert len(history_list[0].actions) == 1  # snapshot should still have 1

    def test_get_history_list(self):
        store = MemoryStore()
        store.create_session()
        store.update_session_status(SessionStatus.completed)
        store.save_execution_history("msg1")

        store.clear_session()
        store.create_session()
        store.update_session_status(SessionStatus.completed)
        store.save_execution_history("msg2")

        history_list = store.get_history_list()
        assert len(history_list) == 2

    def test_get_history_detail(self):
        store = MemoryStore()
        store.create_session()
        store.update_session_status(SessionStatus.completed)
        saved = store.save_execution_history("test msg")

        detail = store.get_history_detail(saved.execution_id)
        assert detail is not None
        assert detail.trigger_message == "test msg"

    def test_get_history_detail_not_found(self):
        store = MemoryStore()
        assert store.get_history_detail("nonexistent") is None


class TestClearSession:
    def test_clear_session_resets_state(self):
        store = MemoryStore()
        store.create_session()
        store.add_action(ActionType.intent_recognition, "a", "b", ActionStatus.success)
        store.add_message(Channel.chat, "user", "hello")
        store.mark_channel_unread("upstream")
        store.update_session_status(SessionStatus.completed)
        store.save_execution_history("test")

        store.clear_session()

        assert store.get_session() is None
        assert store.get_messages(Channel.chat) == []
        # History should be preserved
        assert len(store.get_history_list()) == 1

    def test_clear_session_resets_action_counter(self):
        store = MemoryStore()
        store.create_session()
        store.add_action(ActionType.intent_recognition, "a", "b", ActionStatus.success)
        store.add_action(ActionType.tool_call, "c", "d", ActionStatus.success)

        store.clear_session()
        store.create_session()
        action = store.add_action(ActionType.intent_recognition, "e", "f", ActionStatus.running)
        assert action.index == 0  # Counter should reset

    def test_clear_session_idempotent(self):
        """无活跃会话时清空不报错（幂等 — AC #8）。"""
        store = MemoryStore()
        # 没有创建会话直接清空
        store.clear_session()  # 不抛异常
        assert store.get_session() is None
        assert store.get_messages(Channel.chat) == []

    def test_clear_session_double_clear(self):
        """连续两次清空不报错（幂等）。"""
        store = MemoryStore()
        store.create_session()
        store.add_message(Channel.chat, "user", "hello")
        store.clear_session()
        store.clear_session()  # 第二次清空不抛异常
        assert store.get_session() is None

    def test_clear_session_preserves_history(self):
        """清空会话后历史记录完整保留（AC #8 相关）。"""
        store = MemoryStore()
        # 第一次会话
        store.create_session()
        store.add_action(ActionType.intent_recognition, "a", "b", ActionStatus.success)
        store.update_session_status(SessionStatus.completed)
        store.save_execution_history("msg1", skill_name="提前离店")
        store.clear_session()
        # 第二次会话
        store.create_session()
        store.add_action(ActionType.intent_recognition, "c", "d", ActionStatus.success)
        store.update_session_status(SessionStatus.completed)
        store.save_execution_history("msg2", skill_name="订单取消")
        store.clear_session()
        # 验证两条历史都保留
        history = store.get_history_list()
        assert len(history) == 2
        assert history[0].trigger_message == "msg1"
        assert history[0].skill_name == "提前离店"
        assert history[1].trigger_message == "msg2"
        assert history[1].skill_name == "订单取消"

    def test_clear_then_new_session(self):
        """清空后可以创建全新会话（AC #6）。"""
        store = MemoryStore()
        store.create_session()
        old_id = store.get_session().session_id
        store.add_message(Channel.chat, "user", "old msg")
        store.clear_session()
        # 创建新会话
        store.create_session()
        new_session = store.get_session()
        assert new_session is not None
        assert new_session.session_id != old_id
        assert new_session.status == SessionStatus.idle
        assert new_session.actions == []
        assert store.get_messages(Channel.chat) == []
