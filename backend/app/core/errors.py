"""Custom exceptions + handlers giving every error the same JSON shape:

    {"error": "<code>", "message": "<human readable>", "fields": [...]}
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger("errors")


# ---------- Custom exceptions raised by services/routers ----------
class AppError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "bad_request"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class InvalidTransitionError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "invalid_transition"


class AIUnavailableError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "ai_unavailable"


# ---------- Helpers ----------
def _body(code: str, message: str, fields: list | None = None) -> dict:
    return {"error": code, "message": message, "fields": fields or []}


def _clean_msg(msg: str) -> str:
    # Pydantic prefixes custom validator messages with "Value error, "
    return msg.removeprefix("Value error, ")


# ---------- Handlers ----------
async def app_error_handler(request: Request, exc: AppError):
    logger.info("AppError %s on %s %s", exc.code, request.method, request.url.path)
    return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message))


async def validation_error_handler(request: Request, exc: RequestValidationError):
    fields = []
    for err in exc.errors():
        loc = [str(p) for p in err.get("loc", []) if p not in ("body", "query", "path")]
        fields.append({"field": ".".join(loc) or "request", "message": _clean_msg(err.get("msg", "Invalid value"))})
    logger.info("Validation failed on %s %s (%d field errors)", request.method, request.url.path, len(fields))
    return JSONResponse(
        status_code=422,  # Unprocessable Content
        content=_body("validation_error", "Some fields are missing or invalid.", fields),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content=_body("http_error", str(exc.detail)))


async def db_unavailable_handler(request: Request, exc: OperationalError):
    logger.error("Database unavailable on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=_body("database_unavailable", "The database is currently unavailable."),
    )


async def unhandled_error_handler(request: Request, exc: Exception):
    # Log the exception type only - never the message, which may contain data.
    logger.error("Unhandled %s on %s %s", type(exc).__name__, request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_body("internal_error", "An unexpected error occurred."),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(OperationalError, db_unavailable_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)