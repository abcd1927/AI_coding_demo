"""订单数据查看与重置路由。"""

from fastapi import APIRouter

from app.mock.data import MOCK_ORDERS

router = APIRouter(prefix="/api", tags=["orders"])

_INITIAL_STATUS = "confirmed"


@router.get("/orders")
async def get_orders():
    """返回所有订单当前状态。"""
    return list(MOCK_ORDERS.values())


@router.post("/orders/reset")
async def reset_orders():
    """将所有订单状态重置为 confirmed，返回重置后的列表。"""
    for order in MOCK_ORDERS.values():
        order["status"] = _INITIAL_STATUS
    return list(MOCK_ORDERS.values())
