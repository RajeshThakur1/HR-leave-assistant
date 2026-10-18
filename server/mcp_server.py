"""ASGI entry point for the containerised HR Leave MCP server.

Run locally:
    uvicorn server.mcp_server:app --host 0.0.0.0 --port 8000

The MCP endpoint is available at:
    http://localhost:8000/mcp
"""

from __future__ import annotations

import contextlib
import logging
from typing import Callable

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.routing import Mount, Route

from server.config import MCP_AUTH_TOKEN, MCP_SERVER_NAME, configure_logging
from server.config import HR_DB_PATH
from server.db import init_database
from server.prompts import register_prompts
from server.resources import register_resources
from server.tools import register_tools

configure_logging()
LOGGER = logging.getLogger(__name__)

mcp = FastMCP(MCP_SERVER_NAME, stateless_http=True, json_response=True)
register_tools(mcp)
register_prompts(mcp)
register_resources(mcp)

class BearerTokenMiddleware(BaseHTTPMiddleware):
    """Simple bearer-token guard for MCP HTTP requests.

    This is a classroom-friendly demonstration. Real production systems should
    use a proper identity provider and OAuth/token verification.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate Authorization header for MCP routes.

        Params:
            request: Incoming request.
            call_next: Downstream ASGI callable.

        Returns:
            Starlette response.
        """
        if request.url.path.startswith("/mcp") and MCP_AUTH_TOKEN:
            expected = f"Bearer {MCP_AUTH_TOKEN}"
            supplied = request.headers.get("Authorization", "")
            if supplied != expected:
                return JSONResponse(
                    {"status": "error", "message": "Unauthorized MCP request."},
                    status_code=401,
                )

        return await call_next(request)


async def health(_: Request) -> JSONResponse:
    """Return server health for Docker and classroom checks.

    Params:
        _: Unused Starlette request.

    Returns:
        JSON health payload.
    """

    return JSONResponse(
        {
            "status": "ok",
            "service": MCP_SERVER_NAME,
            "mcp_endpoint": "/mcp",
            "database_path": str(HR_DB_PATH),
        }
    )



@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    """Initialize database and MCP session manager.

    Params:
        app: Starlette app.

    Returns:
        Async context manager for app lifespan.
    """

    init_database(seed_if_empty=True)
    LOGGER.info("Database ready at %s", HR_DB_PATH)
    async with mcp.session_manager.run():
        LOGGER.info("MCP session manager started.")
        yield

app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Mount("/", mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)
app.add_middleware(BearerTokenMiddleware)

if __name__ == "__main__":
    import uvicorn

    from server.config import MCP_HOST, MCP_PORT

    uvicorn.run("server.mcp_server:app", host=MCP_HOST, port=MCP_PORT, reload=True)
