import type { FusionResult } from "../types";

const COLORS: Record<string, string> = {
  happy: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
  surprised: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
  calm: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200",
  neutral: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  sad: "bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-200",
  fearful: "bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-200",
  angry: "bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200",
  disgust: "bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200",
};

export function EmotionBadge({ emotion }: { emotion: FusionResult }) {
  const { voice, text, face, context } = emotion.signals;
  const parts = [
    voice !== null && `voice ${Math.round(voice * 100)}%`,
    text !== null && `text ${Math.round(text * 100)}%`,
    face != null && `face ${Math.round(face * 100)}%`,
    context !== null && `context ${Math.round(context * 100)}%`,
  ].filter(Boolean);
  return (
    <span
      title={`Model prediction, not a diagnosis. Signals: ${parts.join(", ")}`}
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ${COLORS[emotion.state] ?? COLORS.neutral}`}
    >
      {emotion.state} · {Math.round(emotion.confidence * 100)}%
    </span>
  );
}
