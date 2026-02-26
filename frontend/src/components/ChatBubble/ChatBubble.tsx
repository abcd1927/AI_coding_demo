import './ChatBubble.css';

interface ChatBubbleProps {
  sender: string;
  content: string;
  isUser: boolean;
}

const ChatBubble = ({ sender, content, isUser }: ChatBubbleProps) => {
  const align = isUser ? 'user' : 'other';

  return (
    <div className={`chat-bubble-wrapper ${align}`}>
      <span className="chat-bubble-sender">{sender}</span>
      <div className={`chat-bubble ${align}`}>{content}</div>
    </div>
  );
};

export default ChatBubble;
