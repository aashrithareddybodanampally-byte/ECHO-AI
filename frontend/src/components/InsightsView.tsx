import { useEffect, useState } from "react";
import { api } from "../api";
import type { Analytics } from "../types";

export function InsightsView({ statsEnabled }: { statsEnabled: boolean }) {
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.analytics().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="p-6 text-red-600">{error}</p>;
  if (!data) return <p className="p-6 text-slate-500">Loading…</p>;

  const entries = Object.entries(data.emotion_distribution).sort((a, b) => b[1] - a[1]);
  const total = entries.reduce((sum, [, n]) => sum + n, 0);
  const feedbackTotal = data.feedback.helpful + data.feedback.not_helpful;

  return (
    <div className="mx-auto max-w-2xl space-y-8 p-6">
      <section>
        <h2 className="text-lg font-semibold">Emotion trends</h2>
        <p className="mt-1 text-sm text-slate-500">
          How your messages were classified. These are model predictions, not clinical measurements.
        </p>
        {!statsEnabled && (
          <p className="mt-3 rounded-lg bg-slate-100 p-3 text-sm dark:bg-slate-800">
            Saving emotional statistics is off. Turn it on in Settings to see trends here.
          </p>
        )}
        {total === 0 ? (
          <p className="mt-4 text-sm text-slate-500">No saved predictions yet.</p>
        ) : (
          <ul className="mt-4 space-y-2">
            {entries.map(([state, count]) => (
              <li key={state} className="grid grid-cols-[6rem_1fr_3rem] items-center gap-3 text-sm">
                <span className="capitalize">{state}</span>
                <span className="h-3 rounded-full bg-slate-200 dark:bg-slate-800">
                  <span
                    className="block h-3 rounded-full bg-indigo-500"
                    style={{ width: `${(count / total) * 100}%` }}
                  />
                </span>
                <span className="text-right tabular-nums text-slate-500">{count}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section>
        <h2 className="text-lg font-semibold">Feedback</h2>
        {feedbackTotal === 0 ? (
          <p className="mt-2 text-sm text-slate-500">No feedback given yet.</p>
        ) : (
          <p className="mt-2 text-sm">
            {data.feedback.helpful} of {feedbackTotal} rated replies were marked helpful (
            {Math.round((data.feedback.helpful / feedbackTotal) * 100)}%).
          </p>
        )}
      </section>
    </div>
  );
}
