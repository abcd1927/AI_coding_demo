"""消息发送工具 — 向指定频道发送消息。"""

from app.agent.tools.base import BaseTool
from app.schemas.models import Channel
from app.store.memory import store


class MessageSendTool(BaseTool):
    """模拟消息发送工具（FR20, FR21）。"""

    @property
    def name(self) -> str:
        return "message_send"

    @property
    def description(self) -> str:
        return "向指定频道（downstream/upstream）发送消息"

    def execute(self, **kwargs) -> dict:
        channel_str: str = kwargs.get("channel", "")
        content: str = kwargs.get("content", "")
        sender: str = kwargs.get("sender", "agent")

        if not content:
            return {
                "error": True,
                "error_type": "EMPTY_CONTENT",
                "message": "消息内容不能为空",
            }

        try:
            channel = Channel(channel_str)
        except ValueError:
            return {
                "error": True,
                "error_type": "INVALID_CHANNEL",
                "message": f"无效的频道标识: {channel_str}",
            }

        store.add_message(channel=channel, sender=sender, content=content)
        store.mark_channel_unread(channel_str)
        return {
            "success": True,
            "data": {"channel": channel_str, "content": content},
        }

    def _get_parameters(self) -> dict:
        return {
            "channel": {
                "type": "string",
                "description": "目标频道（downstream/upstream）",
            },
            "content": {"type": "string", "description": "消息内容"},
            "sender": {
                "type": "string",
                "description": "发送者标识（默认 agent）",
            },
        }
