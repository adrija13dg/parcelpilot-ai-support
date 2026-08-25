import { useState, useRef, useEffect } from 'react';
import { Send, Bot } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useSession } from '../context/SessionContext';
import ChatMessage from '../components/ChatMessage';
import ToolTrace from '../components/ToolTrace';
import EscalationModal from '../components/EscalationModal';

const STARTERS = [
  'Can Northstar cancel ORD-1001 without a fee?',
  'Is TKT-501 a P1 and is SLA breached?',
  'Does LumenWorks get a credit on ORD-2002?',
  'What are the cancellation policies?',
];

export default function ChatPage() {
  const { session } = useSession();
  const location = useLocation();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [toolTrace, setToolTrace] = useState([]);
  const [pending, setPending] = useState(null);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading, toolTrace]);

  useEffect(() => {
    if (location.state?.prefill) {
      sendMessage(location.state.prefill);
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state]);

  const sendMessage = async (text) => {
    const content = (text || input).trim();
    if (!content || loading) return;

    setInput('');
    setError('');
    const userMsg = { role: 'user', content };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setLoading(true);

    try {
      const res = await api.chat(nextMessages, session);
      setMessages([
        ...nextMessages,
        { role: 'assistant', content: res.reply, reliability: res.reliability },
      ]);
      setToolTrace(res.tool_trace || []);
      setPending(res.pending_escalation || null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    if (!pending) return;
    setConfirmLoading(true);
    try {
      const res = await api.confirmEscalation({
        session,
        ticket_id: pending.ticket_id,
        reason: pending.reason,
        severity: pending.severity,
      });
      setPending(null);
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: `Escalation **${res.escalation_id}** created for ticket ${res.ticket_id}.` },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setConfirmLoading(false);
    }
  };

  return (
    <div className="chat-page">
      <header className="page-header">
        <div>
          <div className="header-badge">Live agent</div>
          <h2>AI Support</h2>
          <p>
            {session.is_internal ? 'Internal Support' : session.account_name}
            <span className="dot">·</span>
            Snapshot 16 Aug 2026, 11:00 IST
          </p>
        </div>
        <div className="header-icon-wrap">
          <Bot size={22} strokeWidth={2} />
        </div>
      </header>

      <div className="chat-area">
        {messages.length === 0 && (
          <div className="starters">
            <div className="starters-icon">
              <Bot size={28} strokeWidth={2} />
            </div>
            <h3>How can I help today?</h3>
            <p>Pick a demo question or ask about orders, tickets, policies, or escalations.</p>
            <div className="starter-grid">
              {STARTERS.map((q) => (
                <button key={q} type="button" className="starter-chip" onClick={() => sendMessage(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <ChatMessage key={i} role={m.role} content={m.content} reliability={m.reliability} />
        ))}

        {loading && (
          <div className="typing-indicator glass">
            <span /><span /><span />
            Agent is thinking…
          </div>
        )}

        {error && <div className="error-banner">{error}</div>}
        <ToolTrace trace={toolTrace} />
        <div ref={bottomRef} />
      </div>

      <form
        className="chat-input-bar"
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage();
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about orders, tickets, policies, or escalations…"
          disabled={loading}
        />
        <button type="submit" className="send-btn" disabled={loading || !input.trim()} aria-label="Send">
          <Send size={18} strokeWidth={2.25} />
        </button>
      </form>

      <EscalationModal
        pending={pending}
        onConfirm={handleConfirm}
        onCancel={() => setPending(null)}
        loading={confirmLoading}
      />
    </div>
  );
}
