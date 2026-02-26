import { Collapse } from 'antd';
import type { ActionLogEntry } from '../../types';
import './ActionLogItem.css';

interface ActionLogItemProps {
  action: ActionLogEntry;
}

const STATUS_BG: Record<string, string> = {
  running: '#E6F4FF',
  success: '#F6FFED',
  error: '#FFF2F0',
};

const KEY_LABELS: Record<string, string> = {
  intent: '识别意图',
  confidence: '置信度',
  skill_id: 'Skill ID',
  skill_name: 'Skill 名称',
  tool_name: '工具名称',
  input: '输入',
  output: '输出',
  channel: '目标频道',
  content: '消息内容',
  waiting_for: '等待',
  final_reply: '最终回复',
  order_no: '订单号',
  supplier_no: '供应商订单号',
  error: '错误',
  message: '消息',
  result: '结果',
  refund_id: '退款单号',
  amount: '金额',
  status: '状态',
};

function formatKey(key: string): string {
  return KEY_LABELS[key] || key;
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (Array.isArray(value)) return value.map(formatValue).join(', ');
  return JSON.stringify(value, null, 2);
}

function renderDetail(detail: Record<string, unknown>) {
  return (
    <div style={{ padding: '8px 12px', background: '#fafafa', borderRadius: 4, fontSize: 13, lineHeight: 1.6 }}>
      {Object.entries(detail).map(([key, value]) => (
        <div key={key} style={{ marginBottom: 4 }}>
          <span style={{ color: '#8c8c8c', marginRight: 8 }}>{formatKey(key)}:</span>
          {typeof value === 'object' && value !== null && !Array.isArray(value) ? (
            <div style={{ paddingLeft: 16, marginTop: 2 }}>
              {Object.entries(value as Record<string, unknown>).map(([k, v]) => (
                <div key={k} style={{ marginBottom: 2 }}>
                  <span style={{ color: '#8c8c8c', marginRight: 8 }}>{formatKey(k)}:</span>
                  <span>{formatValue(v)}</span>
                </div>
              ))}
            </div>
          ) : (
            <span>{formatValue(value)}</span>
          )}
        </div>
      ))}
    </div>
  );
}

function getStatusBg(action: ActionLogEntry): string {
  if (action.status === 'running' && action.action_type === 'waiting') {
    return '#FFFBE6';
  }
  return STATUS_BG[action.status] ?? '#fff';
}

const ActionLogItem = ({ action }: ActionLogItemProps) => {
  const bgColor = getStatusBg(action);
  const hasDetail = action.detail && Object.keys(action.detail).length > 0;
  const isError = action.status === 'error';

  const ts = action.timestamp
    ? new Date(action.timestamp).toLocaleTimeString('zh-CN', { hour12: false })
    : '';

  return (
    <div className="action-log-item" style={{ background: bgColor, borderRadius: 8, padding: '12px 16px', marginBottom: 4 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 16, fontWeight: 500, flex: 1 }}>{action.title}</span>
        <span style={{ fontSize: 12, color: '#8c8c8c', flexShrink: 0 }}>{ts}</span>
      </div>

      <div style={{ fontSize: 14, color: '#595959', marginTop: 4 }}>
        {action.summary}
      </div>

      {hasDetail && (
        <div style={{ marginTop: 8 }}>
          <Collapse
            size="small"
            defaultActiveKey={isError ? ['detail'] : []}
            items={[
              {
                key: 'detail',
                label: <span style={{ fontSize: 12, color: '#8c8c8c' }}>查看详情</span>,
                children: renderDetail(action.detail!),
              },
            ]}
            ghost
          />
        </div>
      )}
    </div>
  );
};

export default ActionLogItem;
