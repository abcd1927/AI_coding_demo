"""DELETE /api/session 路由测试。"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.session import router
from app.schemas.models import Channel
from app.store.memory import MemoryStore


def _make_app(test_store: MemoryStore):
    """创建一个仅包含 session router 的测试 App，避免导入 engine.py。"""
    import app.routers.session as session_mod

    original = session_mod.store
    session_mod.store = test_store

    test_app = FastAPI()
    test_app.include_router(router)

    # 返回 app 和 cleanup 函数
    return test_app, lambda: setattr(session_mod, "store", original)


class TestDeleteSessionRouter:
    def test_delete_session_success(self):
        """有活跃会话时清空成功（AC #5）。"""
        store = MemoryStore()
        store.create_session()
        store.add_message(
            channel=Channel.chat, sender="user", content="hello"
        )
        app, cleanup = _make_app(store)
        try:
            client = TestClient(app)
            response = client.delete("/api/session")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "会话已清空"
            # 验证 store 已清空
            assert store.get_session() is None
            assert store.get_messages(Channel.chat) == []
        finally:
            cleanup()

    def test_delete_session_idempotent(self):
        """无活跃会话时清空也返回成功（AC #8 幂等）。"""
        store = MemoryStore()
        # 没有创建会话
        app, cleanup = _make_app(store)
        try:
            client = TestClient(app)
            response = client.delete("/api/session")
            assert response.status_code == 200
            assert response.json()["message"] == "会话已清空"
        finally:
            cleanup()

    def test_delete_session_preserves_history(self):
        """清空会话后历史记录保留。"""
        from app.schemas.models import ActionStatus, ActionType, SessionStatus

        store = MemoryStore()
        store.create_session()
        store.add_action(
            ActionType.intent_recognition, "a", "b", ActionStatus.success
        )
        store.update_session_status(SessionStatus.completed)
        store.save_execution_history("test msg")

        app, cleanup = _make_app(store)
        try:
            client = TestClient(app)
            response = client.delete("/api/session")
            assert response.status_code == 200
            # 历史保留
            assert len(store.get_history_list()) == 1
            assert store.get_history_list()[0].trigger_message == "test msg"
        finally:
            cleanup()

    def test_delete_session_double_call(self):
        """连续调用两次 DELETE 都成功。"""
        store = MemoryStore()
        store.create_session()
        app, cleanup = _make_app(store)
        try:
            client = TestClient(app)
            r1 = client.delete("/api/session")
            r2 = client.delete("/api/session")
            assert r1.status_code == 200
            assert r2.status_code == 200
        finally:
            cleanup()
