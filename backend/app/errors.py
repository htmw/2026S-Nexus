import logging

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, message: str, code: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


def json_error(status_code: int, error: str, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "code": code},
    )


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    if exc.status_code >= 500:
        logger.exception("Application error: %s (%s)", exc.message, exc.code)
    else:
        logger.warning("Application error: %s (%s)", exc.message, exc.code)
    return json_error(exc.status_code, exc.message, exc.code)


async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 401:
        return json_error(401, "Unauthorized", "unauthorized")
    if exc.status_code == 404:
        return json_error(404, "Not found", "not_found")
    if exc.status_code == 400:
        return json_error(400, str(exc.detail or "Invalid request"), "bad_request")
    if exc.status_code == 403:
        return json_error(403, str(exc.detail or "Forbidden"), "forbidden")
    return json_error(exc.status_code, str(exc.detail or "Request failed"), "http_error")


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(
        str(part)
        for part in first_error.get("loc", ())
        if part not in {"body", "query", "path"}
    )
    message = str(first_error.get("msg", "Invalid request"))
    if location:
        message = f"{location}: {message}"
    return json_error(400, message, "validation_error")


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled error during %s %s",
        request.method,
        request.url.path,
    )
    return json_error(500, "Something went wrong on our side.", "internal_server_error")
