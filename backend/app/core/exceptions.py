"""
Unified Exception Handling
Provides consistent error responses across the entire API
"""

import logging
from typing import Any, Optional, Union
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Base exception for all API errors"""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Internal server error",
        error_code: Optional[str] = None,
        data: Optional[Any] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code or f"ERR_{status_code}"
        self.data = data
        super().__init__(self.detail)


class BadRequestException(APIException):
    """400 Bad Request"""

    def __init__(self, detail: str = "Bad request", data: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="BAD_REQUEST",
            data=data
        )


class UnauthorizedException(APIException):
    """401 Unauthorized"""

    def __init__(self, detail: str = "Unauthorized", data: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED",
            data=data
        )


class ForbiddenException(APIException):
    """403 Forbidden"""

    def __init__(self, detail: str = "Forbidden", data: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN",
            data=data
        )


class NotFoundException(APIException):
    """404 Not Found"""

    def __init__(self, detail: str = "Resource not found", data: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND",
            data=data
        )


class ConflictException(APIException):
    """409 Conflict"""

    def __init__(self, detail: str = "Resource conflict", data: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT",
            data=data
        )


class RateLimitException(APIException):
    """429 Too Many Requests"""

    def __init__(self, detail: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="RATE_LIMIT_EXCEEDED",
            data={"retry_after": retry_after}
        )


class InternalServerException(APIException):
    """500 Internal Server Error"""

    def __init__(self, detail: str = "Internal server error", data: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="INTERNAL_SERVER_ERROR",
            data=data
        )


class ServiceUnavailableException(APIException):
    """503 Service Unavailable"""

    def __init__(self, detail: str = "Service temporarily unavailable", data: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="SERVICE_UNAVAILABLE",
            data=data
        )


def create_error_response(
    status_code: int,
    detail: str,
    error_code: Optional[str] = None,
    data: Optional[Any] = None
) -> dict:
    """Create standardized error response"""
    response = {
        "success": False,
        "error": {
            "code": error_code or f"ERR_{status_code}",
            "message": detail,
            "status_code": status_code
        }
    }

    if data is not None:
        response["error"]["details"] = data

    return response


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle custom API exceptions"""
    logger.error(
        f"API Exception: {exc.error_code} - {exc.detail} "
        f"(Path: {request.url.path}, Status: {exc.status_code})"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            detail=exc.detail,
            error_code=exc.error_code,
            data=exc.data
        )
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail} "
        f"(Path: {request.url.path})"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            detail=str(exc.detail)
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(
        f"Validation Error: {len(errors)} errors "
        f"(Path: {request.url.path})"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Validation error",
            error_code="VALIDATION_ERROR",
            data={"errors": errors}
        )
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors"""
    logger.exception(
        f"Database Error: {type(exc).__name__} "
        f"(Path: {request.url.path})"
    )

    # Check for specific error types
    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=create_error_response(
                status_code=status.HTTP_409_CONFLICT,
                detail="Database integrity error (duplicate or constraint violation)",
                error_code="DATABASE_INTEGRITY_ERROR"
            )
        )

    # Generic database error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred",
            error_code="DATABASE_ERROR"
        )
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions"""
    logger.exception(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)} "
        f"(Path: {request.url.path})"
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
            error_code="INTERNAL_SERVER_ERROR"
        )
    )


def setup_exception_handlers(app: FastAPI):
    """Register all exception handlers with FastAPI app"""
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("✅ Unified exception handlers registered")
