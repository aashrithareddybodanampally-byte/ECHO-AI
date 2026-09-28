# ECHO-AI — Architecture

> This document describes the **planned** high-level architecture of ECHO-AI.
> Implemented so far (Phases 2.1–2.5): the Backend API foundation (health, authentication),
> the Database layer, and contract-only service interfaces. Everything else is planned.
> Phase status: [`docs/phases/README.md`](../phases/README.md).

---

## System Overview

ECHO-AI is a multimodal conversational AI system composed of the following major subsystems:

```
┌───────────────────────────────────────────────────────────────┐
│                        FRONTEND                               │
│               React + Vite + Tailwind CSS                     │
│         Chat UI · Voice Capture · Analytics Dashboard          │
└──────────────────────────┬────────────────────────────────────┘
                           │  HTTP REST / WebSocket
                           ▼
┌───────────────────────────────────────────────────────────────┐
│                       BACKEND API                             │
│                      Python FastAPI                           │
├───────────┬──────────┬──────────┬──────────┬─────────────────┤
│   Auth    │ Session  │ Convo    │ Memory   │  Response       │
│  Service  │ Manager  │ Manager  │ Service  │  Orchestrator   │
└─────┬─────┴─────┬────┴─────┬────┴──────────┴────────┬────────┘
      │           │          │                         │
      ▼           ▼          ▼                         ▼
┌──────────┐ ┌─────────┐ ┌──────────────┐     ┌─────────────┐
│ Database │ │   ML    │ │     RAG      │     │   Safety    │
│ Postgres │ │Pipeline │ │   System     │     │ Guardrails  │
└──────────┘ ├─────────┤ ├──────────────┤     └─────────────┘
             │ Audio   │ │ Ingestion    │
             │  └ STT  │ │ Embeddings   │
             │  └ Emot.│ │ Retrieval    │
             │ NLP     │ └──────┬───────┘
             │  └ Sent. │        │
             │  └ Intent│        │
             │ Fusion   │        │
             └────┬─────┘        │
                  │              │
                  └──────┬───────┘
                         ▼
                  ┌────────────┐
                  │    LLM     │
                  │  (API)     │
                  └──────┬─────┘
                         ▼
                  ┌────────────┐
                  │  Response  │
                  └────────────┘
```

---

## Component Descriptions

### Frontend
- **Technology**: React + Vite + Tailwind CSS
- **Responsibility**: User interface for text/voice chat, settings, analytics
- **Communication**: REST and WebSocket connections to Backend API
- **Status**: 🔮 Planned (phase not yet defined)

### Backend API
- **Technology**: Python + FastAPI
- **Responsibility**: API gateway, request routing, session management, response orchestration
- **Key Services**:
  - Authentication & Authorization (✅ implemented, Phase 2.4)
  - Session Manager
  - Conversation Manager
  - Memory Service (user-approved persistent context)
  - Response Orchestrator (coordinates ML, RAG, LLM, Safety)
- **Status**: ✅ Foundation implemented (Phases 2.1–2.4); AI endpoints defined as contracts returning `501` (Phase 2.5, see [`docs/api/CONTRACTS.md`](../api/CONTRACTS.md)). Session, conversation, memory and orchestration services are not implemented.

### Database
- **Technology**: PostgreSQL
- **Responsibility**: Persistent storage for users, sessions, conversations, preferences
- **Status**: ✅ Implemented (Phases 2.2–2.4): SQLAlchemy models `users`, `conversations`, `messages` with Alembic migrations. Not yet exercised against live PostgreSQL in the automated test suite.

### ML Pipeline
- **Technology**: Python, scikit-learn, librosa, Transformers
- **Sub-modules**:
  - **Audio**: Speech-to-text (Whisper), emotion detection, audio feature extraction
  - **NLP**: Sentiment analysis, intent classification, entity extraction
  - **Fusion**: Multimodal signal combination
- **Status**: 🔮 Planned — audio preprocessing is Phase 2.6 (next), feature extraction Phase 2.7

### RAG System
- **Technology**: Embeddings model + Vector database
- **Sub-modules**:
  - **Ingestion**: Document processing and chunking
  - **Embeddings**: Vector generation
  - **Retrieval**: Similarity search for relevant context
- **Status**: 🔮 Planned (phase not yet defined; `RetrievalService` contract defined in Phase 2.5)

### Safety & Guardrails
- **Responsibility**: Content filtering, harmful content detection, bias mitigation, output validation
- **Status**: 🔮 Planned (phase not yet defined; `SafetyService` contract defined in Phase 2.5)

### LLM Integration
- **Technology**: API-based LLM (e.g., OpenAI, Anthropic)
- **Responsibility**: Response generation grounded in conversation context, ML analysis, and RAG results
- **Status**: 🔮 Planned (phase not yet defined; `LLMService` contract defined in Phase 2.5)

---

## Data Flow

1. **Input**: User sends text or voice via Frontend
2. **Transport**: Frontend sends request to Backend API (REST or WebSocket)
3. **Processing**: Backend routes to appropriate services:
   - Voice → ML Audio pipeline (STT + emotion analysis)
   - Text → ML NLP pipeline (sentiment + intent)
   - Both → RAG retrieval for relevant context
4. **Generation**: LLM receives ML analysis + RAG context + conversation history → generates response
5. **Safety**: Response passes through Safety guardrails
6. **Output**: Filtered response returned to Frontend

---

## Design Principles

1. **Loose coupling** — Each subsystem communicates through well-defined interfaces
2. **Independent deployability** — Components can be developed, tested, and scaled independently
3. **Configuration-driven** — Behavior controlled through environment variables, not code changes
4. **Graceful degradation** — System functions with reduced capability if optional components are unavailable
5. **Security by default** — No secrets in code, input validation, output filtering

---

## Currently Implemented

| Component | Status |
|---|---|
| Repository structure | ✅ Implemented |
| Documentation foundation | ✅ Implemented |
| Environment configuration | ✅ Implemented |
| Backend foundation & health checks | ✅ Implemented (2.1) |
| Database layer & migrations | ✅ Implemented (2.2, 2.3) |
| Authentication (JWT, bcrypt) | ✅ Implemented (2.4) |
| API contracts & service interfaces | 🔍 Implemented, in review (2.5) — endpoints return `501` |
| Everything else | 🔮 Planned |
