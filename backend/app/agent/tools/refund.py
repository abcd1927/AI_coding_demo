"""退款登记工具 — 模拟退款操作。"""

from app.agent.tools.base import BaseTool
from app.mock.data import MOCK_ORDERS


class RefundTool(BaseTool):
    """模拟退款登记工具（FR24）。"""

    @property
    def name(self) -> str:
        return "refund"

    @property
    def description(self) -> str:
        return "根据订单信息执行退款登记操作"

    def execute(self, **kwargs) -> dict:
        order_id: str = kwargs.get("order_id", "")
        supplier_order_id: str = kwargs.get("supplier_order_id", "")

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
                "message": "订单不存在，无法办理退款",
            }

        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "supplier_order_id": supplier_order_id or order["supplier_order_id"],
                "refund_status": "approved",
                "message": "退款登记成功",
            },
        }

    def _get_parameters(self) -> dict:
        return {
            "order_id": {"type": "string", "description": "订单号"},
            "supplier_order_id": {
                "type": "string",
                "description": "供应商订单号",
            },
        }
