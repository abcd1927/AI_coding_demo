import { useEffect, useRef } from 'react';
import { Timeline, Tag, Spin } from 'antd';
import { RobotOutlined, CheckCircleFilled, CloseCircleFilled, HourglassOutlined } from '@ant-design/icons';
import { useAppContext } from '../../context/AppContext';
import ActionLogItem from '../../components/ActionLogItem/ActionLogItem';
import type { ActionLogEntry } from '../../types';

function getTimelineDot(action: ActionLogEntry): React.ReactNode {
  if (action.status === 'running' && action.action_type === 'waiting') {
    return <HourglassOutlined style={{ fontSize: 14, color: '#FAAD14' }} />;
  }
  if (action.status === 'running') {
    return <Spin size="small" />;
  }
  if (action.status === 'success') {
    return <CheckCircleFilled style={{ fontSize: 14, color: '#52C41A' }} />;
  }
  if (action.status === 'error') {
    return <CloseCircleFilled style={{ fontSize: 14, color: '#FF4D4F' }} />;
  }
  return undefined;
}

const STATUS_TAG: Record<string, { color: string; label: string }> = {
  idle: { color: 'default', label: '空闲' },
  running: { color: 'processing', label: '执行中' },
  completed: { color: 'success', label: '已完成' },
  error: { color: 'error', label: '异常' },
};

const ActionLogPanel = () => {
  const { state } = useAppContext();
  const { actions, sessionStatus } = state;
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [actions.length]);

  if (actions.length === 0) {
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
  }

  const tagCfg = STATUS_TAG[sessionStatus] || STATUS_TAG.idle;

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ padding: '16px 24px 8px', display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
        <span style={{ fontSize: 18, fontWeight: 600 }}>Agent 动作日志</span>
        <Tag color={tagCfg.color}>{tagCfg.label}</Tag>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '8px 24px 24px' }}>
        <Timeline
          items={actions.map((action) => ({
            dot: getTimelineDot(action),
            children: <ActionLogItem action={action} />,
          }))}
        />
        <div ref={endRef} />
      </div>
    </div>
  );
};

export default ActionLogPanel;
