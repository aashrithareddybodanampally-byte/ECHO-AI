# ECHO-AI Backend Foundation

This is the FastAPI backend foundation for ECHO-AI (Phase 2.1) and Database Foundation (Phase 2.2).

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
Install the required packages for the backend:
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
After configuring `DATABASE_URL`, apply the initial migration:
```bash
alembic upgrade head
```

To create a new migration after adding/changing models:
```bash
alembic revision --autogenerate -m "description of changes"
```

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

## Running Tests
Run the test suite from the `backend/` directory using pytest:
```bash
pytest
```
**Note:** Tests that interact with the database (if not mocked) require a running PostgreSQL instance configured via `DATABASE_URL`. Currently, database health tests use mocked sessions, so they do not strictly require PostgreSQL to pass.

## Project Structure
- `app/main.py`: Application entry point.
- `app/config.py`: Environment configuration management.
- `app/core/`: Core features like logging and exception handlers.
- `app/api/v1/`: API route handlers.
- `app/schemas/`: Pydantic models for request/response validation.
- `app/db/`: Database configuration, sessions, declarative base, and FastAPI dependencies.
- `tests/`: Automated test suite.
- `alembic/`: Database migration scripts.
