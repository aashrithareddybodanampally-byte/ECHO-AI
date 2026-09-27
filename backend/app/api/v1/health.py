from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.health import HealthResponse, DatabaseHealthResponse
from app.config import settings
from app.db.dependencies import get_db

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        version=settings.APP_VERSION
    )

@router.get("/health/db", response_model=DatabaseHealthResponse)
async def db_health_check(db: Session = Depends(get_db)):
    try:
        # Execute a simple safe query
        db.execute(text("SELECT 1"))
        return DatabaseHealthResponse(
            status="healthy",
            database="connected"
        )
    except Exception as e:
        return DatabaseHealthResponse(
            status="unhealthy",
            database="disconnected"
        )
