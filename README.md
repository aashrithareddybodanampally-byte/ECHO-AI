# ECHO-AI

> A multimodal AI conversational system that combines voice and text understanding for intelligent, context-aware interactions.

---

## Overview

ECHO-AI is a multimodal conversational AI platform designed to process both text and voice input, analyze speech and language characteristics, maintain conversation context and user memory, retrieve relevant information through RAG, generate LLM-powered responses, and enforce safety guardrails — all within a modular, production-ready architecture.

## Vision

Create a conversational AI system that truly *listens* — understanding not just the words, but the tone, emotion, and context behind them — to deliver responses that are accurate, personalized, and safe.

---

## Current Phase

### ✅ Phase 1 — Development Environment & Repository Foundation

The project is currently in Phase 1. This phase establishes:

- [x] Git repository with branching strategy
- [x] Project directory structure
- [x] Environment variable strategy
- [x] Documentation foundation
- [x] Agent instructions for AI-assisted development
- [x] Development workflow documentation
- [x] Environment validation tooling

> **No AI/ML functionality, application logic, or deployment infrastructure has been implemented yet.** All features listed below are **planned**.

---

## Planned Capabilities

| Capability | Status | Description |
|---|---|---|
| Text conversation | 🔮 Planned | Real-time text-based chat interface |
| Voice input | 🔮 Planned | Microphone capture and audio streaming |
| Speech-to-text | 🔮 Planned | Whisper-based transcription |
| Voice emotion analysis | 🔮 Planned | Emotion detection from audio features |
| Text/NLP analysis | 🔮 Planned | Sentiment, intent, and entity extraction |
| Multimodal fusion | 🔮 Planned | Combined audio + text signal analysis |
| Conversation context | 🔮 Planned | Multi-turn conversation history |
| User memory | 🔮 Planned | Opt-in persistent user preferences |
| RAG | 🔮 Planned | Retrieval-Augmented Generation |
| LLM integration | 🔮 Planned | API-based response generation |
| Safety guardrails | 🔮 Planned | Content filtering and bias detection |
| Analytics | 🔮 Planned | Conversation quality and usage metrics |

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
| Backend | Python + FastAPI | 🔮 Planned |
| Database | PostgreSQL | 🔮 Planned |
| ML | Python, scikit-learn, librosa, NumPy, pandas | 🔮 Planned |
| Speech | Whisper (or equivalent) | 🔮 Planned |
| NLP | Transformers / NLP tooling | 🔮 Planned |
| RAG | Embeddings + Vector DB | 🔮 Planned |
| LLM | API-based (e.g., OpenAI, Anthropic) | 🔮 Planned |
| Testing | Pytest, Vitest/Jest | 🔮 Planned |
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
| **Phase 1** | Development environment & repository foundation | ✅ Current |
| **Phase 2** | Backend API, database, authentication | 🔮 Planned |
| **Phase 3** | Frontend application | 🔮 Planned |
| **Phase 4** | ML pipelines (audio + NLP) | 🔮 Planned |
| **Phase 5** | RAG system & vector search | 🔮 Planned |
| **Phase 6** | LLM integration & response generation | 🔮 Planned |
| **Phase 7** | Safety guardrails & content filtering | 🔮 Planned |
| **Phase 8** | Multimodal fusion & advanced features | 🔮 Planned |
| **Phase 9** | Analytics, monitoring & MLOps | 🔮 Planned |
| **Phase 10** | Production deployment & CI/CD | 🔮 Planned |

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
# (no actual services to configure in Phase 1)

# Run environment validation
# On Windows (PowerShell):
.\scripts\check_environment.ps1

# On Linux/macOS:
bash scripts/check_environment.sh
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your values. **Never commit `.env` to version control.**

See `.env.example` for all available configuration options.

---

## Git Workflow

1. **`main`** — Production-ready code. Protected branch.
2. **`develop`** — Integration branch for active development.
3. **Feature branches** — Branch from `develop`, merge back via PR.

### Branch Naming

```
feat/<feature-name>
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

Tests are organized under `tests/` mirroring the source structure:

```
tests/
├── backend/       # Backend API and service tests
├── frontend/      # Frontend component and integration tests
├── ml/            # ML model and pipeline tests
├── rag/           # RAG system tests
└── integration/   # Cross-module integration tests
```

```bash
# Run backend tests (when implemented)
pytest tests/backend/

# Run all tests
pytest
```

---

## Future Work

See the [Development Roadmap](#development-roadmap) for the full plan. Key upcoming milestones:

- **Phase 2**: FastAPI backend with PostgreSQL, user authentication, session management
- **Phase 3**: React frontend with real-time chat interface
- **Phase 4**: Audio emotion detection and NLP analysis pipelines
- **Phase 5**: RAG with vector search for knowledge retrieval
- **Phase 6**: LLM-powered response generation

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
