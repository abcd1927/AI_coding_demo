"""GET /api/status/{session_id} — 轮询获取 Agent 执行状态。"""

from fastapi import APIRouter, HTTPException

from app.schemas.models import StatusResponse
from app.store.memory import store

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status/{session_id}", response_model=StatusResponse)
async def get_status(
    session_id: str,
    after_index: int | None = None,
) -> StatusResponse:
    """获取 Agent 执行状态。支持完整模式和增量模式。"""
    session = store.get_session()
    if not session or session.session_id != session_id:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")

    if after_index is not None:
        # 增量模式：只返回 index > after_index 的新动作
        new_actions = store.get_actions(after_index=after_index)
        return StatusResponse(
            session_id=session.session_id,
            status=session.status,
            new_actions=new_actions,
            unread_channels=session.unread_channels,
            final_reply=session.final_reply,
        )

    # 完整模式：返回所有 actions
    return StatusResponse(
        session_id=session.session_id,
        status=session.status,
        actions=session.actions,
        unread_channels=session.unread_channels,
        final_reply=session.final_reply,
    )
