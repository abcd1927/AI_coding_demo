"""POST /api/chat — 发送消息触发 Agent 处理。"""

from fastapi import APIRouter, BackgroundTasks

from app.agent.engine import run_agent
from app.schemas.models import ChatRequest, ChatResponse
from app.store.memory import store

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
) -> ChatResponse:
    """接收用户消息，创建会话并在后台启动 Agent 处理。"""
    session = store.create_session()
    background_tasks.add_task(run_agent, session.session_id, request.message)
    return ChatResponse(session_id=session.session_id)
