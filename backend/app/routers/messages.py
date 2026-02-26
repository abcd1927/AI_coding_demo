"""GET /api/messages/{channel} — 获取指定频道的消息列表。"""

from fastapi import APIRouter, HTTPException

from app.schemas.models import Channel, ChannelMessage
from app.store.memory import store

router = APIRouter(prefix="/api", tags=["messages"])


@router.get("/messages/{channel}", response_model=list[ChannelMessage])
async def get_messages(channel: str) -> list[ChannelMessage]:
    """获取指定频道的消息列表。"""
    try:
        ch = Channel(channel)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="INVALID_CHANNEL",
        )
    return store.get_messages(ch)
