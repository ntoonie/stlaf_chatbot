"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { sendChatMessage } from "../lib/api";
import { createClient } from "../lib/supabase";
import type { ChatMessage } from "../lib/types";
import type { User } from "@supabase/supabase-js";
import { v4 as uuidv4 } from "uuid";

const REFUSAL_TEXT =
  "I could not find information about this in the Philippine labor law documents I have access to.";

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const supabase = createClient();
  const [conversationSessionId] = useState<string>(() => uuidv4());

  useEffect(() => {
  supabase.auth.getSession().then(({ data, error }) => {
    console.log("SESSION DEBUG:", data.session);
    console.log("SESSION ERROR:", error);
  });
}, []);

  // Check auth status on page load; redirect to /login if not signed in
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
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/login");
  };

  const handleSend = async () => {
    const question = input.trim();
    if (!question || isLoading || !user) return;

    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setIsLoading(true);

    try {
      // Use the authenticated user's ID as the session identifier -
      // replaces the old random UUID from the pre-auth version
      const result = await sendChatMessage(question, conversationSessionId);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.answer, citations: result.citations },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "⚠️ Could not reach the chatbot backend. Please try again." },
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

  if (checkingAuth) {
    return <div className="auth-loading">Checking session...</div>;
  }

  return (
    <div className="app-container">
      <header>
        <div className="header-row">
          <div>
            <h1>⚖️ Philippine Labor Law Chatbot</h1>
            <p>Answers are grounded in official documents only.</p>
          </div>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <div className="messages-container">
        {messages.map((msg, idx) => {
          const isRefusal = msg.role === "assistant" && msg.content === REFUSAL_TEXT;
          return (
            <div key={idx} className={`message ${msg.role}${isRefusal ? " refusal" : ""}`}>
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
          );
        })}
        {isLoading && <div className="message loading">Thinking...</div>}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about Philippine labor law..."
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}