// RECONSTRUCTED from project_knowledge_search - verify against your
// real app/forgot-password/page.tsx before replacing it.

"use client";

import { useState } from "react";
import { createClient } from "../../lib/supabase";
import MarketingShell from "../components/marketing-shell";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const supabase = createClient();

  const handleReset = async () => {
    setLoading(true);
    setError("");
    setMessage("");

    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });

    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }

    setMessage("If an account exists for that email, a password reset link has been sent.");
    setLoading(false);
  };

  return (
    <MarketingShell>
      <div className="auth-card">
        <h1>Reset Password</h1>
        <p className="auth-subtitle">Philippine Labor Law Chatbot</p>

        {error && <div className="auth-error">{error}</div>}
        {message && <div className="auth-success">{message}</div>}

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <button onClick={handleReset} disabled={loading || !email}>
          {loading ? "Sending..." : "Send Reset Link"}
        </button>

        <p className="auth-footer">
          <a href="/login">Back to Sign In</a>
        </p>
      </div>
    </MarketingShell>
  );
}
