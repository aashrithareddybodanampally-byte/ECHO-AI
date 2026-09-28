from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import health, auth, emotion, rag, chat, feedback, history, analytics, memory
from app.config import settings, setup_logging
from app.core.exceptions import setup_exception_handlers

# Setup centralized logging
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for ECHO-AI",
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup centralized exception handling
setup_exception_handlers(app)

if settings.DATABASE_URL.startswith("sqlite"):
    # Local-development convenience only: SQLite cannot run the Alembic history
    # (ALTER COLUMN), so create the schema directly. PostgreSQL uses `alembic upgrade head`.
    from app import models as _models  # noqa: F401  (registers tables; must not rebind `app`)
    from app.db.base import Base
    from app.db.session import engine

    Base.metadata.create_all(bind=engine)

# Register API routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(emotion.router, prefix="/api/v1", tags=["Emotion"])
app.include_router(rag.router, prefix="/api/v1", tags=["RAG"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(feedback.router, prefix="/api/v1", tags=["Feedback"])
app.include_router(history.router, prefix="/api/v1", tags=["History"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
app.include_router(memory.router, prefix="/api/v1", tags=["Memory & Settings"])
