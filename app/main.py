import logging
import os

import uvicorn
from fastapi import FastAPI
from starlette.routing import Route

from app.routes.chat import router as chat_router
from app.routes.mcp import handle_messages, handle_sse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


class _MCPASGI:
    """Starlette Route treats plain callables as Request handlers; MCP needs raw ASGI (scope, receive, send)."""

    __slots__ = ("_handler",)

    def __init__(self, handler):
        self._handler = handler

    async def __call__(self, scope, receive, send):
        await self._handler(scope, receive, send)


app = FastAPI(
    title="AI Newsletter API",
    description="POST /chat + MCP SSE at /mcp/sse in one process.",
    version="1.0.0",
)

app.router.routes = [
    Route("/mcp/sse", endpoint=_MCPASGI(handle_sse), methods=["GET"]),
    Route("/mcp/messages", endpoint=_MCPASGI(handle_messages), methods=["POST"]),
    *app.router.routes,
]

app.include_router(chat_router)

@app.get("/")
def read_root():
    return {
        "message": "AI Newsletter API",
        "chat": "POST /chat",
        "mcp_sse": "/mcp/sse",
        "docs": "/docs",
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
