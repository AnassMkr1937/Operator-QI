from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import Settings
from app.core.security import decode_access_token
from app.models.audit import AuditLog
from app.models.user import User


class AuditLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        if request.method == "OPTIONS":
            return response

        if not request.url.path.startswith("/api/v1/recommendations"):
            return response

        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()

        user: User | None = None
        session_factory = request.app.state.session_factory

        if token:
            try:
                payload = decode_access_token(token, self.settings)
                user_id = payload.get("sub")
                if user_id is not None:
                    with session_factory() as db:
                        user = db.get(User, int(user_id))
            except ValueError:
                user = None

        with session_factory() as db:
            log = AuditLog(
                user_id=user.id if user else None,
                user_email=user.email if user else None,
                user_role=user.role.value if user else None,
                action="recommendations",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                ip_address=request.client.host if request.client else None,
            )
            db.add(log)
            db.commit()

        return response
