# ECHO-AI — Technology Stack

> This document records the **planned** technology choices for ECHO-AI.
> Backend dependencies are installed (see `backend/requirements.txt`); all other
> choices are planned and **not yet installed**.

---

## Frontend

| Technology | Purpose | Version (Target) |
|---|---|---|
| React | UI framework | 18+ |
| Vite | Build tool & dev server | 5+ |
| Tailwind CSS | Utility-first CSS | 3+ |
| TypeScript | Type-safe JavaScript | 5+ |
| Vitest or Jest | Unit testing | Latest |
| React Testing Library | Component testing | Latest |

**Rationale**: Vite provides fast HMR and build performance. React is the team's primary competency. Tailwind enables rapid, consistent styling. TypeScript catches errors at compile time.

---

## Backend

| Technology | Purpose | Version (Target) |
|---|---|---|
| Python | Core language | 3.10+ |
| FastAPI | Web framework | 0.100+ |
| Uvicorn | ASGI server | Latest |
| Pydantic | Data validation & settings | 2+ |
| SQLAlchemy | ORM & database toolkit | 2+ |
| Alembic | Database migrations | Latest |
| pydantic-settings | Environment-based settings (used instead of python-dotenv) | 2+ |
| psycopg | PostgreSQL driver | 3+ |
| PyJWT | JWT access tokens | 2.8+ |
| bcrypt | Password hashing | <4.0 |

**Rationale**: FastAPI provides automatic OpenAPI docs, async support, and Pydantic-based validation. SQLAlchemy 2.0 offers both ORM and Core patterns. Alembic handles schema evolution.

---

## Database

| Technology | Purpose |
|---|---|
| PostgreSQL | Primary relational database |
| pgvector (potential) | Vector similarity search extension |

**Rationale**: PostgreSQL is battle-tested, supports JSON, full-text search, and with pgvector can handle embeddings — potentially unifying relational and vector storage.

---

## Machine Learning

| Technology | Purpose |
|---|---|
| NumPy | Numerical computing |
| pandas | Data manipulation |
| scikit-learn | Classical ML models |
| librosa | Audio feature extraction |
| Whisper (OpenAI) | Speech-to-text |
| Transformers (Hugging Face) | NLP models |
| PyTorch or TensorFlow | Deep learning framework |

**Rationale**: The Python ML ecosystem is mature and well-documented. librosa is the standard for audio analysis. Whisper provides state-of-the-art STT. Transformers gives access to pre-trained NLP models.

---

## RAG (Retrieval-Augmented Generation)

| Technology | Purpose |
|---|---|
| Sentence Transformers | Embedding generation |
| Vector database (TBD) | Similarity search & storage |
| LangChain or LlamaIndex | RAG orchestration (under evaluation) |

**Rationale**: RAG technology choices will be finalized during the RAG phase based on scale requirements and embedding model selection.

---

## LLM Integration

| Technology | Purpose |
|---|---|
| OpenAI API / Anthropic API | Response generation |
| LiteLLM (potential) | Multi-provider abstraction |

**Rationale**: API-based LLMs avoid the infrastructure cost of self-hosting. LiteLLM would allow provider-agnostic integration.

---

## Testing

| Technology | Purpose |
|---|---|
| Pytest | Python unit & integration testing |
| pytest-asyncio | Async test support |
| pytest-cov | Coverage reporting |
| httpx | Async HTTP test client (for FastAPI) |
| Vitest or Jest | Frontend unit testing |
| Playwright or Cypress | End-to-end testing |

---

## Infrastructure & DevOps

| Technology | Purpose |
|---|---|
| Docker | Containerization |
| Docker Compose | Multi-service orchestration |
| GitHub Actions | CI/CD pipelines |
| pre-commit | Git hook management |

---

## Monitoring & Observability (Future)

| Technology | Purpose |
|---|---|
| Prometheus + Grafana | Metrics & dashboards |
| MLflow or Weights & Biases | Experiment tracking |
| Sentry | Error tracking |

---

## Installation Status

> **Installed**: backend dependencies in `backend/requirements.txt` (FastAPI, Uvicorn, pydantic-settings,
> SQLAlchemy, psycopg, Alembic, PyJWT, bcrypt, passlib, email-validator, pytest, httpx).
>
> **Not installed**: all ML, RAG, LLM, frontend and infrastructure dependencies. Phase 2.6 proposes
> `numpy`, `soundfile` and `scipy` (pending approval).
>
> Dependencies are added incrementally as each phase begins, with justification in the PR.
