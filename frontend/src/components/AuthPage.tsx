import { useState, type FormEvent } from "react";
import { api, setToken } from "../api";
import { routeHref } from "../route";
import { Logo } from "./Logo";

interface Props {
  mode: "signin" | "signup";
  onAuthenticated: () => void;
}

const COPY = {
  signin: { title: "Welcome back", subtitle: "Sign in to continue your conversations.", button: "Sign in",
            switchText: "New to ECHO-AI?", switchLabel: "Create an account", switchTo: "signup" as const },
  signup: { title: "Create your account", subtitle: "Start talking with ECHO-AI in under a minute.", button: "Create account",
            switchText: "Already have an account?", switchLabel: "Sign in", switchTo: "signin" as const },
};

export function AuthPage({ mode, onAuthenticated }: Props) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const copy = COPY[mode];

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "signup") await api.register(email, password);
      const { access_token } = await api.login(email, password);
      setToken(access_token);
      onAuthenticated();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const input =
    "mt-1.5 w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2.5 text-white placeholder:text-slate-500 " +
    "focus:border-indigo-400/60 focus:outline-none focus:ring-2 focus:ring-indigo-500/30";

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-12">
      <div className="glow -top-32 left-1/2 h-96 w-[36rem] -translate-x-1/2 bg-indigo-600" />
      <div className="relative w-full max-w-sm">
        <a href={routeHref("home")} className="mb-8 flex justify-center" aria-label="Back to home"><Logo /></a>
        <div className="card-outline p-7 shadow-2xl shadow-indigo-950/60">
          <h1 className="text-2xl font-semibold tracking-tight text-white">{copy.title}</h1>
          <p className="mt-1 text-sm text-slate-400">{copy.subtitle}</p>
          <form onSubmit={submit} className="mt-6 space-y-4">
            <label className="block text-sm text-slate-300">
              Email
              <input type="email" required autoComplete="email" value={email}
                onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" className={input} />
            </label>
            <label className="block text-sm text-slate-300">
              Password
              <input type="password" required minLength={8}
                autoComplete={mode === "signin" ? "current-password" : "new-password"}
                value={password} onChange={(e) => setPassword(e.target.value)}
                placeholder={mode === "signup" ? "At least 8 characters" : ""} className={input} />
            </label>
            {error && <p className="rounded-lg bg-rose-500/10 px-3 py-2 text-sm text-rose-300">{error}</p>}
            <button disabled={busy}
              className="w-full rounded-lg bg-indigo-500 py-2.5 font-medium text-white shadow-lg shadow-indigo-500/25 hover:bg-indigo-400 disabled:opacity-50">
              {busy ? "Please wait…" : copy.button}
            </button>
          </form>
        </div>
        <p className="mt-6 text-center text-sm text-slate-400">
          {copy.switchText}{" "}
          <a href={routeHref(copy.switchTo)} className="font-medium text-indigo-300 hover:text-indigo-200">{copy.switchLabel}</a>
        </p>
        <p className="mt-8 text-center text-xs text-slate-500">
          ECHO-AI is not a medical service and cannot diagnose or provide crisis care.
        </p>
      </div>
    </main>
  );
}
