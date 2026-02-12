"""Custom exception classes and global exception handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger("trendedge.exceptions")


class TrendEdgeError(Exception):
    """Base exception for all TrendEdge errors."""

    def __init__(self, message: str, code: str, status_code: int, details: list[dict[str, str]] | None = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


class AuthenticationError(TrendEdgeError):
    def __init__(self, message: str = "Authentication required. Please provide a valid access token."):
        super().__init__(message=message, code="AUTHENTICATION_REQUIRED", status_code=401)


class ForbiddenError(TrendEdgeError):
    def __init__(self, message: str = "You do not have permission to access this resource."):
        super().__init__(message=message, code="FORBIDDEN", status_code=403)


class NotFoundError(TrendEdgeError):
    def __init__(self, resource: str = "Resource", identifier: str = ""):
        message = f"{resource} not found." if not identifier else f"{resource} with ID '{identifier}' not found."
        super().__init__(message=message, code="NOT_FOUND", status_code=404)


class ConflictError(TrendEdgeError):
    def __init__(self, message: str = "Resource conflict."):
        super().__init__(message=message, code="CONFLICT", status_code=409)


class RateLimitError(TrendEdgeError):
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(
            message=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            code="RATE_LIMITED",
            status_code=429,
        )


class BrokerError(TrendEdgeError):
    def __init__(self, message: str = "Broker service is temporarily unavailable. Please try again."):
        super().__init__(message=message, code="BROKER_ERROR", status_code=502)


class ServiceUnavailableError(TrendEdgeError):
    def __init__(self, message: str = "Service temporarily unavailable. Please try again in a few minutes."):
        super().__init__(message=message, code="SERVICE_UNAVAILABLE", status_code=503)


def _build_error_response(
    code: str,
    message: str,
    request_id: str,
    details: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    }
    if details:
        response["error"]["details"] = details
    return response


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(TrendEdgeError)
    async def trendedge_error_handler(request: Request, exc: TrendEdgeError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        log_level = {401: "warning", 403: "warning", 404: "debug"}.get(exc.status_code, "info")
        getattr(logger, log_level)(
            exc.message,
            error_code=exc.code,
            status_code=exc.status_code,
            request_id=request_id,
        )
        headers = {}
        if isinstance(exc, RateLimitError):
            headers["Retry-After"] = str(exc.retry_after)
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_response(exc.code, exc.message, request_id, exc.details),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        details = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
            details.append({"field": field, "message": error["msg"]})
        logger.info("Request validation failed", request_id=request_id, detail_count=len(details))
        return JSONResponse(
            status_code=400,
            content=_build_error_response("VALIDATION_ERROR", "Request validation failed", request_id, details),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.critical(
            "Unhandled exception",
            request_id=request_id,
            exc_type=type(exc).__name__,
            exc_message=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content=_build_error_response(
                "INTERNAL_ERROR",
                "An internal error occurred. This has been reported automatically.",
                request_id,
            ),
        )
