"""In-memory state management for sessions, messages, and history."""

import copy
import uuid

from app.schemas.models import (
    ActionLogEntry,
    ActionStatus,
    ActionType,
    AgentExecutionState,
    Channel,
    ChannelMessage,
    ExecutionHistory,
    SessionStatus,
)


class MemoryStore:
    """单例内存存储，管理会话状态、消息、历史记录。"""

    def __init__(self):
        self._session: AgentExecutionState | None = None
        self._messages: list[ChannelMessage] = []
        self._history: list[ExecutionHistory] = []
        self._action_counter: int = 0

    # === 会话管理 ===

    def create_session(self) -> AgentExecutionState:
        """创建新会话，返回初始状态。同时清除旧消息和计数器。"""
        self._session = AgentExecutionState(session_id=str(uuid.uuid4()))
        self._messages = []
        self._action_counter = 0
        return self._session

    def get_session(self) -> AgentExecutionState | None:
        """获取当前会话状态。"""
        return self._session

    def update_session_status(self, status: SessionStatus) -> None:
        """更新会话状态。无活跃会话时抛出 ValueError。"""
        if not self._session:
            raise ValueError("No active session")
        self._session.status = status

    def set_final_reply(self, reply: str) -> None:
        """设置 Agent 最终回复。无活跃会话时抛出 ValueError。"""
        if not self._session:
            raise ValueError("No active session")
        self._session.final_reply = reply

    # === 动作日志 ===

    def add_action(
        self,
        action_type: ActionType,
        title: str,
        summary: str,
        status: ActionStatus,
        detail: dict | None = None,
    ) -> ActionLogEntry:
        """追加一条动作记录，自动分配递增 index。无活跃会话时抛出 ValueError。"""
        if not self._session:
            raise ValueError("No active session")
        action = ActionLogEntry(
            index=self._action_counter,
            action_type=action_type,
            title=title,
            summary=summary,
            status=status,
            detail=detail,
        )
        self._action_counter += 1
        self._session.actions.append(action)
        return action

    def update_action_status(
        self,
        index: int,
        status: ActionStatus,
        detail: dict | None = None,
        summary: str | None = None,
    ) -> None:
        """更新指定 index 的动作状态、详情和摘要。"""
        if not self._session:
            raise ValueError("No active session")
        for action in self._session.actions:
            if action.index == index:
                action.status = status
                if detail is not None:
                    action.detail = detail
                if summary is not None:
                    action.summary = summary
                return
        raise ValueError(f"Action with index {index} not found")

    def get_actions(self, after_index: int = -1) -> list[ActionLogEntry]:
        """获取动作日志，支持增量查询。after_index=-1 返回全部。"""
        if not self._session:
            return []
        return [a for a in self._session.actions if a.index > after_index]

    # === 消息管理 ===

    def add_message(
        self,
        channel: Channel,
        sender: str,
        content: str,
    ) -> ChannelMessage:
        """添加一条频道消息。"""
        msg = ChannelMessage(channel=channel, sender=sender, content=content)
        self._messages.append(msg)
        return msg

    def get_messages(self, channel: Channel) -> list[ChannelMessage]:
        """按频道查询消息列表。"""
        return [m for m in self._messages if m.channel == channel]

    # === 未读频道 ===

    def mark_channel_unread(self, channel: str) -> None:
        """标记频道有未读消息。"""
        if self._session and channel not in self._session.unread_channels:
            self._session.unread_channels.append(channel)

    def clear_channel_unread(self, channel: str) -> None:
        """清除频道未读标记。"""
        if self._session and channel in self._session.unread_channels:
            self._session.unread_channels.remove(channel)

    # === 历史记录 ===

    def save_execution_history(
        self,
        trigger_message: str,
        skill_name: str | None = None,
    ) -> ExecutionHistory:
        """保存当前执行为历史记录（深拷贝 actions 快照）。"""
        actions_snapshot = copy.deepcopy(self._session.actions) if self._session else []

        history = ExecutionHistory(
            execution_id=str(uuid.uuid4()),
            trigger_message=trigger_message,
            skill_name=skill_name,
            status=self._session.status if self._session else SessionStatus.error,
            actions=actions_snapshot,
        )
        self._history.append(history)
        return history

    def get_history_list(self) -> list[ExecutionHistory]:
        """获取所有历史执行记录。"""
        return self._history

    def get_history_detail(self, execution_id: str) -> ExecutionHistory | None:
        """根据 execution_id 获取某次执行详情。"""
        for h in self._history:
            if h.execution_id == execution_id:
                return h
        return None

    # === 会话重置 ===

    def clear_session(self) -> None:
        """清空当前会话（保留历史记录）。"""
        self._session = None
        self._messages = []
        self._action_counter = 0


# 模块级单例实例
store = MemoryStore()
