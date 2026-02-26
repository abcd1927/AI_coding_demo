import { Tabs, Input, Button } from 'antd';
import { SendOutlined } from '@ant-design/icons';

const channelTabs = [
  { key: 'chat', label: '对话' },
  { key: 'downstream', label: '下游群' },
  { key: 'upstream', label: '上游群' },
];

const MessagePanel = () => {
  return (
    <>
      <div style={{ padding: '0 24px' }}>
        <Tabs items={channelTabs} defaultActiveKey="chat" />
      </div>
      <div
        style={{
          flex: 1,
          padding: '0 24px',
          overflowY: 'auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#8c8c8c',
          fontSize: 14,
        }}
      >
        暂无消息
      </div>
      <div
        style={{
          padding: 16,
          borderTop: '1px solid #f0f0f0',
          display: 'flex',
          gap: 8,
        }}
      >
        <Input
          placeholder="输入客服消息，例如：订单号 HT20260301001 的客人申请提前离店"
          disabled
        />
        <Button type="primary" icon={<SendOutlined />} disabled>
          发送
        </Button>
      </div>
    </>
  );
};

export default MessagePanel;
