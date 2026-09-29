import { useCallback, useEffect, useState } from "react";
import { api, getToken, setToken, setUnauthorizedHandler } from "./api";
import { AuthPage } from "./components/AuthPage";
import { Landing } from "./components/landing/Landing";
import { Logo } from "./components/Logo";
import { navigate, useRoute } from "./route";
import { ChatView } from "./components/ChatView";
import { InsightsView } from "./components/InsightsView";
import { SettingsView } from "./components/SettingsView";
import type { ChatItem, Conversation, Settings } from "./types";

type View = "chat" | "insights" | "settings";
const AUTO_SPEAK_KEY = "echo-ai-auto-speak";

function readAutoSpeak(): boolean {
  try {
    return localStorage.getItem(AUTO_SPEAK_KEY) === "1";
  } catch {
    return false;
  }
}

export default function App() {
  const [authed, setAuthed] = useState(() => Boolean(getToken()));
  const route = useRoute();
  const [email, setEmail] = useState<string | null>(null);
  const [view, setView] = useState<View>("chat");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [chatKey, setChatKey] = useState(0);
  const [initialMessages, setInitialMessages] = useState<ChatItem[]>([]);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [autoSpeak, setAutoSpeak] = useState(readAutoSpeak);
  const [menuOpen, setMenuOpen] = useState(false);

  const logout = useCallback(() => {
    setToken(null);
    setAuthed(false);
    setConversations([]);
    setActiveId(null);
    // Never let the next account on this browser see the previous one's messages.
    setInitialMessages([]);
    setChatKey((k) => k + 1);
    navigate("home");
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(logout);
  }, [logout]);

  const refreshHistory = useCallback(async () => {
    const { conversations } = await api.history();
    setConversations(conversations);
  }, []);

  useEffect(() => {
    if (!authed) return;
    api.me().then((u) => setEmail(u.email)).catch(() => {});
    api.settings().then(setSettings).catch(() => {});
    refreshHistory().catch(() => {});
  }, [authed, refreshHistory]);

  if (!authed) {
    if (route === "home") return <Landing />;
    return <AuthPage key={route} mode={route} onAuthenticated={() => setAuthed(true)} />;
  }

  function openConversation(id: number | null) {
    // Messages are loaded only when a conversation is explicitly opened; the
    // ChatView (re-keyed below) then owns them for the rest of the session.
    setInitialMessages(conversations.find((c) => c.id === id)?.messages ?? []);
    setActiveId(id);
    setChatKey((k) => k + 1);
    setView("chat");
    setMenuOpen(false);
  }

  async function deleteConversation(id: number) {
    if (!confirm("Delete this conversation permanently?")) return;
    await api.deleteConversation(id);
    if (id === activeId) openConversation(null);
    await refreshHistory();
  }

  function changeAutoSpeak(value: boolean) {
    setAutoSpeak(value);
    try {
      localStorage.setItem(AUTO_SPEAK_KEY, value ? "1" : "0");
    } catch {
      /* ignore */
    }
  }

  const nav = (id: View, label: string) => (
    <button
      onClick={() => { setView(id); setMenuOpen(false); }}
      className={`w-full rounded-lg px-3 py-2 text-left text-sm ${view === id ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5 hover:text-white"}`}
    >
      {label}
    </button>
  );

  return (
    <div className="flex h-screen">
      <aside
        className={`${menuOpen ? "fixed inset-0 z-20 flex" : "hidden"} w-full flex-col border-r border-white/5 bg-ink-900 p-3 md:static md:flex md:w-72`}
      >
        <div className="mb-3 flex items-center justify-between">
          <Logo />
          <button className="md:hidden" onClick={() => setMenuOpen(false)} aria-label="Close menu">✕</button>
        </div>
        <button
          onClick={() => openConversation(null)}
          className="mb-3 rounded-lg bg-indigo-500 px-3 py-2 text-sm font-medium text-white shadow-lg shadow-indigo-500/20 hover:bg-indigo-400"
        >
          + New conversation
        </button>
        {nav("chat", "Chat")}
        {nav("insights", "Insights")}
        {nav("settings", "Memory & settings")}
        <p className="mt-4 mb-1 px-3 text-xs uppercase tracking-wide text-slate-500">History</p>
        <ul className="flex-1 space-y-0.5 overflow-y-auto">
          {conversations.map((c) => (
            <li key={c.id} className="group flex items-center">
              <button
                onClick={() => openConversation(c.id)}
                className={`flex-1 truncate rounded-lg px-3 py-1.5 text-left text-sm ${c.id === activeId && view === "chat" ? "bg-white/10 text-white" : "text-slate-400 hover:bg-white/5 hover:text-slate-200"}`}
              >
                {c.title || "Untitled"}
              </button>
              <button
                onClick={() => deleteConversation(c.id)}
                aria-label="Delete conversation"
                className="px-2 text-slate-400 opacity-0 group-hover:opacity-100 hover:text-rose-600"
              >
                🗑
              </button>
            </li>
          ))}
        </ul>
        <div className="mt-3 border-t border-white/5 pt-3 text-sm">
          <p className="truncate text-slate-500">{email}</p>
          <button onClick={logout} className="mt-1 text-indigo-300 hover:text-indigo-200">Log out</button>
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-white/5 px-4 py-2 md:hidden">
          <button onClick={() => setMenuOpen(true)} aria-label="Open menu">☰</button>
          <Logo />
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto">
          {view === "chat" && (
            <ChatView
              key={chatKey}
              conversationId={activeId}
              initialMessages={initialMessages}
              autoSpeak={autoSpeak}
              onConversationChanged={(id) => {
                setActiveId(id);
                refreshHistory().catch(() => {});
              }}
            />
          )}
          {view === "insights" && <InsightsView statsEnabled={settings?.save_emotion_stats ?? false} />}
          {view === "settings" && settings && (
            <SettingsView
              settings={settings}
              onSettingsChange={setSettings}
              autoSpeak={autoSpeak}
              onAutoSpeakChange={changeAutoSpeak}
            />
          )}
        </div>
        <footer className="border-t border-white/5 px-4 py-1.5 text-center text-xs text-slate-500">
          ECHO-AI can make mistakes and is not a medical service. In an emergency, contact local emergency services.
        </footer>
      </main>
    </div>
  );
}
