import type {
  Analytics,
  ChatResponse,
  Conversation,
  MemoryItem,
  Settings,
} from "./types";

export const API_URL: string =
  import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1";

const TOKEN_KEY = "echo-ai-token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable: session-only login */
  }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

let onUnauthorized: () => void = () => {};
export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler;
}

function errorMessage(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown })?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
  return `Request failed (${status})`;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && typeof init.body === "string") headers.set("Content-Type", "application/json");

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "Cannot reach the ECHO-AI server. Is the backend running?");
  }
  if (response.status === 401 && token) onUnauthorized();
  if (response.status === 204) return undefined as T;
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, errorMessage(body, response.status));
  return body as T;
}

const json = (method: string, data?: unknown): RequestInit => ({
  method,
  body: data === undefined ? undefined : JSON.stringify(data),
});

export const api = {
  register: (email: string, password: string) =>
    request<{ id: number; email: string }>("/auth/register", json("POST", { email, password })),
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", json("POST", { email, password })),
  me: () => request<{ id: number; email: string }>("/auth/me"),

  chat: (message: string, conversationId?: number) =>
    request<ChatResponse>(
      "/chat",
      json("POST", { message, ...(conversationId ? { conversation_id: conversationId } : {}) }),
    ),
  chatVoice: (wav: Blob, conversationId?: number) =>
    request<ChatResponse>(
      `/chat/voice${conversationId ? `?conversation_id=${conversationId}` : ""}`,
      { method: "POST", body: wav, headers: { "Content-Type": "audio/wav" } },
    ),

  history: () => request<{ conversations: Conversation[] }>("/history?limit=50"),
  deleteConversation: (id: number) => request<void>(`/history/${id}`, { method: "DELETE" }),
  feedback: (messageId: number, helpful: boolean) =>
    request("/feedback", json("POST", { message_id: messageId, helpful })),
  analytics: () => request<Analytics>("/analytics"),

  memories: () => request<{ enabled: boolean; items: MemoryItem[] }>("/memory"),
  addMemory: (content: string) => request<MemoryItem>("/memory", json("POST", { content })),
  deleteMemory: (id: number) => request<void>(`/memory/${id}`, { method: "DELETE" }),
  settings: () => request<Settings>("/settings"),
  updateSettings: (patch: Partial<Settings>) => request<Settings>("/settings", json("PATCH", patch)),
};
