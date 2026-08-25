import ReactMarkdown from 'react-markdown';
import { User, Bot } from 'lucide-react';
import ReliabilityBadge from './ReliabilityBadge';

export default function ChatMessage({ role, content, reliability }) {
  const isUser = role === 'user';
  return (
    <div className={`message ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-avatar">
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>
      <div className="message-body glass">
        {isUser ? (
          <p>{content}</p>
        ) : (
          <>
            <ReliabilityBadge reliability={reliability} />
            <ReactMarkdown>{content}</ReactMarkdown>
          </>
        )}
      </div>
    </div>
  );
}
