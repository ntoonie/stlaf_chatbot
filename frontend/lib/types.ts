// Mirrors backend/app/schemas.py exactly. If the backend response
// shape changes, update this file to match.

export interface ChatRequest {
  question: string;
  session_id: string;
}

export interface SourceCitation {
  title: string;
  law_number: string;
  page_reference: string;
  category: string;
  snippet: string;
  distance: number;
}

export interface ChatResponse {
  answer: string;
  citations: SourceCitation[];
  citation_count: number;
  found_context: boolean;
  latency_seconds: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: SourceCitation[];
}
