"""
Audit logging middleware.

Records every HTTP request/response pair as a structured log event so that
the full API audit trail is available without instrumenting individual endpoints.

Logged fields:
    method        HTTP method (GET / POST / …)
    path          Request path (without query string)
    query_string  Raw query string
    status_code   Response status code
    duration_ms   Total request processing time in milliseconds
    user_id       Subject extracted from the Bearer token (if present)
    client_ip     Remote address of the caller
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import decode_token_subject

logger = get_logger("audit.http")


class AuditMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that emits a structured audit log entry per request."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        if not settings.AUDIT_LOG_ENABLED:
            return await call_next(request)

        start = time.monotonic()

        # Attempt to extract user identity from the token without failing
        user_id: str | None = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):]
            user_id = decode_token_subject(token)

        response: Response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            query_string=str(request.url.query),
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=user_id or "anonymous",
            client_ip=request.client.host if request.client else "unknown",
        )
        return response
