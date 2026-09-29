# PROJECT-CONTEXT.md — ECHO-AI

---

## Project Name

**ECHO-AI**

## Purpose

ECHO-AI is a **multimodal conversational AI system** designed to:

- Process **text** and **voice** input simultaneously
- Analyze speech characteristics (emotion, tone, cadence) and text semantics
- Maintain **conversational context** across sessions
- Store **user-approved memory** for personalized interactions
- Retrieve relevant information using **Retrieval-Augmented Generation (RAG)**
- Generate responses through an **LLM** with grounding in retrieved data
- Apply **safety controls and guardrails** to all outputs
- Provide **analytics** on conversation quality, user satisfaction, and system performance

Emotion and sentiment outputs are model predictions, never clinical or
psychological diagnoses.

---

## Current Status

Phases 1 and 2.1-2.4 are merged. Phase 2.5 (API contracts) has a PR open
against `develop`. The rest of the product was implemented under the
completion plan in [`docs/phases/README.md`](docs/phases/README.md) on
`feature/echo-ai-completion`, after the project owner delegated technical
decisions to the coding agent (2026-09-29).

### Implemented (covered by automated tests unless noted)

- **Backend** (`backend/`): FastAPI, settings, logging, error handling, health checks, CORS.
- **Database**: SQLAlchemy 2.x, PostgreSQL via Alembic (SQLite for local development). Models: User (+ privacy preferences), Conversation, Message, Memory, Feedback, AnalysisResult.
- **Authentication**: register, login, JWT (HS256), bcrypt; per-user ownership enforced on every resource.
- **Audio ML** (`ml/audio`, `ml/training`, `ml/inference`): preprocessing, 100-dim features, RAVDESS training with SVM vs Random Forest, inference. Speaker-independent test accuracy 0.458 / macro-F1 0.453 (8 classes): [`docs/ml/VOICE-EMOTION-MODEL.md`](docs/ml/VOICE-EMOTION-MODEL.md).
- **Speech-to-text**: faster-whisper `base`, local CPU. Verified manually with real speech; not in automated tests (model download).
- **Text analysis** (`ml/nlp`): VADER sentiment + keyword emotion lexicon (heuristic, uncalibrated).
- **Fusion** (`ml/models`): weighted late fusion of voice, text, optional facial expression and previous-turn context.
- **Camera expression (opt-in)**: facial expression estimated in the browser with `@vladmandic/face-api` (MIT); only a label and confidence are sent, never video. Not covered by automated tests with a real camera.
- **Counseling-style responses**: prompt built around reflective listening, one exploratory question, past-session and mood-history context, tailored evidence-based techniques; no diagnosis or medication advice; referrals only for hopelessness/worthlessness language or on request.
- **Conversation pipeline**: context window, user-approved memory, response policy, LLM (Groq or Claude behind `LLMService`; labeled offline fallback), RAG with cited sources, input/output safety, crisis protocol.
- **RAG** (`rag/`): original knowledge base, Markdown chunking, TF-IDF retrieval.
- **Safety** (`safety/`): rule-based input classifier (normal/distress/high-risk), output guardrail.
- **Feedback, analytics, privacy settings**: emotion statistics are opt-in; raw audio is never stored.
- **Frontend** (`frontend/`): React + Vite + TypeScript + Tailwind; text and voice chat, emotion display, sources, feedback, browser TTS, history, insights, memory & settings.
- **Infrastructure**: Dockerfiles, docker-compose, GitHub Actions CI, **written but not validated**.

Not exercised by the automated suite: live LLM provider calls (Groq/Claude; tested with fake clients), live
PostgreSQL migrations (rendered offline only), Whisper transcription.

### Not Implemented

- Real-time streaming / WebSockets
- Multilingual support
- Grounding / hallucination verification beyond showing sources
- Learned fusion; transformer-based text emotion
- Drift monitoring, experiment tracking, A/B testing
- Production deployment

---

## Future Modules

| Module | Directory | Description |
|---|---|---|
| **Frontend** | `frontend/` | React + Vite web application (implemented) |
| **Backend** | `backend/` | FastAPI REST API and conversation pipeline (implemented) |
| **Database** | `backend/alembic/` | PostgreSQL schema managed with Alembic migrations (implemented) |
| **Audio ML** | `ml/audio/`, `ml/training/`, `ml/inference/` | Preprocessing, features, voice emotion model (implemented) |
| **NLP** | `ml/nlp/` | Text sentiment and emotion (implemented, heuristic) |
| **Speech-to-Text** | `ml/audio/` | faster-whisper transcription (implemented) |
| **Multimodal Fusion** | `ml/models/` | Weighted late fusion (implemented) |
| **Memory** | `backend/` | Context window & user-approved memory (implemented) |
| **RAG** | `rag/` | Knowledge base, chunking, TF-IDF retrieval (implemented) |
| **LLM** | `backend/app/services/llm.py` | Groq or Claude behind `LLMService` (implemented) |
| **Safety** | `safety/` | Input/output guardrails, crisis protocol (implemented) |
| **Analytics** | `backend/` | Emotion distribution, feedback, per-request timings (implemented) |
| **Testing** | `backend/tests/`, `tests/`, `frontend/src/*.test.ts` | Unit, integration and pipeline tests (implemented) |
| **Infrastructure** | `infrastructure/`, `docker-compose.yml`, `.github/` | Docker, Compose, CI (not validated) |
| **MLOps** | `ml/training/`, `ml/evaluation/` | Versioned artifact, metrics.json, latency benchmark (tracking/monitoring not implemented) |

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                     Frontend                         │
│              (React + Vite + Tailwind)               │
└──────────────────────┬──────────────────────────────┘
                       │ REST / WebSocket
                       ▼
┌─────────────────────────────────────────────────────┐
│                   Backend API                        │
│                    (FastAPI)                          │
├──────────────────────┬──────────────────────────────┤
│  Authentication      │  Conversation Manager         │
│  Session Management  │  Memory Service               │
│  Analytics           │  Response Orchestrator         │
└──────────┬───────────┴──────────┬───────────────────┘
           │                      │
     ┌─────┴─────┐         ┌─────┴─────┐
     ▼           ▼         ▼           ▼
┌─────────┐ ┌────────┐ ┌───────┐ ┌─────────┐
│   ML    │ │Database│ │  RAG  │ │ Safety  │
│Pipeline │ │(Postgres│ │System │ │Guardrails│
├─────────┤ │)       │ ├───────┤ └─────────┘
│ Audio   │ └────────┘ │Ingest │
│ NLP     │            │Embed  │
│ Fusion  │            │Retrieve│
└────┬────┘            └───┬───┘
     │                     │
     └──────────┬──────────┘
                ▼
         ┌────────────┐
         │    LLM     │
         │  (API)     │
         └──────┬─────┘
                ▼
         ┌────────────┐
         │  Response   │
         └────────────┘
```

All components in this diagram are implemented (RAG uses TF-IDF rather than
a vector database). The backend talks to the ML, RAG, safety and LLM
components only through the service interfaces in
`backend/app/services/interfaces.py`.

### Data Flow (target)

1. **User** sends text/voice input via the **Frontend**
2. **Backend** receives the request, routes to processing pipelines
3. **ML Pipeline** analyzes audio (emotion, features) and text (sentiment, intent)
4. **RAG System** retrieves relevant context from the vector database
5. **LLM** generates a response grounded in ML analysis, RAG context, and conversation history
6. **Safety** module filters the response for harmful content
7. **Backend** returns the final response to the **Frontend**

---

## Currently Out of Scope

See "Not Implemented" above. Any of these needs an explicit decision before
work starts.
