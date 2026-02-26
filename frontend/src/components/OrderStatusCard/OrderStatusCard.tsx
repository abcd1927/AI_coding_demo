import { useEffect, useState, useCallback, useImperativeHandle, forwardRef } from 'react';
import { Card, Tag, Button, Table } from 'antd';
import { ReloadOutlined, DatabaseOutlined } from '@ant-design/icons';
import { getOrders, resetOrders } from '../../services/api';
import type { Order } from '../../types';

export interface OrderStatusCardRef {
  refreshOrders: () => void;
}

const STATUS_TAG: Record<string, { color: string; label: string }> = {
  confirmed: { color: 'green', label: 'confirmed' },
  cancelled: { color: 'red', label: 'cancelled' },
};

const columns = [
  { title: '订单号', dataIndex: 'order_id', key: 'order_id', width: 160 },
  { title: '客人', dataIndex: 'guest_name', key: 'guest_name', width: 80 },
  { title: '酒店', dataIndex: 'hotel_name', key: 'hotel_name' },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
    render: (status: string) => {
      const cfg = STATUS_TAG[status] || { color: 'default', label: status };
      return <Tag color={cfg.color}>{cfg.label}</Tag>;
    },
  },
];

const OrderStatusCard = forwardRef<OrderStatusCardRef>((_props, ref) => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  const fetchOrders = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getOrders();
      setOrders(data);
    } catch {
      // 静默处理
    } finally {
      setLoading(false);
    }
  }, []);

  useImperativeHandle(ref, () => ({ refreshOrders: fetchOrders }), [fetchOrders]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const handleReset = async () => {
    try {
      setLoading(true);
      const data = await resetOrders();
      setOrders(data);
    } catch {
      // 静默处理
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      size="small"
      title={
        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <DatabaseOutlined />
          订单数据
        </span>
      }
      extra={
        <span style={{ display: 'flex', gap: 8 }}>
          <Button size="small" icon={<ReloadOutlined />} onClick={handleReset}>
            重置
          </Button>
          <Button size="small" type="text" onClick={() => setCollapsed((v) => !v)}>
            {collapsed ? '展开' : '收起'}
          </Button>
        </span>
      }
      styles={{ body: { padding: collapsed ? 0 : '8px 0 0', display: collapsed ? 'none' : undefined } }}
      style={{ margin: '12px 12px 0', flexShrink: 0 }}
    >
      <Table
        dataSource={orders}
        columns={columns}
        rowKey="order_id"
        size="small"
        pagination={false}
        loading={loading}
      />
    </Card>
  );
});

OrderStatusCard.displayName = 'OrderStatusCard';

export default OrderStatusCard;
