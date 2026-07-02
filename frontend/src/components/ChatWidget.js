import React, { useState, useRef, useCallback } from 'react';

const COL = {
  bg: '#080c16', card: '#111827', border: '#1f2937', text: '#e0e5ec',
  muted: '#6b7280', accent: '#00e5ff', userBubble: '#00e5ff', botBubble: '#1a2332',
};

export default function ChatWidget({ plantState, riskResult, compliance, healthIndex, riskTrend, alerts }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Ask me about plant risk, alerts, permits, compliance, incidents, or overall health.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const listRef = useRef(null);

  const send = useCallback(async () => {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);
    try {
      const res = await fetch('/api/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg }),
      });
      if (!res.ok) throw new Error('Chat request failed');
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'bot', text: data.answer }]);
    } catch {
      setMessages(prev => [...prev, { role: 'bot', text: 'Sorry, I encountered an error. Check the server connection.' }]);
    } finally {
      setLoading(false);
    }
  }, [input]);

  const handleKeyDown = (e) => { if (e.key === 'Enter') send(); };

  return (
    <>
      <div onClick={() => setOpen(!open)} style={{
        position: 'fixed', bottom: 20, right: 20, zIndex: 9999,
        width: 48, height: 48, borderRadius: '50%', background: COL.accent,
        color: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 22, cursor: 'pointer', boxShadow: '0 4px 20px rgba(0,229,255,0.3)',
      }}>{'\u{1F4AC}'}</div>
      {open && (
        <div style={{
          position: 'fixed', bottom: 76, right: 20, zIndex: 9999,
          width: 340, height: 460, background: COL.bg,
          border: `1px solid ${COL.border}`, borderRadius: 12,
          display: 'flex', flexDirection: 'column', boxShadow: '0 8px 40px rgba(0,0,0,0.5)',
        }}>
          <div style={{
            padding: '10px 14px', borderBottom: `1px solid ${COL.border}`,
            fontWeight: 600, fontSize: 13, color: COL.accent,
          }}>{'\u{1F916}\uFE0F'} AI Assistant</div>
          <div ref={listRef} style={{
            flex: 1, overflow: 'auto', padding: 10, display: 'flex', flexDirection: 'column', gap: 8,
          }}>
            {messages.map((m, i) => (
              <div key={i} style={{
                alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '80%', padding: '8px 12px', borderRadius: 10,
                background: m.role === 'user' ? COL.userBubble : COL.botBubble,
                color: m.role === 'user' ? '#000' : COL.text,
                fontSize: 12, lineHeight: 1.4,
              }}>{m.text}</div>
            ))}
            {loading && <div style={{ alignSelf: 'flex-start', color: COL.muted, fontSize: 11 }}>Thinking...</div>}
          </div>
          <div style={{ display: 'flex', borderTop: `1px solid ${COL.border}`, padding: 8 }}>
            <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
              placeholder="Ask something..."
              style={{
                flex: 1, padding: '8px 10px', background: COL.card, color: COL.text,
                border: `1px solid ${COL.border}`, borderRadius: 6, fontSize: 12, outline: 'none',
              }} />
            <button onClick={send} disabled={loading} style={{
              marginLeft: 6, padding: '8px 14px', background: COL.accent, color: '#000',
              border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer',
            }}>Send</button>
          </div>
        </div>
      )}
    </>
  );
}
