import { useEffect, useState, type FormEvent } from "react";
import { api } from "../api";
import type { MemoryItem, Settings } from "../types";

interface Props {
  settings: Settings;
  onSettingsChange: (s: Settings) => void;
  autoSpeak: boolean;
  onAutoSpeakChange: (value: boolean) => void;
}

function Toggle({ label, hint, checked, onChange }: {
  label: string; hint: string; checked: boolean; onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-start justify-between gap-4 py-3">
      <span>
        <span className="block font-medium">{label}</span>
        <span className="block text-sm text-slate-500">{hint}</span>
      </span>
      <input type="checkbox" className="mt-1 h-5 w-5 accent-indigo-600" checked={checked}
        onChange={(e) => onChange(e.target.checked)} />
    </label>
  );
}

export function SettingsView({ settings, onSettingsChange, autoSpeak, onAutoSpeakChange }: Props) {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.memories().then((m) => setMemories(m.items)).catch((e) => setError(e.message));
  }, []);

  async function update(patch: Partial<Settings>) {
    try {
      onSettingsChange(await api.updateSettings(patch));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function addMemory(event: FormEvent) {
    event.preventDefault();
    if (!draft.trim()) return;
    try {
      const item = await api.addMemory(draft.trim());
      setMemories((prev) => [...prev, item]);
      setDraft("");
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function removeMemory(id: number) {
    try {
      await api.deleteMemory(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8 p-6">
      {error && <p className="text-sm text-red-600">{error}</p>}
      <section>
        <h2 className="text-lg font-semibold">Privacy &amp; preferences</h2>
        <div className="mt-2 divide-y divide-slate-200 dark:divide-slate-800">
          <Toggle label="Use memory" hint="Let ECHO-AI use the facts you saved below when replying."
            checked={settings.memory_enabled} onChange={(v) => update({ memory_enabled: v })} />
          <Toggle label="Save emotional statistics"
            hint="Store emotion predictions for your Insights page. Off by default."
            checked={settings.save_emotion_stats} onChange={(v) => update({ save_emotion_stats: v })} />
          <Toggle label="Read replies aloud" hint="Speak each reply using your browser's voice."
            checked={autoSpeak} onChange={onAutoSpeakChange} />
          <label className="flex items-center justify-between gap-4 py-3">
            <span>
              <span className="block font-medium">Response length</span>
              <span className="block text-sm text-slate-500">How much detail you prefer.</span>
            </span>
            <select value={settings.response_style}
              onChange={(e) => update({ response_style: e.target.value as Settings["response_style"] })}
              className="rounded-lg border border-slate-300 bg-transparent px-2 py-1 dark:border-slate-700">
              <option value="concise">Concise</option>
              <option value="balanced">Balanced</option>
              <option value="detailed">Detailed</option>
            </select>
          </label>
          <p className="py-3 text-sm text-slate-500">
            Raw audio is processed in memory and never stored.
          </p>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Memory</h2>
        <p className="mt-1 text-sm text-slate-500">
          ECHO-AI only remembers what you add here. You can delete anything at any time.
        </p>
        <form onSubmit={addMemory} className="mt-3 flex gap-2">
          <input value={draft} onChange={(e) => setDraft(e.target.value)} maxLength={500}
            disabled={!settings.memory_enabled}
            placeholder={settings.memory_enabled ? "e.g. My exams are in December" : "Memory is off"}
            className="flex-1 rounded-lg border border-slate-300 bg-transparent px-3 py-2 dark:border-slate-700" />
          <button disabled={!settings.memory_enabled || !draft.trim()}
            className="rounded-lg bg-indigo-600 px-4 text-white disabled:opacity-40">Add</button>
        </form>
        <ul className="mt-3 divide-y divide-slate-200 dark:divide-slate-800">
          {memories.map((m) => (
            <li key={m.id} className="flex items-center justify-between gap-4 py-2 text-sm">
              <span>{m.content}</span>
              <button onClick={() => removeMemory(m.id)} className="text-rose-600 hover:underline">
                Delete
              </button>
            </li>
          ))}
          {memories.length === 0 && <li className="py-2 text-sm text-slate-500">Nothing saved.</li>}
        </ul>
      </section>
    </div>
  );
}
