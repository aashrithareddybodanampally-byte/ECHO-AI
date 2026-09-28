import logging
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

from app.services.interfaces import InvalidInputError, ResourceNotFoundError

logger = logging.getLogger(__name__)

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(InvalidInputError)
    async def invalid_input_handler(request: Request, exc: InvalidInputError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(ResourceNotFoundError)
    async def not_found_handler(request: Request, exc: ResourceNotFoundError):
        # Same response whether the resource is missing or owned by another user.
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"}
        )
