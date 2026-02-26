"""工具和模拟层单元测试。"""

import pytest

from app.agent.tools.base import BaseTool
from app.mock.data import MOCK_ORDERS
from app.mock.upstream import simulate_upstream_reply
from app.schemas.models import Channel, ToolDefinition
from app.store.memory import MemoryStore


# === Fixtures ===


@pytest.fixture()
def fresh_store(monkeypatch):
    """提供一个全新的 MemoryStore 实例并替换全局 store。"""
    new_store = MemoryStore()
    new_store.create_session()
    # Patch store in modules that import it
    monkeypatch.setattr("app.agent.tools.message_send.store", new_store)
    monkeypatch.setattr("app.mock.upstream.store", new_store)
    return new_store


# === Task 1: BaseTool 抽象基类 ===


class TestBaseTool:
    def test_cannot_instantiate_abstract(self):
        """BaseTool 不可直接实例化。"""
        with pytest.raises(TypeError):
            BaseTool()

    def test_concrete_subclass_requires_all_methods(self):
        """缺少抽象方法的子类不可实例化。"""

        class IncompleteTool(BaseTool):
            @property
            def name(self) -> str:
                return "incomplete"

        with pytest.raises(TypeError):
            IncompleteTool()

    def test_concrete_subclass_can_instantiate(self):
        """实现所有抽象方法的子类可正常实例化。"""

        class DummyTool(BaseTool):
            @property
            def name(self) -> str:
                return "dummy"

            @property
            def description(self) -> str:
                return "A dummy tool"

            def execute(self, **kwargs) -> dict:
                return {"success": True, "data": {}}

            def _get_parameters(self) -> dict:
                return {}

        tool = DummyTool()
        assert tool.name == "dummy"
        assert tool.description == "A dummy tool"

    def test_get_definition_returns_tool_definition(self):
        """get_definition 返回 ToolDefinition 实例。"""

        class DummyTool(BaseTool):
            @property
            def name(self) -> str:
                return "dummy_def"

            @property
            def description(self) -> str:
                return "Dummy for definition test"

            def execute(self, **kwargs) -> dict:
                return {}

            def _get_parameters(self) -> dict:
                return {"param1": {"type": "string", "description": "test"}}

        tool = DummyTool()
        definition = tool.get_definition()
        assert isinstance(definition, ToolDefinition)
        assert definition.name == "dummy_def"
        assert definition.description == "Dummy for definition test"
        assert "param1" in definition.parameters


# === Task 2: 模拟数据 ===


class TestMockData:
    def test_has_at_least_3_orders(self):
        """模拟数据包含至少 3 条订单记录。"""
        assert len(MOCK_ORDERS) >= 3

    def test_required_order_mapping(self):
        """HT20260301001 映射到 SUP-88901。"""
        order = MOCK_ORDERS["HT20260301001"]
        assert order["supplier_order_id"] == "SUP-88901"

    def test_order_has_required_fields(self):
        """每条订单包含必要字段。"""
        required_fields = {
            "order_id",
            "supplier_order_id",
            "guest_name",
            "hotel_name",
            "check_in",
            "check_out",
            "room_type",
            "status",
        }
        for order_id, order in MOCK_ORDERS.items():
            assert required_fields.issubset(order.keys()), (
                f"Order {order_id} missing fields"
            )

    def test_order_ids_consistent(self):
        """字典 key 与 order_id 字段一致。"""
        for key, order in MOCK_ORDERS.items():
            assert key == order["order_id"]


# === Task 3: 订单查询工具 ===


class TestOrderQueryTool:
    def _make_tool(self):
        from app.agent.tools.order_query import OrderQueryTool

        return OrderQueryTool()

    def test_name(self):
        tool = self._make_tool()
        assert tool.name == "order_query"

    def test_valid_order_returns_supplier_id(self):
        """有效订单号返回正确的供应商订单号（AC #2）。"""
        tool = self._make_tool()
        result = tool.execute(order_id="HT20260301001")
        assert result["success"] is True
        assert result["data"]["supplier_order_id"] == "SUP-88901"

    def test_valid_order_returns_guest_info(self):
        """有效订单返回客户信息。"""
        tool = self._make_tool()
        result = tool.execute(order_id="HT20260301001")
        assert result["data"]["guest_name"] == "张三"
        assert result["data"]["hotel_name"] == "杭州西湖大酒店"

    def test_valid_order_returns_dates(self):
        """有效订单返回入住/退房日期。"""
        tool = self._make_tool()
        result = tool.execute(order_id="HT20260301001")
        assert result["data"]["check_in"] == "2026-03-01"
        assert result["data"]["check_out"] == "2026-03-05"
        assert result["data"]["room_type"] == "大床房"

    def test_invalid_order_returns_error(self):
        """无效订单号返回错误信息（AC #3）。"""
        tool = self._make_tool()
        result = tool.execute(order_id="INVALID-ID")
        assert result["error"] is True
        assert result["error_type"] == "ORDER_NOT_FOUND"
        assert result["message"] == "订单不存在"

    def test_empty_order_id_returns_error(self):
        """空订单号返回错误信息。"""
        tool = self._make_tool()
        result = tool.execute(order_id="")
        assert result["error"] is True

    def test_no_order_id_returns_error(self):
        """未传 order_id 参数返回错误信息。"""
        tool = self._make_tool()
        result = tool.execute()
        assert result["error"] is True

    def test_all_mock_orders_queryable(self):
        """所有模拟订单都可查询。"""
        tool = self._make_tool()
        for order_id in MOCK_ORDERS:
            result = tool.execute(order_id=order_id)
            assert result["success"] is True


# === Task 4: 消息发送工具 ===


class TestMessageSendTool:
    def _make_tool(self):
        from app.agent.tools.message_send import MessageSendTool

        return MessageSendTool()

    def test_name(self):
        tool = self._make_tool()
        assert tool.name == "message_send"

    def test_send_to_downstream(self, fresh_store):
        """消息写入 downstream 频道（AC #4）。"""
        tool = self._make_tool()
        result = tool.execute(channel="downstream", content="测试消息")
        assert result["success"] is True
        messages = fresh_store.get_messages(Channel.downstream)
        assert len(messages) == 1
        assert messages[0].content == "测试消息"
        assert messages[0].sender == "agent"

    def test_send_to_upstream(self, fresh_store):
        """消息写入 upstream 频道。"""
        tool = self._make_tool()
        result = tool.execute(channel="upstream", content="上游消息")
        assert result["success"] is True
        messages = fresh_store.get_messages(Channel.upstream)
        assert len(messages) == 1
        assert messages[0].content == "上游消息"

    def test_marks_channel_unread(self, fresh_store):
        """发送消息后标记频道未读。"""
        tool = self._make_tool()
        tool.execute(channel="downstream", content="test")
        assert "downstream" in fresh_store.get_session().unread_channels

    def test_custom_sender(self, fresh_store):
        """支持自定义 sender。"""
        tool = self._make_tool()
        tool.execute(channel="downstream", content="msg", sender="user")
        messages = fresh_store.get_messages(Channel.downstream)
        assert messages[0].sender == "user"

    def test_invalid_channel_returns_error(self, fresh_store):
        """无效频道标识返回错误。"""
        tool = self._make_tool()
        result = tool.execute(channel="invalid", content="test")
        assert result["error"] is True
        assert result["error_type"] == "INVALID_CHANNEL"

    def test_empty_content_returns_error(self, fresh_store):
        """空内容返回错误。"""
        tool = self._make_tool()
        result = tool.execute(channel="downstream", content="")
        assert result["error"] is True
        assert result["error_type"] == "EMPTY_CONTENT"

    def test_no_content_returns_error(self, fresh_store):
        """未传 content 参数返回错误。"""
        tool = self._make_tool()
        result = tool.execute(channel="downstream")
        assert result["error"] is True


# === Task 5: 退款登记工具 ===


class TestRefundTool:
    def _make_tool(self):
        from app.agent.tools.refund import RefundTool

        return RefundTool()

    def test_name(self):
        tool = self._make_tool()
        assert tool.name == "refund"

    def test_refund_success(self):
        """退款登记返回成功结果（AC #5）。"""
        tool = self._make_tool()
        result = tool.execute(
            order_id="HT20260301001", supplier_order_id="SUP-88901"
        )
        assert result["success"] is True
        assert result["data"]["refund_status"] == "approved"
        assert result["data"]["order_id"] == "HT20260301001"

    def test_refund_returns_message(self):
        """退款结果包含确认消息。"""
        tool = self._make_tool()
        result = tool.execute(order_id="HT20260301001")
        assert "退款登记成功" in result["data"]["message"]

    def test_refund_invalid_order_returns_error(self):
        """无效订单号退款返回错误（FR24 退款失败场景）。"""
        tool = self._make_tool()
        result = tool.execute(order_id="INVALID-ORDER")
        assert result["error"] is True
        assert result["error_type"] == "ORDER_NOT_FOUND"

    def test_refund_missing_order_id_returns_error(self):
        """缺少订单号退款返回错误。"""
        tool = self._make_tool()
        result = tool.execute()
        assert result["error"] is True
        assert result["error_type"] == "MISSING_ORDER_ID"

    def test_refund_fills_supplier_order_id(self):
        """退款时未传 supplier_order_id 自动从订单数据填充。"""
        tool = self._make_tool()
        result = tool.execute(order_id="HT20260301001")
        assert result["data"]["supplier_order_id"] == "SUP-88901"


# === Task 6: 上游自动回复 ===


class TestUpstreamReply:
    def test_reply_added_to_upstream_channel(self, fresh_store):
        """自动回复写入 upstream 频道（AC #7）。"""
        simulate_upstream_reply("SUP-88901")
        messages = fresh_store.get_messages(Channel.upstream)
        assert len(messages) == 1
        assert "SUP-88901" in messages[0].content
        assert "已处理完成" in messages[0].content
        assert messages[0].sender == "supplier"

    def test_reply_marks_channel_unread(self, fresh_store):
        """自动回复标记 upstream 频道未读。"""
        simulate_upstream_reply("SUP-88901")
        assert "upstream" in fresh_store.get_session().unread_channels

    def test_reply_returns_content(self, fresh_store):
        """函数返回回复消息内容。"""
        content = simulate_upstream_reply("SUP-88901")
        assert "SUP-88901" in content
        assert "已处理完成" in content

    def test_reply_no_session_raises(self):
        """无活跃会话时抛出 ValueError。"""
        no_session_store = MemoryStore()
        import app.mock.upstream as upstream_mod

        original = upstream_mod.store
        upstream_mod.store = no_session_store
        try:
            with pytest.raises(ValueError, match="No active session"):
                simulate_upstream_reply("SUP-88901")
        finally:
            upstream_mod.store = original


# === Task 7: 工具注册表 ===


class TestToolRegistry:
    def test_all_tools_registered(self):
        """自动发现并注册所有工具。"""
        from app.agent.tools import get_all_tools

        tools = get_all_tools()
        tool_names = {t.name for t in tools}
        assert "order_query" in tool_names
        assert "message_send" in tool_names
        assert "refund" in tool_names
        assert "order_cancel" in tool_names

    def test_get_tool_by_name(self):
        """按名称查找工具。"""
        from app.agent.tools import get_tool

        tool = get_tool("order_query")
        assert tool is not None
        assert tool.name == "order_query"

    def test_get_tool_not_found(self):
        """查找不存在的工具返回 None。"""
        from app.agent.tools import get_tool

        assert get_tool("nonexistent") is None

    def test_get_tool_definitions(self):
        """获取全部工具定义。"""
        from app.agent.tools import get_tool_definitions

        definitions = get_tool_definitions()
        assert len(definitions) >= 3
        assert all(isinstance(d, ToolDefinition) for d in definitions)
        names = {d.name for d in definitions}
        assert "order_query" in names
        assert "message_send" in names
        assert "refund" in names

    def test_tool_count_matches_expected(self):
        """注册的工具数量正确（4 个：order_query, message_send, refund, order_cancel）。"""
        from app.agent.tools import get_all_tools

        tools = get_all_tools()
        real_tools = [
            t
            for t in tools
            if t.name in ("order_query", "message_send", "refund", "order_cancel")
        ]
        assert len(real_tools) == 4


# === Story 2.1: 订单取消工具 ===


@pytest.fixture()
def _restore_order_status():
    """测试后恢复 MOCK_ORDERS 中被取消订单的原始状态。"""
    original_statuses = {oid: o["status"] for oid, o in MOCK_ORDERS.items()}
    yield
    for oid, status in original_statuses.items():
        MOCK_ORDERS[oid]["status"] = status


@pytest.mark.usefixtures("_restore_order_status")
class TestOrderCancelTool:
    def _make_tool(self):
        from app.agent.tools.order_cancel import OrderCancelTool

        return OrderCancelTool()

    def test_name(self):
        tool = self._make_tool()
        assert tool.name == "order_cancel"

    def test_description(self):
        tool = self._make_tool()
        assert tool.description == "取消指定订单号的订单"

    def test_cancel_valid_order_success(self):
        """有效订单取消成功（AC #3, FR25）。"""
        tool = self._make_tool()
        result = tool.execute(order_id="HT20260301002")
        assert result["success"] is True
        assert result["data"]["cancel_status"] == "cancelled"
        assert result["data"]["order_id"] == "HT20260301002"
        assert result["data"]["guest_name"] == "李四"
        assert result["data"]["hotel_name"] == "上海外滩酒店"
        assert "已成功取消" in result["data"]["message"]

    def test_cancel_updates_order_status(self):
        """取消后订单状态更新为 cancelled。"""
        tool = self._make_tool()
        tool.execute(order_id="HT20260301002")
        assert MOCK_ORDERS["HT20260301002"]["status"] == "cancelled"

    def test_cancel_invalid_order_returns_error(self):
        """无效订单号返回 ORDER_NOT_FOUND 错误（AC #4）。"""
        tool = self._make_tool()
        result = tool.execute(order_id="INVALID-ORDER")
        assert result["error"] is True
        assert result["error_type"] == "ORDER_NOT_FOUND"
        assert result["message"] == "订单不存在"

    def test_cancel_already_cancelled_order(self):
        """重复取消已取消订单返回 ORDER_ALREADY_CANCELLED 错误（AC #8）。"""
        tool = self._make_tool()
        # 第一次取消成功
        result1 = tool.execute(order_id="HT20260301002")
        assert result1["success"] is True
        # 第二次取消失败
        result2 = tool.execute(order_id="HT20260301002")
        assert result2["error"] is True
        assert result2["error_type"] == "ORDER_ALREADY_CANCELLED"
        assert "订单已取消，无法重复操作" in result2["message"]

    def test_cancel_empty_order_id_returns_error(self):
        """空订单号返回 MISSING_ORDER_ID 错误。"""
        tool = self._make_tool()
        result = tool.execute(order_id="")
        assert result["error"] is True
        assert result["error_type"] == "MISSING_ORDER_ID"

    def test_cancel_no_order_id_returns_error(self):
        """未传 order_id 参数返回错误。"""
        tool = self._make_tool()
        result = tool.execute()
        assert result["error"] is True
        assert result["error_type"] == "MISSING_ORDER_ID"

    def test_get_parameters(self):
        """参数定义包含 order_id。"""
        tool = self._make_tool()
        params = tool._get_parameters()
        assert "order_id" in params
        assert params["order_id"]["type"] == "string"

    def test_get_definition(self):
        """get_definition 返回正确的 ToolDefinition。"""
        tool = self._make_tool()
        definition = tool.get_definition()
        assert isinstance(definition, ToolDefinition)
        assert definition.name == "order_cancel"


# === Story 2.1: 工具注册表更新验证 ===


class TestToolRegistryWithOrderCancel:
    def test_order_cancel_registered(self):
        """order_cancel 工具已自动注册。"""
        from app.agent.tools import get_all_tools

        tools = get_all_tools()
        tool_names = {t.name for t in tools}
        assert "order_cancel" in tool_names

    def test_get_order_cancel_by_name(self):
        """按名称查找 order_cancel 工具。"""
        from app.agent.tools import get_tool

        tool = get_tool("order_cancel")
        assert tool is not None
        assert tool.name == "order_cancel"

    def test_order_cancel_in_definitions(self):
        """order_cancel 出现在工具定义列表中。"""
        from app.agent.tools import get_tool_definitions

        definitions = get_tool_definitions()
        names = {d.name for d in definitions}
        assert "order_cancel" in names


# === Story 2.1: Skill 注册验证 ===


class TestSkillRegistryWithOrderCancel:
    def test_order_cancel_skill_registered(self):
        """order_cancel Skill 已自动注册。"""
        from app.agent.skills import get_all_skills

        skills = get_all_skills()
        skill_ids = {s.skill_id for s in skills}
        assert "order_cancel" in skill_ids

    def test_order_cancel_skill_content(self):
        """order_cancel Skill 包含正确的名称和描述。"""
        from app.agent.skills import get_skill

        skill = get_skill("order_cancel")
        assert skill is not None
        assert skill.name == "订单取消"
        assert "取消" in skill.description

    def test_two_skills_registered(self):
        """系统注册了 2 个 Skill（early_checkout + order_cancel）。"""
        from app.agent.skills import get_all_skills

        skills = get_all_skills()
        assert len(skills) == 2
