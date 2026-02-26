"""REST API 端点测试 — POST /api/chat, GET /api/status, GET /api/messages。"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.models import (
    ActionStatus,
    ActionType,
    Channel,
    SessionStatus,
)
from app.store.memory import MemoryStore


@pytest.fixture(autouse=True)
def fresh_store(monkeypatch):
    """每个测试使用独立的 MemoryStore 实例。"""
    fresh = MemoryStore()
    monkeypatch.setattr("app.routers.chat.store", fresh)
    monkeypatch.setattr("app.routers.status.store", fresh)
    monkeypatch.setattr("app.routers.messages.store", fresh)
    return fresh


@pytest.fixture
def client():
    """FastAPI TestClient。"""
    return TestClient(app)


# === POST /api/chat 测试 ===


class TestChatEndpoint:
    """POST /api/chat 端点测试。"""

    @patch("app.routers.chat.run_agent", new_callable=AsyncMock)
    def test_send_message_returns_session_id(self, mock_agent, client, fresh_store):
        """正常发送消息返回 session_id。"""
        response = client.post("/api/chat", json={"message": "订单号 HT20260301001 的客人申请提前离店"})
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert isinstance(data["session_id"], str)
        assert len(data["session_id"]) > 0

    @patch("app.routers.chat.run_agent", new_callable=AsyncMock)
    def test_send_message_creates_session(self, mock_agent, client, fresh_store):
        """发送消息后 store 中创建了会话。"""
        response = client.post("/api/chat", json={"message": "测试消息"})
        session_id = response.json()["session_id"]
        session = fresh_store.get_session()
        assert session is not None
        assert session.session_id == session_id

    @patch("app.routers.chat.run_agent", new_callable=AsyncMock)
    def test_send_message_triggers_agent(self, mock_agent, client, fresh_store):
        """发送消息触发 run_agent 后台任务。"""
        response = client.post("/api/chat", json={"message": "测试消息"})
        session_id = response.json()["session_id"]
        mock_agent.assert_called_once_with(session_id, "测试消息")

    def test_send_empty_message_rejected(self, client, fresh_store):
        """空请求体被拒绝。"""
        response = client.post("/api/chat", json={})
        assert response.status_code == 422

    def test_send_empty_string_rejected(self, client, fresh_store):
        """空字符串消息被拒绝。"""
        response = client.post("/api/chat", json={"message": ""})
        assert response.status_code == 422

    def test_send_no_body_rejected(self, client, fresh_store):
        """无请求体被拒绝。"""
        response = client.post("/api/chat")
        assert response.status_code == 422


# === GET /api/status/{session_id} 测试 ===


class TestStatusEndpoint:
    """GET /api/status/{session_id} 端点测试。"""

    def test_status_full_response(self, client, fresh_store):
        """完整模式返回所有 actions。"""
        session = fresh_store.create_session()
        fresh_store.add_action(
            action_type=ActionType.intent_recognition,
            title="意图识别",
            summary="识别为提前离店",
            status=ActionStatus.success,
        )
        fresh_store.add_action(
            action_type=ActionType.tool_call,
            title="查询订单",
            summary="查询 HT20260301001",
            status=ActionStatus.running,
        )

        response = client.get(f"/api/status/{session.session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session.session_id
        assert data["status"] == "idle"
        assert len(data["actions"]) == 2
        assert data["actions"][0]["action_type"] == "intent_recognition"
        assert data["actions"][1]["action_type"] == "tool_call"
        assert data["new_actions"] is None
        assert data["final_reply"] is None

    def test_status_incremental_response(self, client, fresh_store):
        """增量模式只返回 index > after_index 的动作。"""
        session = fresh_store.create_session()
        fresh_store.add_action(
            action_type=ActionType.intent_recognition,
            title="意图识别",
            summary="识别",
            status=ActionStatus.success,
        )
        fresh_store.add_action(
            action_type=ActionType.skill_loaded,
            title="加载 Skill",
            summary="加载",
            status=ActionStatus.success,
        )
        fresh_store.add_action(
            action_type=ActionType.tool_call,
            title="调用工具",
            summary="调用",
            status=ActionStatus.running,
        )

        response = client.get(f"/api/status/{session.session_id}?after_index=1")
        assert response.status_code == 200
        data = response.json()
        assert data["actions"] is None
        assert len(data["new_actions"]) == 1
        assert data["new_actions"][0]["index"] == 2
        assert data["new_actions"][0]["action_type"] == "tool_call"

    def test_status_incremental_no_new_actions(self, client, fresh_store):
        """增量模式无新动作时返回空列表。"""
        session = fresh_store.create_session()
        fresh_store.add_action(
            action_type=ActionType.intent_recognition,
            title="意图识别",
            summary="识别",
            status=ActionStatus.success,
        )

        response = client.get(f"/api/status/{session.session_id}?after_index=5")
        assert response.status_code == 200
        data = response.json()
        assert data["new_actions"] == []

    def test_status_includes_unread_channels(self, client, fresh_store):
        """响应包含 unread_channels。"""
        session = fresh_store.create_session()
        fresh_store.mark_channel_unread("upstream")

        response = client.get(f"/api/status/{session.session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "upstream" in data["unread_channels"]

    def test_status_includes_final_reply(self, client, fresh_store):
        """响应包含 final_reply。"""
        session = fresh_store.create_session()
        fresh_store.set_final_reply("处理完成，退款已登记。")

        response = client.get(f"/api/status/{session.session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["final_reply"] == "处理完成，退款已登记。"

    def test_status_invalid_session_id(self, client, fresh_store):
        """无效 session_id 返回 404。"""
        response = client.get("/api/status/non-existent-id")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["error_type"] == "SESSION_NOT_FOUND"

    def test_status_no_session(self, client, fresh_store):
        """无活跃会话返回 404。"""
        response = client.get("/api/status/any-id")
        assert response.status_code == 404


# === GET /api/messages/{channel} 测试 ===


class TestMessagesEndpoint:
    """GET /api/messages/{channel} 端点测试。"""

    def test_get_chat_messages(self, client, fresh_store):
        """获取对话频道消息。"""
        fresh_store.create_session()
        fresh_store.add_message(Channel.chat, "user", "你好")
        fresh_store.add_message(Channel.chat, "agent", "你好，有什么可以帮您？")

        response = client.get("/api/messages/chat")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["sender"] == "user"
        assert data[0]["content"] == "你好"
        assert data[0]["channel"] == "chat"
        assert data[1]["sender"] == "agent"

    def test_get_downstream_messages(self, client, fresh_store):
        """获取下游群消息。"""
        fresh_store.create_session()
        fresh_store.add_message(Channel.downstream, "agent", "下游消息")

        response = client.get("/api/messages/downstream")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["channel"] == "downstream"

    def test_get_upstream_messages(self, client, fresh_store):
        """获取上游群消息。"""
        fresh_store.create_session()
        fresh_store.add_message(Channel.upstream, "supplier", "上游消息")

        response = client.get("/api/messages/upstream")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["channel"] == "upstream"

    def test_get_messages_empty_channel(self, client, fresh_store):
        """无消息频道返回空列表。"""
        fresh_store.create_session()

        response = client.get("/api/messages/chat")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_messages_invalid_channel(self, client, fresh_store):
        """无效频道返回 400。"""
        response = client.get("/api/messages/invalid_channel")
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
        assert data["error_type"] == "INVALID_CHANNEL"

    def test_messages_filtered_by_channel(self, client, fresh_store):
        """消息按频道正确过滤。"""
        fresh_store.create_session()
        fresh_store.add_message(Channel.chat, "user", "对话消息")
        fresh_store.add_message(Channel.downstream, "agent", "下游消息")
        fresh_store.add_message(Channel.upstream, "supplier", "上游消息")

        response = client.get("/api/messages/chat")
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "对话消息"


# === 统一错误响应格式测试 ===


class TestErrorResponse:
    """统一错误响应格式测试。"""

    def test_404_error_format(self, client, fresh_store):
        """404 错误使用统一格式。"""
        response = client.get("/api/status/non-existent")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert "error_type" in data
        assert "message" in data

    def test_400_error_format(self, client, fresh_store):
        """400 错误使用统一格式。"""
        response = client.get("/api/messages/bad_channel")
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
        assert "error_type" in data
        assert "message" in data

    def test_422_validation_error_format(self, client, fresh_store):
        """422 验证错误使用统一格式。"""
        response = client.post("/api/chat", json={})
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert data["error_type"] == "VALIDATION_ERROR"
        assert "message" in data


# === CORS 测试 ===


class TestCORS:
    """CORS 配置测试。"""

    def test_cors_allows_localhost_5173(self, client, fresh_store):
        """CORS 允许 localhost:5173 来源。"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_cors_blocks_other_origins(self, client, fresh_store):
        """CORS 阻止非允许来源。"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") != "http://evil.com"


# === Health Check 测试 ===


class TestHealthCheck:
    """健康检查端点测试。"""

    def test_health_check(self, client, fresh_store):
        """健康检查返回 ok。"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
