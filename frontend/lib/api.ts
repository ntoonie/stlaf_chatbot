import axios from "axios";
import type { ChatRequest, ChatResponse } from "./types";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function sendChatMessage(
  question: string,
  sessionId: string
): Promise<ChatResponse> {
  const payload: ChatRequest = { question, session_id: sessionId };

  const response = await axios.post<ChatResponse>(
    `${BACKEND_URL}/chat`,
    payload,
    { timeout: 60000 } // 60s - generous, matching real LLM latency
  );

  return response.data;
}
