"""订单取消工具 — 模拟取消订单操作（FR25）。"""

from app.agent.tools.base import BaseTool
from app.mock.data import MOCK_ORDERS


class OrderCancelTool(BaseTool):
    """模拟订单取消工具（FR14, FR25）。"""

    @property
    def name(self) -> str:
        return "order_cancel"

    @property
    def description(self) -> str:
        return "取消指定订单号的订单"

    def execute(self, **kwargs) -> dict:
        order_id: str = kwargs.get("order_id", "")

        if not order_id:
            return {
                "error": True,
                "error_type": "MISSING_ORDER_ID",
                "message": "缺少订单号",
            }

        order = MOCK_ORDERS.get(order_id)
        if not order:
            return {
                "error": True,
                "error_type": "ORDER_NOT_FOUND",
                "message": "订单不存在",
            }

        if order.get("status") == "cancelled":
            return {
                "error": True,
                "error_type": "ORDER_ALREADY_CANCELLED",
                "message": "订单已取消，无法重复操作",
            }

        # 执行取消（更新模拟数据状态）
        order["status"] = "cancelled"

        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "guest_name": order["guest_name"],
                "hotel_name": order["hotel_name"],
                "cancel_status": "cancelled",
                "message": f"订单 {order_id} 已成功取消",
            },
        }

    def _get_parameters(self) -> dict:
        return {
            "order_id": {
                "type": "string",
                "description": "要取消的订单号",
            },
        }
