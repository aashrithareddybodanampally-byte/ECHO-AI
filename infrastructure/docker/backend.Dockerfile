# ECHO-AI backend (FastAPI) + ml/, rag/, safety/ packages.
# Build context: repository root.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY ml/requirements.txt ml/requirements.txt
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY ml ml
COPY rag rag
COPY safety safety
COPY backend backend

# Trained model artifacts are mounted at /app/models (see docker-compose.yml).
ENV VOICE_EMOTION_MODEL_PATH=/app/models/emotion_model_v1.pkl

WORKDIR /app/backend
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
