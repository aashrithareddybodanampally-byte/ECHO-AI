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

| Phase | Scope | Status |
|---|---|---|
| 1 | Development environment & repository foundation | ✅ Completed |
| 2.1 | Backend foundation | ✅ Completed |
| 2.2 | Database foundation | ✅ Completed |
| 2.3 | Domain models | ✅ Completed |
| 2.4 | Authentication | ✅ Completed |
| 2.5 | API contracts & service interfaces | 🔍 Implemented, PR open against `develop`, awaiting review |
| 2.6 | Audio preprocessing | ⏭️ Next — spec proposed, not started |
| 2.7 | Audio feature extraction | 🔮 Planned |

Details, branches and PRs: [`docs/phases/README.md`](docs/phases/README.md).

### Implemented (and covered by the backend test suite)

- **Backend** (`backend/`): FastAPI app, environment-based settings, logging, global error handling, `GET /api/v1/health`.
- **Database**: SQLAlchemy 2.x engine/session, PostgreSQL configuration via `DATABASE_URL`, Alembic migrations, `GET /api/v1/health/db`.
- **Domain models**: `User`, `Conversation`, `Message` with ownership relationships.
- **Authentication**: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me` (bcrypt password hashing, HS256 JWT).
- **API contracts (Phase 2.5)**: schemas and service interfaces for emotion analysis, fusion, retrieval, chat, feedback, history and analytics. These endpoints authenticate and validate input but return **`501 Not Implemented`** — no functionality behind them exists yet. See [`docs/api/CONTRACTS.md`](docs/api/CONTRACTS.md).
- **Audio upload limit**: 25 MB, configurable via `MAX_AUDIO_UPLOAD_BYTES`.

Testing note: the backend tests use SQLite in-memory databases, mocked
sessions and dependency overrides. Migrations and queries have **not** been
tested against a live PostgreSQL instance in the automated suite.

### Not Implemented

- Audio preprocessing, feature extraction, emotion models (voice or text)
- Speech-to-text, NLP, multimodal fusion
- Conversation context engine, short/long-term memory
- RAG, embeddings, vector database
- LLM integration
- Safety guardrails
- Conversation history, feedback and analytics logic (contracts only)
- Frontend application
- Docker, CI/CD, deployment, monitoring, MLOps

---

## Future Modules

| Module | Directory | Description |
|---|---|---|
| **Frontend** | `frontend/` | React + Vite web application for the chat interface |
| **Backend** | `backend/` | FastAPI REST/WebSocket API server (foundation implemented) |
| **Database** | `backend/alembic/` | PostgreSQL schema managed with Alembic migrations |
| **Audio ML** | `ml/audio/` | Audio preprocessing (Phase 2.6), feature extraction (Phase 2.7), speech emotion recognition |
| **NLP** | `ml/nlp/` | Text analysis, sentiment, intent classification |
| **Speech-to-Text** | `ml/audio/` | Transcription (provider/model not yet selected) |
| **Multimodal Fusion** | `ml/models/` | Combining audio + text signals |
| **Memory** | `backend/` | Conversation context & user-approved memory |
| **RAG** | `rag/` | Document ingestion, embeddings, vector retrieval |
| **LLM** | `backend/` | LLM API integration behind a provider-agnostic interface |
| **Safety** | `safety/` | Input/output guardrails, high-risk handling |
| **Analytics** | `backend/` | Usage metrics, conversation quality tracking |
| **Testing** | `backend/tests/`, `tests/` | Unit, integration, and end-to-end tests |
| **Infrastructure** | `infrastructure/` | Docker, CI/CD, monitoring, deployment |
| **MLOps** | `infrastructure/` | Model versioning, experiment tracking, monitoring |

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

Of this diagram, only the Backend API (authentication, health) and the
Database layer are implemented. The backend talks to every other component
only through the service interfaces defined in Phase 2.5.

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

The following must not be implemented until their phase is explicitly defined
and approved:

- AI/ML model training or inference (audio preprocessing is next, in Phase 2.6)
- LLM API calls
- RAG / vector database setup
- Safety guardrail logic
- Frontend application code
- Docker containerization, CI/CD execution, production deployment
- Real-time audio processing / streaming
