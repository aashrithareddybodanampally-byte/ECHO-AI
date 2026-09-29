import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "../api";
import { VoiceRecorder, speak } from "../audio";
import { CameraMood, type FaceMood } from "../faceMood";
import type { ChatItem, ChatResponse } from "../types";
import { EmotionBadge } from "./EmotionBadge";

interface Props {
  conversationId: number | null;
  initialMessages: ChatItem[];
  autoSpeak: boolean;
  onConversationChanged: (id: number) => void;
}

export function ChatView({ conversationId, initialMessages, autoSpeak, onConversationChanged }: Props) {
  const [items, setItems] = useState<ChatItem[]>(initialMessages);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recorder = useRef<VoiceRecorder | null>(null);
  const bottom = useRef<HTMLDivElement>(null);
  const camera = useRef<CameraMood | null>(null);
  const video = useRef<HTMLVideoElement>(null);
  const [cameraState, setCameraState] = useState<"off" | "consent" | "starting" | "on">("off");
  const [faceMood, setFaceMood] = useState<FaceMood | null>(null);

  // Always release the camera when leaving the chat.
  useEffect(() => () => {
    camera.current?.stop();
  }, []);

  async function startCamera() {
    setError(null);
    setCameraState("starting");
    try {
      camera.current = new CameraMood();
      await camera.current.start(video.current!, setFaceMood);
      setCameraState("on");
    } catch {
      camera.current?.stop();
      camera.current = null;
      setCameraState("off");
      setError("Camera access was denied or is unavailable.");
    }
  }

  function stopCamera() {
    camera.current?.stop();
    camera.current = null;
    setFaceMood(null);
    setCameraState("off");
  }

  /** The averaged expression to send with a message, only while the camera is on. */
  function currentFace(): FaceMood | null {
    return cameraState === "on" ? camera.current?.current() ?? null : null;
  }

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [items, busy]);

  function applyResponse(response: ChatResponse, userText: string) {
    const replyItem: ChatItem = {
      ...response.reply,
      sources: response.sources,
      safety_level: response.safety_level,
      llm_model: response.llm_model,
    };
    setItems((prev) => {
      const withoutPending = prev.filter((m) => m.id !== -1);
      const userItem: ChatItem = {
        id: response.reply.id - 1,
        conversation_id: response.conversation_id,
        role: "user",
        content: userText,
        created_at: response.reply.created_at,
        // Never label a high-risk message with an emotion prediction.
        emotion: response.safety_level === "high_risk" ? null : response.emotion,
        transcript: response.transcript,
      };
      return [...withoutPending, userItem, replyItem];
    });
    if (autoSpeak) speak(response.reply.content);
    if (response.conversation_id !== conversationId) onConversationChanged(response.conversation_id);
  }

  async function send(event?: FormEvent) {
    event?.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setError(null);
    setBusy(true);
    setItems((prev) => [
      ...prev,
      { id: -1, conversation_id: conversationId ?? 0, role: "user", content: text, created_at: "" },
    ]);
    try {
      applyResponse(await api.chat(text, conversationId ?? undefined, currentFace()), text);
    } catch (e) {
      setItems((prev) => prev.filter((m) => m.id !== -1));
      setInput(text);
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function toggleRecording() {
    setError(null);
    if (!recording) {
      try {
        recorder.current = new VoiceRecorder();
        await recorder.current.start();
        setRecording(true);
      } catch {
        setError("Microphone access was denied or is unavailable.");
      }
      return;
    }
    setRecording(false);
    setBusy(true);
    try {
      const wav = await recorder.current!.stop();
      const response = await api.chatVoice(wav, conversationId ?? undefined, currentFace());
      applyResponse(response, response.transcript ?? "(voice message)");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function giveFeedback(item: ChatItem, helpful: boolean) {
    try {
      await api.feedback(item.id, helpful);
      setItems((prev) => prev.map((m) => (m.id === item.id ? { ...m, feedback: helpful } : m)));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-2xl space-y-5">
          {items.length === 0 && (
            <div className="mt-16 text-center text-slate-500">
              <p className="text-lg">How are you doing today?</p>
              <p className="mt-1 text-sm">Type a message or tap the microphone to talk.</p>
            </div>
          )}
          {items.map((item) =>
            item.role === "user" ? (
              <div key={item.id} className="flex flex-col items-end gap-1">
                <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-indigo-600 px-4 py-2 text-white whitespace-pre-wrap">
                  {item.transcript && <span className="mr-1 opacity-70">🎙</span>}
                  {item.content}
                </div>
                {item.emotion && <EmotionBadge emotion={item.emotion} />}
              </div>
            ) : (
              <div key={item.id} className="flex flex-col items-start gap-2">
                {item.safety_level === "high_risk" && (
                  <div className="w-full rounded-xl border border-rose-300 bg-rose-50 px-4 py-2 text-sm text-rose-800 dark:border-rose-800 dark:bg-rose-950/50 dark:text-rose-200">
                    If you are in immediate danger, please contact your local emergency number now.
                  </div>
                )}
                <div className="max-w-[85%] rounded-2xl rounded-bl-sm border border-slate-200 bg-white px-4 py-3 whitespace-pre-wrap dark:border-slate-800 dark:bg-slate-900">
                  {item.content}
                </div>
                {item.sources && item.sources.length > 0 && (
                  <details className="max-w-[85%] text-xs text-slate-500">
                    <summary className="cursor-pointer">Sources ({item.sources.length})</summary>
                    <ol className="mt-1 list-decimal space-y-1 pl-5">
                      {item.sources.map((s) => (
                        <li key={s.source}>
                          <span className="font-medium">{s.source}</span>: {s.content}
                        </li>
                      ))}
                    </ol>
                  </details>
                )}
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span>Was this helpful?</span>
                  {[true, false].map((helpful) => (
                    <button
                      key={String(helpful)}
                      onClick={() => giveFeedback(item, helpful)}
                      aria-label={helpful ? "Helpful" : "Not helpful"}
                      className={`rounded px-1.5 py-0.5 hover:bg-slate-200 dark:hover:bg-slate-800 ${item.feedback === helpful ? "bg-slate-200 dark:bg-slate-800" : ""}`}
                    >
                      {helpful ? "👍" : "👎"}
                    </button>
                  ))}
                  <button
                    onClick={() => speak(item.content)}
                    className="rounded px-1.5 py-0.5 hover:bg-slate-200 dark:hover:bg-slate-800"
                    aria-label="Read aloud"
                  >
                    🔊
                  </button>
                  {item.llm_model && <span className="opacity-60">{item.llm_model}</span>}
                </div>
              </div>
            ),
          )}
          {busy && <p className="text-sm text-slate-500">ECHO-AI is thinking…</p>}
          <div ref={bottom} />
        </div>
      </div>

      <form onSubmit={send} className="border-t border-slate-200 bg-white/80 p-3 dark:border-slate-800 dark:bg-slate-950/80">
        {error && <p className="mx-auto mb-2 max-w-2xl text-sm text-red-600">{error}</p>}
        {cameraState === "consent" && (
          <div className="mx-auto mb-3 max-w-2xl rounded-xl border border-indigo-400/20 bg-indigo-500/10 p-4 text-sm">
            <p className="font-medium text-white">Let ECHO-AI see your expression?</p>
            <p className="mt-1 text-slate-300">
              Your video is analyzed only in this browser and is never uploaded or saved. Only a short
              label such as &ldquo;sad, 70%&rdquo; is sent with your messages, and only while the camera is on.
              The estimate can be wrong.
            </p>
            <div className="mt-3 flex gap-2">
              <button type="button" onClick={startCamera}
                className="rounded-lg bg-indigo-500 px-3 py-1.5 font-medium text-white hover:bg-indigo-400">
                Turn on camera
              </button>
              <button type="button" onClick={() => setCameraState("off")}
                className="rounded-lg px-3 py-1.5 text-slate-300 hover:bg-white/5">
                Not now
              </button>
            </div>
          </div>
        )}
        <div className={`mx-auto mb-3 max-w-2xl items-center gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-2 ${cameraState === "on" || cameraState === "starting" ? "flex" : "hidden"}`}>
          <video ref={video} muted playsInline className="h-20 w-28 -scale-x-100 rounded-lg bg-black object-cover" />
          <div className="flex-1 text-sm">
            <p className="text-slate-300">
              {cameraState === "starting"
                ? "Starting camera…"
                : faceMood
                  ? <>Expression: <span className="font-medium text-white">{faceMood.emotion}</span> · {Math.round(faceMood.confidence * 100)}%</>
                  : "Looking for your face…"}
            </p>
            <p className="text-xs text-slate-500">Analyzed on this device only · estimate, not a diagnosis</p>
          </div>
          <button type="button" onClick={stopCamera}
            className="rounded-lg px-3 py-1.5 text-sm text-slate-300 hover:bg-white/5">
            Turn off
          </button>
        </div>
        <div className="mx-auto flex max-w-2xl gap-2">
          <button
            type="button"
            onClick={toggleRecording}
            disabled={busy && !recording}
            aria-label={recording ? "Stop recording" : "Record voice message"}
            className={`rounded-full px-4 ${recording ? "animate-pulse bg-rose-600 text-white" : "bg-slate-200 dark:bg-slate-800"}`}
          >
            {recording ? "■" : "🎙"}
          </button>
          <button
            type="button"
            onClick={() => (cameraState === "off" ? setCameraState("consent") : stopCamera())}
            aria-label={cameraState === "off" ? "Share facial expression (camera)" : "Turn camera off"}
            aria-pressed={cameraState === "on"}
            className={`rounded-full px-4 ${cameraState === "on" ? "bg-indigo-500 text-white" : "bg-slate-200 dark:bg-slate-800"}`}
          >
            📷
          </button>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={recording ? "Recording… tap ■ to send" : "Message ECHO-AI"}
            disabled={recording}
            className="flex-1 rounded-full border border-slate-300 bg-transparent px-4 py-2 dark:border-slate-700"
          />
          <button
            disabled={busy || !input.trim()}
            className="rounded-full bg-indigo-600 px-5 font-medium text-white disabled:opacity-40"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
