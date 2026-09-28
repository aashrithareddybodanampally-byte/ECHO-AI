import logging
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

from app.services.interfaces import (
    ConflictError,
    InvalidInputError,
    ResourceNotFoundError,
    ServiceUnavailableError,
    UnsupportedMediaError,
)

logger = logging.getLogger(__name__)

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(InvalidInputError)
    async def invalid_input_handler(request: Request, exc: InvalidInputError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(ResourceNotFoundError)
    async def not_found_handler(request: Request, exc: ResourceNotFoundError):
        # Same response whether the resource is missing or owned by another user.
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    @app.exception_handler(UnsupportedMediaError)
    async def unsupported_media_handler(request: Request, exc: UnsupportedMediaError):
        return JSONResponse(status_code=415, content={"detail": str(exc)})

    @app.exception_handler(ServiceUnavailableError)
    async def unavailable_handler(request: Request, exc: ServiceUnavailableError):
        logger.warning(f"Service unavailable: {exc}")
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"}
        )
