import { RobotOutlined } from '@ant-design/icons';

const ActionLogPanel = () => {
  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
        color: '#8c8c8c',
      }}
    >
      <RobotOutlined style={{ fontSize: 48, marginBottom: 16, color: '#d9d9d9' }} />
      <p style={{ fontSize: 16, margin: 0 }}>
        发送一条消息，观看 Agent 的工作过程
      </p>
    </div>
  );
};

export default ActionLogPanel;
