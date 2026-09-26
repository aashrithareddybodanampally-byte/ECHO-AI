# ECHO-AI Backend Foundation

This is the FastAPI backend foundation for ECHO-AI (Phase 2.1).

## Prerequisites
- Python >= 3.10

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
- **Health Check**: `GET /api/v1/health`
  Returns the health status, environment, and version of the API.

## Running Tests
Run the test suite from the `backend/` directory using pytest:
```bash
pytest
```

## Project Structure
- `app/main.py`: Application entry point.
- `app/config.py`: Environment configuration management.
- `app/core/`: Core features like logging and exception handlers.
- `app/api/v1/`: API route handlers.
- `app/schemas/`: Pydantic models for request/response validation.
- `tests/`: Automated test suite.
