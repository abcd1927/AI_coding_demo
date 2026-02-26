"""GET /api/orders 与 POST /api/orders/reset 路由测试。"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.mock.data import MOCK_ORDERS
from app.routers.orders import router


def _make_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestGetOrders:
    def setup_method(self):
        # 每个测试前重置所有订单状态
        for order in MOCK_ORDERS.values():
            order["status"] = "confirmed"

    def test_get_orders_returns_list(self):
        """GET /api/orders 返回订单列表。"""
        client = _make_client()
        response = client.get("/api/orders")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_get_orders_fields(self):
        """返回的订单包含必需字段。"""
        client = _make_client()
        data = client.get("/api/orders").json()
        order = data[0]
        assert "order_id" in order
        assert "guest_name" in order
        assert "hotel_name" in order
        assert "status" in order

    def test_get_orders_reflects_mutation(self):
        """直接修改 MOCK_ORDERS 后，GET 能反映最新状态。"""
        MOCK_ORDERS["HT20260301001"]["status"] = "cancelled"
        client = _make_client()
        data = client.get("/api/orders").json()
        statuses = {o["order_id"]: o["status"] for o in data}
        assert statuses["HT20260301001"] == "cancelled"
        assert statuses["HT20260301002"] == "confirmed"


class TestResetOrders:
    def setup_method(self):
        for order in MOCK_ORDERS.values():
            order["status"] = "confirmed"

    def test_reset_restores_confirmed(self):
        """POST /api/orders/reset 将所有订单重置为 confirmed。"""
        MOCK_ORDERS["HT20260301001"]["status"] = "cancelled"
        MOCK_ORDERS["HT20260301002"]["status"] = "cancelled"

        client = _make_client()
        response = client.post("/api/orders/reset")
        assert response.status_code == 200
        data = response.json()
        for order in data:
            assert order["status"] == "confirmed"

    def test_reset_returns_list(self):
        """重置后返回完整订单列表。"""
        client = _make_client()
        data = client.post("/api/orders/reset").json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_reset_idempotent(self):
        """连续重置两次结果一致。"""
        client = _make_client()
        client.post("/api/orders/reset")
        data = client.post("/api/orders/reset").json()
        for order in data:
            assert order["status"] == "confirmed"

    def teardown_method(self):
        for order in MOCK_ORDERS.values():
            order["status"] = "confirmed"
