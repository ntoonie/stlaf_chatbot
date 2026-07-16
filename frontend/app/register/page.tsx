// frontend/app/register/page.tsx
"use client";

import { useState } from "react";
import { createClient } from "../../lib/supabase";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const supabase = createClient();

const handleRegister = async () => {
  setLoading(true);
  setError("");
  setMessage("");

  const { error } = await supabase.auth.signUp({
    email,
    password,
    options: { data: { display_name: displayName } },
  });

  if (error) {
    setError(error.message);
    setLoading(false);
    return;
  }

  // No manual profile insert needed - the database trigger handles it automatically
  setMessage("Check your email to verify your account before signing in.");
  setLoading(false);
};

  return (
    <div className="auth-container">
      <h1>Create Account</h1>
      <p className="auth-subtitle">Philippine Labor Law Chatbot</p>

      {error && <div className="auth-error">{error}</div>}
      {message && <div className="auth-success">{message}</div>}

      <input
        type="text"
        placeholder="Full name"
        value={displayName}
        onChange={(e) => setDisplayName(e.target.value)}
      />
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <button onClick={handleRegister} disabled={loading}>
        {loading ? "Creating account..." : "Register"}
      </button>

      <p className="auth-footer">
        Already have an account? <a href="/login">Sign In</a>
      </p>
    </div>
  );
}