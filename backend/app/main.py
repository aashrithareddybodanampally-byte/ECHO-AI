from fastapi import FastAPI
from app.api.v1 import health, auth, emotion, rag, chat, feedback, history, analytics
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

# Setup centralized exception handling
setup_exception_handlers(app)

# Register API routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(emotion.router, prefix="/api/v1", tags=["Emotion"])
app.include_router(rag.router, prefix="/api/v1", tags=["RAG"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(feedback.router, prefix="/api/v1", tags=["Feedback"])
app.include_router(history.router, prefix="/api/v1", tags=["History"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
