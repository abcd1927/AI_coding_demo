"""DELETE /api/session — 清空当前会话。"""

from fastapi import APIRouter

from app.store.memory import store

router = APIRouter(prefix="/api", tags=["session"])


@router.delete("/session")
async def delete_session():
    """清空当前会话，保留历史记录（FR31）。"""
    store.clear_session()
    return {"message": "会话已清空"}
