from fastapi import FastAPI
from app.api.v1 import health
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
