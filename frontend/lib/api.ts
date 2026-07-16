import axios from "axios";
import { createClient } from "./supabase";
import type { ChatRequest, ChatResponse } from "./types";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function sendChatMessage(
  question: string,
  sessionId: string
): Promise<ChatResponse> {
  const supabase = createClient();

  // Get the current session's access token to attach as Bearer auth -
  // matches what backend/app/auth.py now requires on /chat.
  const { data: { session } } = await supabase.auth.getSession();

  if (!session) {
    throw new Error("Not authenticated. Please log in again.");
  }

  const payload: ChatRequest = { question, session_id: sessionId };

  const response = await axios.post<ChatResponse>(
    `${BACKEND_URL}/chat`,
    payload,
    {
      timeout: 60000,
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    }
  );

  return response.data;
}