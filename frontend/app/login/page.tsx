// frontend/app/login/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "../../lib/supabase";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const supabase = createClient();

  const handleLogin = async () => {
    setLoading(true);
    setError("");

    const { error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }

    router.push("/"); // redirect to chat page after successful login
    router.refresh();
  };

  return (
    <div className="auth-container">
      <h1>Sign In</h1>
      <p className="auth-subtitle">Philippine Labor Law Chatbot</p>

      {error && <div className="auth-error">{error}</div>}

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
      <button onClick={handleLogin} disabled={loading}>
        {loading ? "Signing in..." : "Sign In"}
      </button>

      <p className="auth-footer">
        Don&apos;t have an account? <a href="/register">Register</a>
      </p>
      <p className="auth-footer">
        <a href="/forgot-password">Forgot password?</a>
      </p>
    </div>
  );
}