"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { sendChatMessage } from "../lib/api";
import { createClient } from "../lib/supabase";
import type { ChatMessage } from "../lib/types";
import type { User } from "@supabase/supabase-js";
import { v4 as uuidv4 } from "uuid";
import MarketingShell, { ScalesIcon } from "./components/marketing-shell";

const REFUSAL_TEXT =
  "I could not find information about this in the Philippine labor law documents I have access to.";

type DisplayMessage = ChatMessage & { timestamp: string };

const QUICK_ACTIONS = [
  { label: "Minimum Wage", question: "What is the minimum wage in the Philippines?" },
  { label: "Overtime Pay", question: "How is overtime pay computed?" },
  { label: "Holiday Pay", question: "How is holiday pay computed?" },
  { label: "13th Month Pay", question: "How is 13th month pay computed?" },
  { label: "Leave Benefits", question: "What leave benefits are employees entitled to?" },
  { label: "Separation Pay", question: "How is separation pay computed?" },
  { label: "Working Hours", question: "What are the standard working hours under the Labor Code?" },
  { label: "Maternity Leave", question: "What are the requirements for maternity leave?" },
];

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M4 12L20 4L13 20L11 13L4 12Z" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function MenuDotsIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <circle cx="5" cy="12" r="1.6" />
      <circle cx="12" cy="12" r="1.6" />
      <circle cx="19" cy="12" r="1.6" />
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 5v14M5 12h14" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function DownloadIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 3v12m0 0l-4-4m4 4l4-4M5 19h14" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function Home() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const supabase = createClient();
  const [conversationSessionId, setConversationSessionId] = useState<string>(() => uuidv4());

  useEffect(() => {
    const checkUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        router.push("/login");
        return;
      }
      setUser(user);
      setCheckingAuth(false);
    };
    checkUser();
  }, []);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container) {
      container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
    }
  }, [messages, isLoading]);

  useEffect(() => {
    if (!menuOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenuOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [menuOpen]);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/login");
  };

  const nowStamp = () =>
    new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const handleSend = async (overrideText?: string) => {
    const question = (overrideText ?? input).trim();
    if (!question || isLoading || !user) return;

    setMessages((prev) => [...prev, { role: "user", content: question, timestamp: nowStamp() }]);
    setInput("");
    setIsLoading(true);

    try {
      const result = await sendChatMessage(question, conversationSessionId);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.answer, citations: result.citations, timestamp: nowStamp() },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "⚠️ Could not reach the chatbot backend. Please try again.", timestamp: nowStamp() },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewChat = () => {
    setMenuOpen(false);
    if (messages.length > 0) {
      const confirmed = window.confirm("Start a new chat? This will clear the current conversation from view.");
      if (!confirmed) return;
    }
    setMessages([]);
    setConversationSessionId(uuidv4());
  };

  const handleExport = () => {
    setMenuOpen(false);
    if (messages.length === 0) return;

    const lines = messages.map((msg) => {
      const speaker = msg.role === "user" ? "You" : "STLAF Assistant";
      let block = `[${msg.timestamp}] ${speaker}:\n${msg.content}`;
      if (msg.citations && msg.citations.length > 0) {
        const sourceLines = msg.citations.map((c) => `  - ${c.title}, ${c.page_reference}`).join("\n");
        block += `\n\nSources:\n${sourceLines}`;
      }
      return block;
    });

    const transcript = `STLAF Labor Law Chatbot - Conversation Export\n${new Date().toLocaleString()}\n\n${lines.join("\n\n---\n\n")}\n`;
    const blob = new Blob([transcript], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `stlaf-chat-${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (checkingAuth) {
    return <div className="auth-loading">Checking session...</div>;
  }

  return (
    <MarketingShell showLogout onLogout={handleLogout}>
      <div className="chat-card">
        <div className="chat-header">
          <div className="chat-header-left">
            <div className="chat-header-avatar-wrap">
              <div className="chat-header-avatar">
                <ScalesIcon size={18} />
              </div>
              <span className="online-dot" />
            </div>
            <div>
              <div className="chat-header-name">STLAF Assistant</div>
              <div className="chat-header-status">Online</div>
            </div>
          </div>
          <div className="chat-header-actions" ref={menuRef}>
            <div className="chat-menu-wrap">
              <button aria-label="More options" onClick={() => setMenuOpen((v) => !v)} aria-expanded={menuOpen}>
                <MenuDotsIcon />
              </button>
              {menuOpen && (
                <div className="chat-menu-dropdown" role="menu">
                  <button className="chat-menu-item" role="menuitem" onClick={handleNewChat}>
                    <PlusIcon />
                    New Chat
                  </button>
                  <button className="chat-menu-item" role="menuitem" onClick={handleExport} disabled={messages.length === 0}>
                    <DownloadIcon />
                    Export Conversation
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="messages-container" ref={messagesContainerRef}>
          {messages.length === 0 && (
            <div className="welcome-block">
              <h2>How can I help you today?</h2>
              <p>Ask about wages, leave, benefits, or workplace rights - or try one of these:</p>
              <div className="chip-grid">
                {QUICK_ACTIONS.map((action) => (
                  <button key={action.label} className="chip" onClick={() => handleSend(action.question)} disabled={isLoading}>
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => {
            const isRefusal = msg.role === "assistant" && msg.content === REFUSAL_TEXT;
            const isUser = msg.role === "user";
            return (
              <div key={idx} className={`message-row ${msg.role}`}>
                <div className={`avatar ${isUser ? "user-avatar" : "assistant-avatar"}`}>
                  {isUser ? "U" : <ScalesIcon size={16} />}
                </div>
                <div className="message-col">
                  <div className={`message ${msg.role}${isRefusal ? " refusal" : ""}`}>
                    <div>{msg.content}</div>
                    {msg.citations && msg.citations.length > 0 && (
                      <details className="sources">
                        <summary>Sources ({msg.citations.length})</summary>
                        {msg.citations.map((c, i) => (
                          <div key={i} className="citation">
                            <strong>{c.title}</strong>, {c.page_reference}
                            <p className="snippet">&quot;{c.snippet}&quot;</p>
                          </div>
                        ))}
                      </details>
                    )}
                  </div>
                  <span className="message-timestamp">{msg.timestamp}</span>
                </div>
              </div>
            );
          })}

          {isLoading && (
            <div className="message-row assistant">
              <div className="avatar assistant-avatar">
                <ScalesIcon size={16} />
              </div>
              <div className="message loading">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          )}
        </div>

        <div className="input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about Philippine labor laws..."
            disabled={isLoading}
          />
          <button className="send-btn" onClick={() => handleSend()} disabled={isLoading || !input.trim()} aria-label="Send message">
            <SendIcon />
          </button>
        </div>
      </div>
    </MarketingShell>
  );
}
