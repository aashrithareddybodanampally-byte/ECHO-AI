# ECHO-AI

> A multimodal, context-aware, safety-driven conversational AI that listens to
> what you say **and** how you say it.

---

## What it does

You talk to ECHO-AI by text or voice. For each message it:

1. **Preprocesses audio** (mono, 16 kHz, filtering, normalization, silence trimming)
2. **Transcribes speech** locally (faster-whisper)
3. **Predicts vocal emotion** with a trained classifier (MFCC, chroma, spectral, ZCR and RMS features)
4. **Analyzes the text** (sentiment + emotion)
5. **Fuses** voice, text and previous-turn context into one emotional state with a confidence
6. **Checks input safety**: distress gets a careful response; high-risk messages get a fixed crisis protocol with helplines, without calling the LLM
7. **Builds context** from recent messages and memories the user chose to save
8. **Retrieves** relevant knowledge-base passages and cites them
9. **Sets a response policy** (tone, length, follow-up question, resources)
10. **Generates** the reply with an LLM: Groq (default `openai/gpt-oss-120b`) or Claude, or a clearly labeled offline responder when no API key is set
11. **Checks output safety** (no diagnoses, dosing advice or self-harm methods)
12. Optionally **reads the reply aloud**, collects **feedback**, and (only if the user opts in) stores **emotion statistics** for an insights page

Emotion outputs are **model predictions, not diagnoses**. ECHO-AI is not a
medical service and cannot provide crisis care.

---

## Status

| Area | Status |
|---|---|
| Backend API, database, authentication | ✅ Implemented and tested |
| Audio preprocessing, feature extraction | ✅ Implemented and tested |
| Voice emotion model (SVM vs Random Forest on RAVDESS) | ✅ Trained; measured results in [`docs/ml/VOICE-EMOTION-MODEL.md`](docs/ml/VOICE-EMOTION-MODEL.md) |
| Speech-to-text, text emotion, fusion | ✅ Implemented |
| Context, memory, response policy, LLM, RAG, safety | ✅ Implemented and tested |
| Feedback, analytics, privacy settings | ✅ Implemented and tested |
| Frontend | ✅ Implemented, built, exercised in a browser |
| Docker / Compose / CI | ⚠️ Written, not validated |

Phases and decisions: [`docs/phases/README.md`](docs/phases/README.md).
API reference: [`docs/api/CONTRACTS.md`](docs/api/CONTRACTS.md).
Architecture: [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md).

---

## Architecture

```
Frontend (React + Vite)  ──REST──>  Backend (FastAPI)
                                       │
          ┌──────────────┬─────────────┼──────────────┬──────────────┐
          ▼              ▼             ▼              ▼              ▼
     ml/audio        ml/nlp        ml/models       rag/          safety/
 preprocessing,   text emotion      fusion      TF-IDF over     guardrails,
 features, STT,                                 knowledge base  crisis protocol
 voice emotion
                                       │
                                       ▼
                  LLM (Groq or Claude) · SQLite/PostgreSQL
```

`ml/`, `rag/` and `safety/` never import the backend; the backend uses them
through the service interfaces in `backend/app/services/interfaces.py`.

---

## Quick start (local)

Prerequisites: Python ≥ 3.10, Node.js ≥ 22, and optionally PostgreSQL.

```bash
# 1. Backend
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env              # set SECRET_KEY; DATABASE_URL (PostgreSQL or sqlite:///./echo_ai_dev.db)
alembic upgrade head              # PostgreSQL only; SQLite creates tables automatically
uvicorn app.main:app --reload --port 8000

# 2. Voice emotion model (once; from the repository root, needs the RAVDESS dataset in data/raw/ravdess)
python -m ml.training.train_voice_emotion --data data/raw/ravdess --out models

# 3. Frontend
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

Optional: set `GROQ_API_KEY` (or `ANTHROPIC_API_KEY`) in `backend/.env` for LLM replies. With `LLM_PROVIDER=auto`, Groq is used first when its key is set.

With Docker (not validated yet): `cp .env.docker.example .env`, set values, `docker compose up --build`.

---

## Testing

```bash
cd backend && pytest              # API, pipeline, security, contracts
pytest tests                      # from repo root: ML, RAG, safety
cd frontend && npm test && npm run build
```

Tests never call the LLM, never download the Whisper model and use synthetic
audio only.

---

## Repository structure

```
ECHO-AI/
├── backend/          # FastAPI app, Alembic migrations, backend tests
├── frontend/         # React + Vite + TypeScript + Tailwind
├── ml/               # audio preprocessing, features, STT, training, inference, text emotion, fusion
├── rag/              # knowledge base, chunking, TF-IDF retrieval
├── safety/           # input/output guardrails, crisis protocol
├── tests/            # ML, RAG and safety tests
├── infrastructure/   # Dockerfiles
├── docs/             # API, architecture, phases, ML, development docs
├── data/             # datasets (git-ignored)
├── models/           # trained model artifacts (git-ignored)
└── .github/workflows # CI
```

---

## Git workflow

- **`main`**: stable. **`develop`**: integration.
- Branch from `develop` as `feature/<phase-or-feature>`, open a PR into `develop`, and merge after human review.
- Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`).

PRs #1–#4 (Phases 2.1–2.4) were merged into `main` and then back into `develop`.

---

## Data and licensing notes

- The voice model is trained on **RAVDESS** (Livingstone & Russo, 2018), licensed
  **CC BY-NC-SA 4.0**. The dataset and trained artifacts are not committed. Models
  trained on it inherit the **non-commercial** restriction.
- The knowledge base in `rag/knowledge_base/` is original text written for this project.

## License

MIT (code). See [LICENSE](LICENSE).
