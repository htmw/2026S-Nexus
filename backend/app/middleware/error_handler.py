import logging
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

DEFAULT_ERROR_MESSAGE = "Something went wrong. Please try again."


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled server error",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                },
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "internal_server_error",
                        "message": DEFAULT_ERROR_MESSAGE,
                        "request_id": request_id,
                    }
                },
                headers={"X-Request-ID": request_id},
            )

        response.headers.setdefault("X-Request-ID", request_id)
        return response
