"""
Security headers middleware.

Adds HTTP security headers to every response, hardening the API against
common web vulnerabilities regardless of what the endpoint returns.

Headers added:
    X-Content-Type-Options        Prevent MIME-type sniffing
    X-Frame-Options               Deny clickjacking via iframes
    X-XSS-Protection              Legacy XSS filter (belt-and-suspenders)
    Strict-Transport-Security     Enforce HTTPS (1 year, includeSubDomains)
    Content-Security-Policy       Restrict resource origins
    Referrer-Policy               Limit referrer leakage
    Permissions-Policy            Disable unused browser features
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject security-related HTTP headers into every response."""

    _HEADERS: dict[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        response: Response = await call_next(request)
        for header, value in self._HEADERS.items():
            response.headers[header] = value
        return response
