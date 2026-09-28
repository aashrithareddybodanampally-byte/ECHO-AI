# ECHO-AI Backend Foundation

This is the FastAPI backend for ECHO-AI: API, database, authentication, and the conversation pipeline that orchestrates the ML, RAG, LLM and safety components.

## Prerequisites
- Python >= 3.10
- PostgreSQL >= 13 (Required for database features and integration tests)

## Setup Virtual Environment
Create and activate a virtual environment:
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

## Install Dependencies
Install the required packages for the backend (includes `ml/requirements.txt`):
```bash
pip install -r requirements.txt
```

## Database Setup
1. Ensure PostgreSQL is running.
2. Create a database for ECHO-AI (e.g., `echo_ai`).
3. Set the `DATABASE_URL` environment variable in your `.env` file.

Example `.env` configuration:
```env
DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/echo_ai
```

## Alembic Migrations
To manage database schema changes, we use Alembic.
After configuring `DATABASE_URL`, apply all migrations:
```bash
alembic upgrade head
```

This creates:
- The Alembic version tracking table (Phase 2.2 initial migration)
- `users`, `conversations`, and `messages` tables (Phase 2.3 migration)
- User preference columns and `memories`, `feedback`, `analysis_results` tables (`c3d4e5f6a7b8`)

To create a new migration after adding/changing models:
```bash
alembic revision --autogenerate -m "description of changes"
```

## Domain Models (Phase 2.3)

### User
Represents a registered ECHO-AI user. Identity anchor for all conversations.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PK, indexed |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE, indexed |
| `created_at` | TIMESTAMP (UTC) | NOT NULL |
| `updated_at` | TIMESTAMP (UTC) | NOT NULL |

### Conversation
Represents a bounded chat session owned by a User.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PK, indexed |
| `user_id` | INTEGER | NOT NULL, FK → users.id (CASCADE) |
| `title` | VARCHAR(255) | nullable |
| `created_at` | TIMESTAMP (UTC) | NOT NULL |
| `updated_at` | TIMESTAMP (UTC) | NOT NULL |

### Message
An individual utterance within a Conversation. Append-only.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PK, indexed |
| `conversation_id` | INTEGER | NOT NULL, FK → conversations.id (CASCADE) |
| `role` | VARCHAR(50) | NOT NULL, CHECK IN ('user','assistant','system') |
| `content` | TEXT | NOT NULL |
| `created_at` | TIMESTAMP (UTC) | NOT NULL, indexed |

### Relationships

```
User (1) ──────────< Conversation (∞)
                         │
                    (1) ─┘
                    Conversation (1) ──< Message (∞)
```

- Deleting a User cascades to their Conversations.
- Deleting a Conversation cascades to its Messages.
- Messages are immutable; they have no `updated_at` field.

## Environment Configuration
Copy the example environment file to `.env`:
```bash
cp .env.example .env
```
(Never commit your real `.env` file containing secrets).

## Running the Application
Start the FastAPI development server:
```bash
uvicorn app.main:app --reload --port 8000
```
The API will be available at `http://127.0.0.1:8000`.

## Endpoints
- **Application Health Check**: `GET /api/v1/health`
  Returns the health status, environment, and version of the API.
- **Database Readiness Check**: `GET /api/v1/health/db`
  Checks if the application can successfully connect to the PostgreSQL database.

### Authentication (Phase 2.4)
- **User Registration**: `POST /api/v1/auth/register`
  Registers a new user given `email` and `password`. Passwords are safely hashed using bcrypt.
- **User Login**: `POST /api/v1/auth/login`
  Authenticates a user and returns a standard JWT Bearer access token.
- **Get Current User**: `GET /api/v1/auth/me`
  Protected endpoint demonstrating JWT authentication and returning the current user profile.

### Conversation & AI endpoints
All implemented; full contract in [`docs/api/CONTRACTS.md`](../docs/api/CONTRACTS.md).

- `POST /api/v1/chat`, `POST /api/v1/chat/voice` — text and voice conversation turns
- `POST /api/v1/emotion/analyze`, `POST /api/v1/emotion/fusion` — voice emotion, multimodal fusion
- `POST /api/v1/rag/retrieve` — knowledge-base retrieval with sources
- `GET/DELETE /api/v1/history` — conversation history
- `POST /api/v1/feedback`, `GET /api/v1/analytics`
- `/api/v1/memory`, `/api/v1/settings` — user-approved memory and privacy settings

The backend imports the root-level `ml/`, `rag/` and `safety/` packages
(`app/__init__.py` adds the repository root to `sys.path`).

**LLM:** set `ANTHROPIC_API_KEY` in `backend/.env` to use Claude. Without a key
the backend uses a clearly labeled offline template responder (`offline-template-v1`).

**Voice emotion model:** train it once from the repository root (see
[`docs/ml/VOICE-EMOTION-MODEL.md`](../docs/ml/VOICE-EMOTION-MODEL.md)). Until then
`/emotion/analyze` returns `503` and voice chat uses text-only emotion.

## Running Tests
Run the full test suite from the `backend/` directory:
```bash
pytest
```

Run only the domain model unit tests (no PostgreSQL required):
```bash
pytest tests/test_models.py -v
```

**Note:** Tests use SQLite in-memory databases, mocked sessions and dependency
overrides; they never call the LLM or download the Whisper model. The
ML/RAG/safety packages have their own suite, run from the repository root:
`pytest tests`. Migrations are not exercised against live PostgreSQL in the
automated suite (`alembic upgrade head --sql` renders them offline).

## Project Structure
- `app/main.py`: Application entry point.
- `app/config.py`: Environment configuration management.
- `app/core/`: Core features like logging and exception handlers.
- `app/api/v1/`: API route handlers.
- `app/schemas/`: Pydantic models for request/response validation.
- `app/db/`: Database configuration, sessions, declarative base, and FastAPI dependencies.
- `app/models/`: SQLAlchemy domain models (User, Conversation, Message, Memory, Feedback, AnalysisResult).
- `app/services/`: Service interfaces, providers, the chat pipeline, response policy, LLM providers and ML/RAG/safety adapters.
- `tests/`: Automated test suite.
- `alembic/`: Database migration scripts.



