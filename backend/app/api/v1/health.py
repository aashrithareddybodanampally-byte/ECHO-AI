from fastapi import APIRouter
from app.schemas.health import HealthResponse
from app.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        version=settings.APP_VERSION
    )
