export type Role = "user" | "assistant" | "system";

export interface Message {
  id: number;
  conversation_id: number;
  role: Role;
  content: string;
  created_at: string;
}

export interface Conversation {
  id: number;
  title: string | null;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface Source {
  source: string;
  content: string;
  score: number;
}

export interface FusionResult {
  state: string;
  confidence: number;
  signals: { voice: number | null; text: number | null; face?: number | null; context: number | null };
}

export type SafetyLevel = "normal" | "distress" | "high_risk";

export interface ChatResponse {
  conversation_id: number;
  reply: Message;
  sources: Source[];
  emotion: FusionResult | null;
  safety_level: SafetyLevel;
  transcript: string | null;
  llm_model: string | null;
  timings_ms: Record<string, number>;
}

export interface Settings {
  memory_enabled: boolean;
  save_emotion_stats: boolean;
  response_style: "concise" | "balanced" | "detailed";
}

export interface MemoryItem {
  id: number;
  content: string;
  created_at: string;
}

export interface Analytics {
  emotion_distribution: Record<string, number>;
  feedback: { helpful: number; not_helpful: number };
}

/** A message shown in the chat, with live-only details from the response. */
export interface ChatItem extends Message {
  emotion?: FusionResult | null;
  sources?: Source[];
  safety_level?: SafetyLevel;
  llm_model?: string | null;
  transcript?: string | null;
  feedback?: boolean;
}
