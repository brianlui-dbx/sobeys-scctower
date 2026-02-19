from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .core import create_app
from .router import router

app = create_app(routers=[router])


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add Cache-Control headers to GET API responses for browser-side caching."""

    async def dispatch(self, request: Request, call_next):  # type: ignore
        response: Response = await call_next(request)
        path = request.url.path
        if request.method == "GET" and path.startswith("/api/") and response.status_code == 200:
            # Skip caching for user-specific endpoints
            if "/current-user" not in path:
                response.headers["Cache-Control"] = "public, max-age=120, stale-while-revalidate=300"
        return response


app.add_middleware(CacheControlMiddleware)
