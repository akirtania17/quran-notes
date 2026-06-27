"""Request ID middleware to tag logs and responses."""
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import set_request_id


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Inject a request id into contextvars and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        token = set_request_id(request_id)
        try:
            response = await call_next(request)
        finally:
            set_request_id(None, token)
        response.headers["X-Request-Id"] = request_id
        return response

