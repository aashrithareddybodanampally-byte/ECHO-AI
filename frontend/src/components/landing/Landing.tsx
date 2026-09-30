import { routeHref } from "../../route";
import { Logo } from "../Logo";

const STEPS = [
  { title: "Listen", text: "Speak or type. Audio is cleaned up, transcribed on the server and never stored." },
  { title: "Understand", text: "Vocal tone and your words are analyzed separately, then combined with the conversation so far." },
  { title: "Recall", text: "Recent messages, and only the facts you chose to save, give the reply its context." },
  { title: "Ground", text: "Relevant notes from a curated knowledge base are retrieved and cited alongside the answer." },
  { title: "Respond safely", text: "Every message and reply passes safety checks before you see it." },
];

const FEATURES = [
  { icon: "🎙", title: "Voice & text", text: "Talk naturally or type. Replies can be read aloud in your browser." },
  { icon: "🌊", title: "Tone-aware", text: "A voice model and a text analyzer estimate how you might be feeling, shown as a prediction, never a diagnosis." },
  { icon: "🧠", title: "Memory you control", text: "Save only what you want remembered. View, delete or switch it off at any time." },
  { icon: "📚", title: "Cited sources", text: "Study, sleep and wellbeing suggestions come with the notes they were based on." },
  { icon: "🛡", title: "Safety first", text: "Distress gets a gentler reply; crisis messages get helplines and human support options immediately." },
  { icon: "📈", title: "Your insights", text: "Opt in to see how your conversations have felt over time, and rate every reply." },
];

function Header() {
  return (
    <header className="absolute inset-x-0 top-0 z-30">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5 sm:px-6">
        <a href={routeHref("home")} aria-label="ECHO-AI home"><Logo /></a>
        <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex">
          <a href="#how" className="hover:text-white">How it works</a>
          <a href="#features" className="hover:text-white">Features</a>
          <a href="#privacy" className="hover:text-white">Privacy & safety</a>
        </nav>
        <div className="flex items-center gap-2 text-sm">
          <a href={routeHref("signin")} className="rounded-lg px-3 py-2 text-slate-300 hover:text-white">Sign in</a>
          <a href={routeHref("signup")}
            className="rounded-lg bg-indigo-500 px-4 py-2 font-medium text-white shadow-lg shadow-indigo-500/25 hover:bg-indigo-400">
            Get started
          </a>
        </div>
      </div>
    </header>
  );
}

function Waveform() {
  const heights = [30, 55, 80, 45, 95, 60, 35, 70, 100, 50, 75, 40, 85, 55, 30, 65, 45, 25];
  return (
    <div className="flex h-24 items-center justify-center gap-1.5" aria-hidden="true">
      {heights.map((h, i) => (
        <span key={i} className="wave-bar w-1.5 rounded-full bg-gradient-to-b from-indigo-300 to-cyan-400"
          style={{ height: `${h}%`, animationDelay: `${(i % 6) * 0.12}s` }} />
      ))}
    </div>
  );
}

function SignalPreview() {
  return (
    <div className="card-outline mx-auto mt-14 max-w-xl p-6 text-left shadow-2xl shadow-indigo-950/60">
      <div className="mb-4 flex items-center justify-between text-xs text-slate-400">
        <span className="rounded-full bg-white/5 px-2 py-0.5">Illustration</span>
        <span>What ECHO-AI considers for one message</span>
      </div>
      <Waveform />
      <p className="mt-4 text-sm text-slate-200">“I've been studying for hours and I can't remember anything.”</p>
      <ul className="mt-4 grid grid-cols-3 gap-2 text-xs">
        {[["Voice", "tone of speech"], ["Words", "sentiment & emotion"], ["Context", "earlier messages"]].map(([name, hint]) => (
          <li key={name} className="rounded-lg border border-white/5 bg-white/[0.03] p-2">
            <span className="block font-medium text-indigo-200">{name}</span>
            <span className="text-slate-400">{hint}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden pt-36 pb-20 sm:pt-44">
      <div className="glow -top-40 left-1/2 h-[28rem] w-[40rem] -translate-x-1/2 bg-indigo-600" />
      <div className="glow top-40 -right-40 h-72 w-72 bg-cyan-500/70" />
      <div className="relative mx-auto max-w-4xl px-4 text-center sm:px-6">
        <p className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-indigo-400/20 bg-indigo-400/10 px-3 py-1 text-xs text-indigo-200">
          Voice + text · context-aware · safety-first
        </p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-6xl">
          <span className="text-gradient">An assistant that hears</span>
          <br />
          <span className="text-white">how you're really doing</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-400">
          ECHO-AI listens to what you say and how you say it, remembers only what you allow,
          and answers with care, grounded in trusted notes and checked for safety.
        </p>
        <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <a href={routeHref("signup")}
            className="w-full rounded-xl bg-indigo-500 px-6 py-3 font-medium text-white shadow-lg shadow-indigo-500/30 hover:bg-indigo-400 sm:w-auto">
            Start a conversation
          </a>
          <a href="#how" className="w-full rounded-xl border border-white/10 bg-white/5 px-6 py-3 font-medium text-slate-200 hover:bg-white/10 sm:w-auto">
            See how it works
          </a>
        </div>
        <SignalPreview />
      </div>
    </section>
  );
}

function HowItWorks() {
  return (
    <section id="how" className="relative mx-auto max-w-6xl scroll-mt-20 px-4 py-20 sm:px-6">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">How ECHO-AI listens</h2>
        <p className="mt-4 text-slate-400">Every message, spoken or typed, goes through the same five steps.</p>
      </div>
      <ol className="mt-14 grid gap-4 md:grid-cols-5">
        {STEPS.map((step, i) => (
          <li key={step.title} className="card-outline p-5">
            <span className="text-gradient text-sm font-semibold">0{i + 1}</span>
            <h3 className="mt-2 font-semibold text-white">{step.title}</h3>
            <p className="mt-2 text-sm text-slate-400">{step.text}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

function Features() {
  return (
    <section id="features" className="relative scroll-mt-20 overflow-hidden py-20">
      <div className="glow top-10 -left-40 h-80 w-80 bg-indigo-700" />
      <div className="relative mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">More than a chatbot</h2>
          <p className="mt-4 text-slate-400">Built around understanding, not just answering.</p>
        </div>
        <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <article key={f.title} className="rounded-2xl border border-white/5 bg-white/[0.03] p-6 transition hover:border-indigo-400/30 hover:bg-white/[0.05]">
              <span className="text-2xl" aria-hidden="true">{f.icon}</span>
              <h3 className="mt-3 font-semibold text-white">{f.title}</h3>
              <p className="mt-2 text-sm text-slate-400">{f.text}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function Privacy() {
  const points = [
    "Raw audio is processed in memory and never stored.",
    "Emotion statistics are off until you turn them on.",
    "Memory holds only facts you add yourself, and you can delete them.",
    "Conversations can be deleted permanently from your history.",
  ];
  return (
    <section id="privacy" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-20 sm:px-6">
      <div className="card-outline grid gap-10 p-8 md:grid-cols-2 md:p-12">
        <div>
          <h2 className="text-3xl font-semibold tracking-tight text-white">Private by default. Careful by design.</h2>
          <p className="mt-4 text-slate-400">
            ECHO-AI is not a doctor or therapist. It never diagnoses, never gives medication advice,
            and treats its emotion estimates as predictions that can be wrong.
          </p>
          <p className="mt-4 text-sm text-slate-400">
            If a message suggests someone may be at risk, ECHO-AI immediately shares helplines and
            encourages reaching out to a real person.
          </p>
        </div>
        <ul className="space-y-3">
          {points.map((p) => (
            <li key={p} className="flex gap-3 rounded-xl border border-white/5 bg-white/[0.03] p-4 text-sm text-slate-300">
              <span className="text-cyan-300" aria-hidden="true">✓</span>
              {p}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function CallToAction() {
  return (
    <section className="relative overflow-hidden py-24 text-center">
      <div className="glow bottom-0 left-1/2 h-72 w-[36rem] -translate-x-1/2 bg-indigo-600" />
      <div className="relative mx-auto max-w-2xl px-4">
        <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          <span className="text-gradient">Ready when you are.</span>
        </h2>
        <p className="mt-4 text-slate-400">Create a free account and say hello, by voice or by text.</p>
        <a href={routeHref("signup")}
          className="mt-8 inline-block rounded-xl bg-indigo-500 px-6 py-3 font-medium text-white shadow-lg shadow-indigo-500/30 hover:bg-indigo-400">
          Create your account
        </a>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-white/5">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-10 text-sm text-slate-500 sm:px-6 md:flex-row md:items-center md:justify-between">
        <Logo />
        <p className="max-w-xl md:text-right">
          ECHO-AI is not a medical service. In an emergency, contact local emergency services.
          India: Tele-MANAS 14416 · US & Canada: 988 · Elsewhere: findahelpline.com
        </p>
      </div>
    </footer>
  );
}

export function Landing() {
  return (
    <div className="min-h-screen overflow-x-hidden">
      <Header />
      <main>
        <Hero />
        <HowItWorks />
        <Features />
        <Privacy />
        <CallToAction />
      </main>
      <Footer />
    </div>
  );
}
