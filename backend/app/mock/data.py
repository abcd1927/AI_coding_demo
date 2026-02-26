"""硬编码模拟数据 — 订单记录和供应商映射。"""

MOCK_ORDERS: dict[str, dict] = {
    "HT20260301001": {
        "order_id": "HT20260301001",
        "supplier_order_id": "SUP-88901",
        "guest_name": "张三",
        "hotel_name": "杭州西湖大酒店",
        "check_in": "2026-03-01",
        "check_out": "2026-03-05",
        "room_type": "大床房",
        "status": "confirmed",
    },
    "HT20260301002": {
        "order_id": "HT20260301002",
        "supplier_order_id": "SUP-88902",
        "guest_name": "李四",
        "hotel_name": "上海外滩酒店",
        "check_in": "2026-03-10",
        "check_out": "2026-03-12",
        "room_type": "双床房",
        "status": "confirmed",
    },
    "HT20260301003": {
        "order_id": "HT20260301003",
        "supplier_order_id": "SUP-88903",
        "guest_name": "王五",
        "hotel_name": "北京国贸大饭店",
        "check_in": "2026-03-15",
        "check_out": "2026-03-18",
        "room_type": "套房",
        "status": "confirmed",
    },
}
