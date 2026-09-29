# ECHO-AI — Architecture

> This document describes the **planned** high-level architecture of ECHO-AI.
> All components below are implemented on `feature/echo-ai-completion` except where noted.
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
- **Status**: ✅ Implemented (React + Vite + TypeScript + Tailwind). Communication is REST only; WebSocket streaming is not implemented.

### Backend API
- **Technology**: Python + FastAPI
- **Responsibility**: API gateway, request routing, session management, response orchestration
- **Key Services**:
  - Authentication & Authorization (✅ implemented, Phase 2.4)
  - Session Manager
  - Conversation Manager
  - Memory Service (user-approved persistent context)
  - Response Orchestrator (coordinates ML, RAG, LLM, Safety)
- **Status**: ✅ Implemented. The Response Orchestrator is `backend/app/services/chat_service.py`; see [`docs/api/CONTRACTS.md`](../api/CONTRACTS.md).

### Database
- **Technology**: PostgreSQL
- **Responsibility**: Persistent storage for users, sessions, conversations, preferences
- **Status**: ✅ Implemented: `users` (+ privacy preferences), `conversations`, `messages`, `memories`, `feedback`, `analysis_results` via Alembic. Migrations are rendered offline in testing; not executed against live PostgreSQL in the automated suite.

### ML Pipeline
- **Technology**: Python, scikit-learn, librosa, Transformers
- **Sub-modules**:
  - **Audio**: Speech-to-text (Whisper), emotion detection, audio feature extraction
  - **NLP**: Sentiment analysis, intent classification, entity extraction
  - **Fusion**: Multimodal signal combination
- **Status**: ✅ Implemented: preprocessing, features, RAVDESS-trained Random Forest (see [`docs/ml/VOICE-EMOTION-MODEL.md`](../ml/VOICE-EMOTION-MODEL.md)), faster-whisper STT, VADER + lexicon text emotion, weighted late fusion. Intent/entity extraction is not implemented.

### RAG System
- **Technology**: Embeddings model + Vector database
- **Sub-modules**:
  - **Ingestion**: Document processing and chunking
  - **Embeddings**: Vector generation
  - **Retrieval**: Similarity search for relevant context
- **Status**: ✅ Implemented with TF-IDF over an original knowledge base (`rag/knowledge_base/`); no embeddings or vector database.

### Safety & Guardrails
- **Responsibility**: Content filtering, harmful content detection, bias mitigation, output validation
- **Status**: ✅ Implemented: rule-based input classifier, output guardrail, crisis protocol that bypasses the LLM. Bias detection is not implemented.

### LLM Integration
- **Technology**: API-based LLM: Groq (open models) or Anthropic (Claude)
- **Responsibility**: Response generation grounded in conversation context, ML analysis, and RAG results
- **Status**: ✅ Implemented: Groq (`openai/gpt-oss-120b`, Groq SDK) or Claude (`claude-opus-5-5`, Anthropic SDK), selected by `LLM_PROVIDER`, with a labeled offline template fallback.

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
| Backend API, database, authentication | ✅ Implemented |
| ML pipeline (audio, STT, text, fusion) | ✅ Implemented |
| Conversation pipeline (context, memory, policy, LLM, RAG, safety) | ✅ Implemented |
| Feedback, analytics, privacy settings | ✅ Implemented |
| Frontend | ✅ Implemented |
| Docker, Compose, CI | ⚠️ Written, not validated |
| Streaming, multilingual, MLOps monitoring | ❌ Not implemented |
