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

---

## Current Status

### Phase 1 — Development Environment & Repository Foundation ✅ (In Progress)

Phase 1 establishes:

- Git repository and branching strategy
- Project directory structure
- Environment variable strategy
- Documentation foundation
- Agent instructions
- Development workflow documentation
- Validation tooling

### What Is NOT Implemented

- No backend API
- No frontend application
- No database schema
- No ML models or pipelines
- No RAG system
- No LLM integration
- No authentication
- No deployment infrastructure

---

## Future Modules

| Module | Directory | Description |
|---|---|---|
| **Frontend** | `frontend/` | React + Vite web application for the chat interface |
| **Backend** | `backend/` | FastAPI REST/WebSocket API server |
| **Database** | `database/` | PostgreSQL schemas, migrations, seed data |
| **Audio ML** | `ml/audio/` | Speech emotion recognition, audio feature extraction |
| **NLP** | `ml/nlp/` | Text analysis, sentiment, intent classification |
| **Speech-to-Text** | `ml/audio/` | Whisper-based transcription |
| **Multimodal Fusion** | `ml/models/` | Combining audio + text signals |
| **Memory** | `backend/` | Conversation context & user-approved memory |
| **RAG** | `rag/` | Document ingestion, embeddings, vector retrieval |
| **LLM** | `backend/` | LLM API integration for response generation |
| **Safety** | `safety/` | Content filtering, guardrails, bias detection |
| **Analytics** | `backend/` | Usage metrics, conversation quality tracking |
| **Testing** | `tests/` | Unit, integration, and end-to-end tests |
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

### Data Flow

1. **User** sends text/voice input via the **Frontend**
2. **Backend** receives the request, routes to processing pipelines
3. **ML Pipeline** analyzes audio (emotion, features) and text (sentiment, intent)
4. **RAG System** retrieves relevant context from the vector database
5. **LLM** generates a response grounded in ML analysis, RAG context, and conversation history
6. **Safety** module filters the response for harmful content
7. **Backend** returns the final response to the **Frontend**

---

## Currently Out of Scope

The following are explicitly **not** part of Phase 1 and must not be implemented until their respective phases:

- Actual AI/ML model training or inference
- LLM API calls
- Database schema creation
- Frontend application code
- Authentication system
- Docker containerization
- CI/CD pipeline execution
- Production deployment
- Real-time audio processing
- Vector database setup
