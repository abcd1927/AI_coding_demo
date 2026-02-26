import { useState, useRef, useEffect } from 'react';
import { Tabs, Input, Button, Badge, message } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import { useAppContext } from '../../context/AppContext';
import { sendMessage } from '../../services/api';
import { useMessagePolling } from '../../hooks/useMessagePolling';
import ChatBubble from '../../components/ChatBubble/ChatBubble';
import type { Channel, ChannelMessage } from '../../types';

function isUserMessage(msg: ChannelMessage, channel: Channel): boolean {
  if (channel === 'chat') {
    const s = msg.sender.toLowerCase();
    return s === 'user';
  }
  return false;
}

const MessagePanel = () => {
  const { state, dispatch } = useAppContext();
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 启动消息轮询
  useMessagePolling();

  const currentMessages = state.messages[state.currentChannel] ?? [];

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentMessages.length]);

  const handleSend = async () => {
    const text = inputValue.trim();
    if (!text || isSending) return;

    setInputValue('');
    setIsSending(true);

    // 乐观更新：立即将用户消息添加到 chat 频道
    const prevMessages = state.messages.chat;
    const optimisticMsg: ChannelMessage = {
      channel: 'chat',
      sender: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    dispatch({
      type: 'SET_MESSAGES',
      channel: 'chat',
      messages: [...prevMessages, optimisticMsg],
    });

    try {
      const resp = await sendMessage(text);
      dispatch({ type: 'SET_SESSION', sessionId: resp.session_id });
      dispatch({ type: 'SET_SESSION_STATUS', status: 'running' });
    } catch {
      // 回滚乐观更新
      dispatch({ type: 'SET_MESSAGES', channel: 'chat', messages: prevMessages });
      message.error('发送失败，请重试');
    } finally {
      setIsSending(false);
    }
  };

  const handleTabChange = (key: string) => {
    const channel = key as Channel;
    dispatch({ type: 'SET_CHANNEL', channel });
    dispatch({ type: 'CLEAR_UNREAD', channel });
  };

  const tabItems = [
    {
      key: 'chat' as const,
      label: (
        <Badge dot={state.unreadChannels.has('chat')} offset={[6, 0]}>
          对话
        </Badge>
      ),
    },
    {
      key: 'downstream' as const,
      label: (
        <Badge dot={state.unreadChannels.has('downstream')} offset={[6, 0]}>
          下游群
        </Badge>
      ),
    },
    {
      key: 'upstream' as const,
      label: (
        <Badge dot={state.unreadChannels.has('upstream')} offset={[6, 0]}>
          上游群
        </Badge>
      ),
    },
  ];

  const showInput = state.currentChannel === 'chat';

  return (
    <>
      <div style={{ padding: '0 24px' }}>
        <Tabs
          items={tabItems}
          activeKey={state.currentChannel}
          onChange={handleTabChange}
        />
      </div>

      <div
        style={{
          flex: 1,
          padding: '0 24px',
          overflowY: 'auto',
        }}
      >
        {currentMessages.length === 0 ? (
          <div
            style={{
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#8c8c8c',
              fontSize: 14,
            }}
          >
            暂无消息
          </div>
        ) : (
          <div style={{ paddingTop: 16, paddingBottom: 8 }}>
            {currentMessages.map((msg, idx) => (
              <ChatBubble
                key={`${msg.timestamp}-${idx}`}
                sender={msg.sender}
                content={msg.content}
                isUser={isUserMessage(msg, state.currentChannel)}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {showInput && (
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
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onPressEnter={handleSend}
            disabled={isSending}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={isSending}
          >
            发送
          </Button>
        </div>
      )}
    </>
  );
};

export default MessagePanel;
