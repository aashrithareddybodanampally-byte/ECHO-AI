# ECHO-AI — Implementation Phases

Status reflects verified Git history and test runs. "Merged" means merged
through a reviewed PR; "Implemented" means code and passing tests exist on the
named branch but it has not been merged yet.

## History (Phases 1 – 2.5)

| Phase | Scope | Status | Branch / PR |
|---|---|---|---|
| 1 | Development environment & repository foundation | ✅ Merged | `965fc32` |
| 2.1 | Backend foundation | ✅ Merged | PR #1 |
| 2.2 | Database foundation | ✅ Merged | PR #2 |
| 2.3 | Domain models | ✅ Merged | PR #3 |
| 2.4 | Authentication | ✅ Merged | PR #4 |
| 2.5 | API contracts, service interfaces, 25 MB upload limit | ✅ Implemented, PR open against `develop` | `feature/phase2-contracts` |

PRs #1–#4 were merged into `main` and then merged back into `develop`.

## Completion plan (Phase 3)

On 2026-09-29 the project owner delegated technical decisions to the coding
agent and asked for the project to be completed. The previous step-by-step
plan (one approved phase at a time) was replaced by this plan, implemented on
`feature/echo-ai-completion` (stacked on `feature/phase2-contracts`).

| Step | Scope | Status |
|---|---|---|
| 3.1 | Audio preprocessing (spec: [`PHASE-2.6-AUDIO-PREPROCESSING.md`](PHASE-2.6-AUDIO-PREPROCESSING.md), defaults as proposed) | ✅ Implemented, tested |
| 3.2 | Audio feature extraction (MFCC, chroma, spectral centroid/bandwidth, ZCR, RMS) | ✅ Implemented, tested |
| 3.3 | Voice emotion model: RAVDESS, speaker-independent split, SVM vs Random Forest, metrics, artifact | ✅ Trained — see [`docs/ml/VOICE-EMOTION-MODEL.md`](../ml/VOICE-EMOTION-MODEL.md) |
| 3.4 | Speech-to-text (faster-whisper, local) and text sentiment/emotion (VADER + lexicon) | ✅ Implemented |
| 3.5 | Multimodal fusion (weighted late fusion) | ✅ Implemented, tested |
| 3.6 | Conversation pipeline: context window, user-approved memory, response policy, LLM (Groq or Claude + labeled offline fallback), RAG (TF-IDF + sources), input/output safety, crisis protocol | ✅ Implemented, tested |
| 3.7 | Feedback, analytics, privacy settings (emotion statistics opt-in) | ✅ Implemented, tested |
| 3.8 | Frontend (React + Vite + TypeScript + Tailwind): auth, text/voice chat, emotion, sources, feedback, TTS, history, insights, memory & settings | ✅ Implemented, built, exercised in a browser |
| 3.9 | Docker, Docker Compose, GitHub Actions CI | ⚠️ Written, **not validated** (Docker is not installed on the development machine; CI has not run yet) |

### Key decisions

| Decision | Choice | Why |
|---|---|---|
| Audio format | WAV/FLAC only; the browser converts recordings to WAV | No ffmpeg dependency |
| Voice dataset | RAVDESS speech (CC BY-NC-SA 4.0, non-commercial) | Standard, labeled, 24 speakers enable a speaker-independent test set |
| Text emotion | VADER + transparent keyword lexicon | No torch/transformer download; deterministic and testable. Heuristic, not a trained model |
| RAG | TF-IDF over an original curated knowledge base, no vector DB | Small corpus; avoids infrastructure and licensing issues |
| LLM | Groq (`openai/gpt-oss-120b`) or Claude (`claude-opus-5-5`) behind `LLMService`; labeled offline template fallback | Groq added at the owner's request (preferred provider); works without a key; never pretends the fallback is an LLM |
| TTS | Browser `speechSynthesis` | No server-side model or cost |
| Safety | Rule-based classifier + output guardrail + fixed crisis protocol that bypasses the LLM | Deterministic, testable, conservative |
| Privacy | Raw audio never stored; emotion statistics opt-in; memory only from explicit user entries | Explicit rather than accidental privacy decisions |

### Not implemented (deliberately out of scope)

Real-time streaming/WebSockets, multilingual support, learned fusion,
transformer-based text emotion, grounding/hallucination verification,
drift monitoring, experiment tracking, A/B testing, production deployment.

## Workflow

```
develop ──> feature/<phase-or-feature> ──> tests + review ──> PR into develop ──> human review ──> merge
```

- Run `cd backend && pytest`, `pytest tests` (repo root) and `cd frontend && npm test && npm run build` before opening a PR.
- Agents open PRs but do not merge them.
