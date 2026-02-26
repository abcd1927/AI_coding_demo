"""上游自动回复模拟 — 模拟供应商自动处理并回复。"""

from app.schemas.models import Channel
from app.store.memory import store


def simulate_upstream_reply(supplier_order_id: str) -> str:
    """模拟上游供应商自动回复（FR22）。

    Args:
        supplier_order_id: 供应商订单号，用于回复内容引用。

    Returns:
        回复消息内容。

    Raises:
        ValueError: 无活跃会话时抛出。
    """
    if not store.get_session():
        raise ValueError("No active session for upstream reply")

    reply_content = f"供应商订单 {supplier_order_id} 已处理完成，可以办理退款"
    store.add_message(
        channel=Channel.upstream,
        sender="supplier",
        content=reply_content,
    )
    store.mark_channel_unread("upstream")
    return reply_content
