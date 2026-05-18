import React, { useState, useRef, useEffect } from 'react';
import { Send, ThumbsUp, ThumbsDown } from 'lucide-react';
import './App.css';

interface Message {
  id: string;
  role: 'user' | 'ai';
  text: string;
  feedback?: 'up' | 'down';
}

const API_BASE = 'http://localhost:8080/api';

const QUICK_CHIPS = [
  "🛑 What is the fever policy?",
  "🦃 Are we open on Veterans Day?",
  "🍏 I forgot to pack lunch today."
];

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: Message = {
      id: `parent-${Date.now()}-${Math.random()}`,
      role: 'user',
      text: text.trim()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/parent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text.trim(), session_id: 'poc-session' })
      });

      if (!response.ok) throw new Error('Failed to fetch');

      const data = await response.json();
      
      const aiMsg: Message = {
        id: data.log_id || `ai-${Date.now()}-${Math.random()}`,
        role: 'ai',
        text: data.answer
      };

      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        text: "I'm having a little trouble connecting. Please try again or reach out to the front desk directly."
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = async (msgId: string, type: 'up' | 'down') => {
    // Optimistic update
    setMessages(prev => prev.map(m => 
      m.id === msgId ? { ...m, feedback: type } : m
    ));

    try {
      await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          log_id: msgId, 
          feedback: type === 'up' ? 'thumbs_up' : 'thumbs_down' 
        })
      });
    } catch (error) {
      console.error('Feedback error:', error);
    }
  };

  return (
    <div className="mobile-container">
      <header>
        <div className="brand">
          <h1>Sunshine Early Learning</h1>
        </div>
        <div className="status">
          <div className="pulse-dot"></div>
          Front Desk Active
        </div>
      </header>

      <main className="chat-slate">
        {messages.length === 0 && (
          <div className="greeting-block">
            <p>Hi there! Ask me anything about Sunshine's schedules, tuition, meals, or health policies.</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className="message-container">
            <div className={`message ${msg.role === 'user' ? 'parent' : 'ai'}`}>
              {msg.text}
            </div>
            {msg.role === 'ai' && (
              <div className="feedback-row">
                <button 
                  className={`feedback-btn ${msg.feedback === 'up' ? 'active' : ''}`}
                  onClick={() => handleFeedback(msg.id, 'up')}
                >
                  <ThumbsUp size={14} fill={msg.feedback === 'up' ? 'currentColor' : 'none'} />
                </button>
                <button 
                  className={`feedback-btn ${msg.feedback === 'down' ? 'active' : ''}`}
                  onClick={() => handleFeedback(msg.id, 'down')}
                >
                  <ThumbsDown size={14} fill={msg.feedback === 'down' ? 'currentColor' : 'none'} />
                </button>
                {msg.feedback === 'down' && (
                  <div className="system-alert">
                    Flagged for review by staff.
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="message ai">
            <div className="loader-wave">
              <div className="loader-bar"></div>
              <div className="loader-bar"></div>
              <div className="loader-bar"></div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </main>

      <footer className="input-area">
        <div className="chips">
          {QUICK_CHIPS.map(chip => (
            <button key={chip} className="chip" onClick={() => handleSend(chip)}>
              {chip}
            </button>
          ))}
        </div>
        <form className="input-container" onSubmit={(e) => { e.preventDefault(); handleSend(input); }}>
          <input 
            type="text" 
            placeholder="Ask a question..." 
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button type="submit" className="send-btn" disabled={!input.trim() || isLoading}>
            <Send size={18} />
          </button>
        </form>
      </footer>
    </div>
  );
}

export default App;
