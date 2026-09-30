# ECHO-AI

> A multimodal, context-aware, safety-first conversational companion that
> listens to **what** you say and **how** you say it, and answers the way a
> warm counselor would: briefly, attentively and without rushing to fix.

ECHO-AI is **not a medical service**. It does not diagnose, treat or give
medication advice, and its emotion estimates are model predictions that can be
wrong. In an emergency, contact local emergency services (India: Tele-MANAS
14416 · US & Canada: 988 · elsewhere: findahelpline.com).

---

## Features

| | |
|---|---|
| 💬 **Text & voice chat** | Type or speak. Voice is transcribed locally with faster-whisper; replies can be read aloud by the browser. |
| 🌊 **Mood understanding** | A trained voice-emotion model, a text sentiment/emotion analyzer and (optionally) your facial expression are fused into one mood estimate. |
| 📷 **Optional camera** | Opt-in. Facial expression is analyzed **in your browser only**; video is never uploaded, only a label like "sad, 80%". |
| 🧑‍⚕️ **Counseling-style replies** | Short, reflective replies with one small question at a time; listens first, offers one idea only when you ask. Based on motivational interviewing (OARS), DBT validation and person-centred practice ([details](docs/ml/COUNSELING-STYLE.md)). |
| 🧠 **Memory you control** | Recent messages, earlier conversations and facts you choose to save give replies context. View, delete or switch memory off at any time. |
| 📚 **Cited sources** | When you ask for help, suggestions can draw on a small original knowledge base (study, sleep, relaxation, support) and cite it. |
| 🛡 **Safety** | Distress gets gentler replies; high-risk messages get a fixed crisis response with helplines and the LLM is bypassed. Replies are checked for diagnoses, dosing advice and self-harm content. |
| 📈 **Insights & feedback** | Rate replies; opt in to see your mood distribution over time. |
| 🔒 **Privacy by default** | Raw audio and video are never stored; emotion statistics are off until you enable them. |

---

## How a message is handled

```
You (text / voice / optional camera label)
  │
  ├─ voice ─> preprocessing ─> speech-to-text ─> voice emotion model
  ├─ words ─> sentiment + emotion
  └─ face  ─> expression estimated in the browser
                     │
                     ▼
        fusion (voice 0.5 · face 0.3 · words 0.3 · previous turn 0.2)
                     │
        input safety ── high risk ──> crisis response with helplines (no LLM)
                     │
        context: this conversation · earlier sessions · saved memories · mood history
                     │
        response policy: stage (explore → deepen → support), tone, length
                     │
        knowledge-base retrieval (only when you ask for help)
                     │
        LLM (Groq or Claude; labeled offline fallback) ─> output safety ─> reply
```

---

## Quick start (local, Windows / macOS / Linux)

Prerequisites: **Python 3.10+**, **Node.js 22+**.

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate             # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` (git-ignored, never commit it):

| Key | Required | Value |
|---|---|---|
| `SECRET_KEY` | ✅ | A long random string: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `DATABASE_URL` | ✅ | `sqlite:///./echo_ai_dev.db` (simplest; tables are created automatically) or a PostgreSQL URL (then run `alembic upgrade head`) |
| `GROQ_API_KEY` | Recommended | From [console.groq.com/keys](https://console.groq.com/keys). Enables real LLM replies (`GROQ_MODEL`, default `openai/gpt-oss-120b`) |
| `ANTHROPIC_API_KEY` | Optional | Alternative LLM (Claude), used when no Groq key is set |

Without an LLM key the app still works with a clearly labeled offline responder.
All other settings have working defaults (see `backend/.env.example`).

```bash
uvicorn app.main:app --reload --port 8000      # API docs: http://localhost:8000/docs
```

### 2. Voice emotion model (once)

Download the RAVDESS speech dataset (`Audio_Speech_Actors_01-24.zip`, CC BY-NC-SA 4.0) from
[Zenodo](https://zenodo.org/records/1188976), extract it to `data/raw/ravdess/`, then from the repository root:

```bash
python -m ml.training.train_voice_emotion --data data/raw/ravdess --out models
```

Without the model, chat and voice still work; voice emotion is simply left out.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                                    # http://localhost:5173
```

`npm run dev` / `npm run build` copy the small face-expression models into
`public/models/` automatically.

### Docker (not validated yet)

```bash
cp .env.docker.example .env                    # set POSTGRES_PASSWORD, SECRET_KEY, GROQ_API_KEY
docker compose up --build
```

---

## Testing

```bash
cd backend && pytest                           # API, pipeline, security, LLM providers, policy
pytest tests                                   # from repo root: audio ML, NLP, fusion, RAG, safety
cd frontend && npm test && npm run build       # WAV encoding, routing, face-mood averaging, type-check
```

Tests never call a paid LLM, never download the Whisper model, never use your
`backend/.env` and use synthetic audio only.

---

## Measured results

Voice emotion model (RAVDESS, 8 emotions, speaker-independent test set):
**accuracy 0.458, macro-F1 0.453** (chance 0.125); ~185 ms per clip on CPU.
Full model card, confusion matrix and error analysis:
[`docs/ml/VOICE-EMOTION-MODEL.md`](docs/ml/VOICE-EMOTION-MODEL.md).

---

## Documentation

| Document | Contents |
|---|---|
| [`docs/api/CONTRACTS.md`](docs/api/CONTRACTS.md) | Every API endpoint, request/response shape, status code and service interface |
| [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | Components and data flow |
| [`docs/architecture/TECH-STACK.md`](docs/architecture/TECH-STACK.md) | Technologies in use and why |
| [`docs/ml/VOICE-EMOTION-MODEL.md`](docs/ml/VOICE-EMOTION-MODEL.md) | Voice model card with real metrics |
| [`docs/ml/COUNSELING-STYLE.md`](docs/ml/COUNSELING-STYLE.md) | How ECHO-AI talks, with research sources |
| [`docs/phases/README.md`](docs/phases/README.md) | Implementation history, decisions and status |
| [`backend/README.md`](backend/README.md) | Backend setup, configuration and endpoints |
| [`AGENTS.md`](AGENTS.md) / [`PROJECT-CONTEXT.md`](PROJECT-CONTEXT.md) | Rules for coding agents / project context |

---

## Repository structure

```
ECHO-AI/
├── backend/          # FastAPI app, conversation pipeline, Alembic migrations, backend tests
├── frontend/         # React + Vite + TypeScript + Tailwind (landing page, chat, insights, settings)
├── ml/               # audio preprocessing, features, speech-to-text, training, inference, text emotion, fusion
├── rag/              # original knowledge base, chunking, TF-IDF retrieval
├── safety/           # input/output guardrails, crisis protocol
├── tests/            # ML, RAG and safety tests
├── infrastructure/   # Dockerfiles
├── docs/             # API, architecture, ML, phase docs
├── data/             # datasets (git-ignored)
├── models/           # trained model artifacts (git-ignored)
└── .github/workflows # CI
```

---

## Known limitations

- The text emotion analyzer is a keyword heuristic; masked feelings ("I act like it's fine") can read as calm.
- The voice model is trained on acted studio speech; accuracy on real microphones has not been measured.
- Facial-expression accuracy with real cameras has not been measured.
- Docker, Compose and CI are written but have not been run.
- An AI companion is not a therapist and cannot replace professional care.

---

## Git workflow

- **`main`**: stable. **`develop`**: integration.
- Branch from `develop` as `feature/<phase-or-feature>`, open a PR, and merge after human review.
- Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`).

---

## Data and licensing

- Code: **MIT** ([LICENSE](LICENSE)).
- The voice model is trained on **RAVDESS** (Livingstone & Russo, 2018), **CC BY-NC-SA 4.0**. The dataset and trained artifacts are not committed, and models trained on it are **non-commercial**.
- Facial expression uses [`@vladmandic/face-api`](https://github.com/vladmandic/face-api) (MIT).
- The knowledge base in `rag/knowledge_base/` and the frontend design are original work for this project.
