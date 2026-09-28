# ECHO-AI

> A multimodal AI conversational system that combines voice and text understanding for intelligent, context-aware interactions.

---

## Overview

ECHO-AI is a multimodal conversational AI platform designed to process both text and voice input, analyze speech and language characteristics, maintain conversation context and user memory, retrieve relevant information through RAG, generate LLM-powered responses, and enforce safety guardrails — all within a modular, production-ready architecture.

## Vision

Create a conversational AI system that truly *listens* — understanding not just the words, but the tone, emotion, and context behind them — to deliver responses that are accurate, personalized, and safe.

---

## Current Phase

### 🔍 Phase 2.5 — API Contracts & Service Interfaces (in review)

| Phase | Scope | Status |
|---|---|---|
| 1 | Development environment & repository foundation | ✅ Completed |
| 2.1 | Backend foundation (FastAPI, config, health) | ✅ Completed |
| 2.2 | Database foundation (SQLAlchemy, PostgreSQL config, Alembic) | ✅ Completed |
| 2.3 | Domain models (User, Conversation, Message) | ✅ Completed |
| 2.4 | Authentication (register, login, JWT) | ✅ Completed |
| 2.5 | API contracts & service interfaces | 🔍 PR open against `develop`, awaiting review |
| 2.6 | Audio preprocessing | ⏭️ Next — spec proposed, not started |
| 2.7 | Audio feature extraction | 🔮 Planned |

See [`docs/phases/README.md`](docs/phases/README.md) for details.

> **No AI/ML, speech, RAG, LLM or safety functionality has been implemented yet.** The AI endpoints defined in Phase 2.5 are contracts only and return `501 Not Implemented`.

---

## Planned Capabilities

Legend: ✅ implemented and tested · 📐 API contract defined, not implemented (returns `501`) · 🔮 planned

| Capability | Status | Description |
|---|---|---|
| User accounts & authentication | ✅ Implemented | Register, login, JWT-protected endpoints |
| Text conversation | 📐 Contract only | `POST /api/v1/chat` |
| Conversation history | 📐 Contract only | `GET /api/v1/history` |
| Voice input | 🔮 Planned | Microphone capture and audio upload (25 MB upload limit enforced) |
| Audio preprocessing | 🔮 Planned (Phase 2.6) | Resampling, normalization, silence removal |
| Speech-to-text | 🔮 Planned | Transcription (model not yet selected) |
| Voice emotion analysis | 📐 Contract only | `POST /api/v1/emotion/analyze` |
| Text/NLP analysis | 🔮 Planned | Sentiment and emotion (internal contract defined) |
| Multimodal fusion | 📐 Contract only | `POST /api/v1/emotion/fusion` |
| User memory | 🔮 Planned | Opt-in persistent user preferences |
| RAG | 📐 Contract only | `POST /api/v1/rag/retrieve` |
| LLM integration | 🔮 Planned | API-based response generation (internal contract defined) |
| Safety guardrails | 🔮 Planned | Input/output guardrails (internal contract defined) |
| Feedback | 📐 Contract only | `POST /api/v1/feedback` |
| Analytics | 📐 Contract only | `GET /api/v1/analytics` |

---

## Architecture

```
Frontend (React + Vite)
        │
        ▼
  Backend API (FastAPI)
        │
  ┌─────┼─────────┬──────────┐
  ▼     ▼         ▼          ▼
 ML   Database   RAG      Safety
  │              │
  └──────┬───────┘
         ▼
        LLM
         ▼
      Response
```

For detailed architecture documentation, see [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md).

---

## Technology Stack

| Layer | Technology | Status |
|---|---|---|
| Frontend | React + Vite + Tailwind CSS | 🔮 Planned |
| Backend | Python + FastAPI, Pydantic, PyJWT, bcrypt | ✅ In use |
| Database | PostgreSQL (SQLAlchemy 2.x, Alembic, psycopg) | ✅ Configured |
| ML | Python, scikit-learn, librosa, NumPy, pandas | 🔮 Planned |
| Speech | Whisper (or equivalent) | 🔮 Planned |
| NLP | Transformers / NLP tooling | 🔮 Planned |
| RAG | Embeddings + Vector DB | 🔮 Planned |
| LLM | API-based (e.g., OpenAI, Anthropic) | 🔮 Planned |
| Testing | Pytest (backend) | ✅ In use |
| Testing | Vitest/Jest (frontend) | 🔮 Planned |
| Infrastructure | Docker, Docker Compose, GitHub Actions | 🔮 Planned |

For detailed technology decisions, see [`docs/architecture/TECH-STACK.md`](docs/architecture/TECH-STACK.md).

---

## Repository Structure

```
ECHO-AI/
├── frontend/              # React + Vite frontend
├── backend/               # FastAPI backend
├── ml/                    # ML pipelines (audio, NLP, fusion)
│   ├── audio/
│   ├── nlp/
│   ├── models/
│   ├── training/
│   ├── inference/
│   └── evaluation/
├── rag/                   # RAG system
│   ├── ingestion/
│   ├── embeddings/
│   ├── retrieval/
│   └── evaluation/
├── safety/                # Safety & guardrails
├── database/              # DB schemas & migrations
├── tests/                 # All tests
│   ├── backend/
│   ├── frontend/
│   ├── ml/
│   ├── rag/
│   └── integration/
├── docs/                  # Documentation
├── scripts/               # Utility scripts
├── infrastructure/        # Docker, CI/CD
├── data/                  # Datasets (git-ignored)
├── models/                # Trained models (git-ignored)
├── logs/                  # Log output (git-ignored)
└── .github/workflows/     # GitHub Actions
```

---

## Development Roadmap

| Phase | Focus | Status |
|---|---|---|
| **Phase 1** | Development environment & repository foundation | ✅ Completed |
| **Phase 2.1–2.4** | Backend, database, domain models, authentication | ✅ Completed |
| **Phase 2.5** | API contracts & service interfaces | 🔍 In review |
| **Phase 2.6** | Audio preprocessing | ⏭️ Next |
| **Phase 2.7** | Audio feature extraction | 🔮 Planned |
| Later | Emotion models & inference, speech-to-text, NLP, fusion, context & memory, LLM, RAG, safety, frontend, feedback & analytics, deployment, MLOps | 🔮 Phases not yet defined |

Each phase is defined and approved before implementation starts. See [`docs/phases/README.md`](docs/phases/README.md).

---

## Local Development

### Prerequisites

- **Git** ≥ 2.30
- **Python** ≥ 3.10
- **Node.js** ≥ 18
- **npm** ≥ 9
- Docker & Docker Compose (optional, for containerized development)

### Getting Started

```bash
# Clone the repository
git clone <repository-url>
cd ECHO-AI

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# (the backend reads its own settings from backend/.env — see backend/.env.example)

# Run environment validation
# On Windows (PowerShell):
.\scripts\check_environment.ps1

# On Linux/macOS:
bash scripts/check_environment.sh
```

For backend setup (virtual environment, migrations, running the API), see
[`backend/README.md`](backend/README.md).

### Environment Variables

Copy `.env.example` to `.env` and fill in your values. **Never commit `.env` to version control.**

See `.env.example` for all available configuration options.

---

## Git Workflow

1. **`main`** — Stable branch. Protected.
2. **`develop`** — Integration branch for active development.
3. **Feature branches** — Branch from `develop`, open a PR into `develop`, merge after human review.

PRs #1–#4 (Phases 2.1–2.4) were merged into `main` and then merged back into
`develop`; from Phase 2.5 onward, phase PRs target `develop`.

### Branch Naming

```
feature/<phase-or-feature>     e.g. feature/phase2-contracts
fix/<bug-description>
docs/<documentation-topic>
chore/<maintenance-task>
```

### Commit Conventions

```
feat: add user authentication endpoint
fix: resolve audio sample rate mismatch
docs: update RAG architecture documentation
chore: update Python dependencies
test: add unit tests for emotion classifier
```

---

## Contribution Guidelines

1. Read `AGENTS.md` for coding standards and rules.
2. Read `PROJECT-CONTEXT.md` for architectural context.
3. Branch from `develop` — never commit directly to `main`.
4. Write tests for new functionality.
5. Update documentation when changing behavior.
6. Keep commits focused and well-described.
7. Do not commit secrets, large datasets, or generated models.

---

## Testing

The backend test suite lives in `backend/tests/` and is run from the
`backend/` directory with the backend virtual environment active:

```bash
cd backend
pytest
```

The top-level `tests/` directories (`backend/`, `frontend/`, `ml/`, `rag/`,
`integration/`) are placeholders for future modules and contain no tests yet.

---

## Future Work

See the [Development Roadmap](#development-roadmap) for the full plan. Key upcoming milestones:

- **Phase 2.6**: Audio preprocessing — spec in [`docs/phases/PHASE-2.6-AUDIO-PREPROCESSING.md`](docs/phases/PHASE-2.6-AUDIO-PREPROCESSING.md) (awaiting approval)
- **Phase 2.7**: Audio feature extraction
- Later phases (emotion models, speech-to-text, NLP, fusion, LLM, RAG, safety, frontend) will be defined one at a time

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
