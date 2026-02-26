"""订单查询工具 — 根据订单号查询供应商订单号。"""

from app.agent.tools.base import BaseTool
from app.mock.data import MOCK_ORDERS


class OrderQueryTool(BaseTool):
    """模拟订单查询工具（FR23, FR26）。"""

    @property
    def name(self) -> str:
        return "order_query"

    @property
    def description(self) -> str:
        return "根据订单号查询对应的供应商订单号和订单详情"

    def execute(self, **kwargs) -> dict:
        order_id: str = kwargs.get("order_id", "")
        order = MOCK_ORDERS.get(order_id)
        if not order:
            return {
                "error": True,
                "error_type": "ORDER_NOT_FOUND",
                "message": "订单不存在",
            }
        return {
            "success": True,
            "data": {
                "order_id": order["order_id"],
                "supplier_order_id": order["supplier_order_id"],
                "guest_name": order["guest_name"],
                "hotel_name": order["hotel_name"],
                "check_in": order["check_in"],
                "check_out": order["check_out"],
                "room_type": order["room_type"],
            },
        }

    def _get_parameters(self) -> dict:
        return {"order_id": {"type": "string", "description": "订单号"}}
