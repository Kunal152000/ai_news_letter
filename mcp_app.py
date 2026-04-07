"""
Standalone MCP server (SSE) for Render or local dev.

Serve with: python mcp_app.py  (uses PORT from env on Render, default 8001 locally)
"""
import json
import logging
import os

import uvicorn

from app.routes.mcp import handle_messages, handle_sse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


async def mcp_asgi_app(scope, receive, send):
    if scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return

    if scope["type"] == "http":
        path = scope["path"]
        if path == "/":
            body = json.dumps({"service": "mcp", "sse": "/mcp/sse"}).encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"application/json"]],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return
        if path == "/mcp/sse":
            await handle_sse(scope, receive, send)
        elif path == "/mcp/messages":
            await handle_messages(scope, receive, send)
        elif path in ("/chat", "/api/chat"):
            # Common mistake: MCP and API are separate Render services; /chat lives on FastAPI only.
            hint = (
                "This URL is the MCP server (tools + SSE). "
                "POST /chat is on your API Web Service: startCommand must run "
                "`python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT` and use that service’s hostname."
            )
            body = json.dumps({"detail": "Not Found", "hint": hint}).encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [[b"content-type", b"application/json"]],
                }
            )
            await send({"type": "http.response.body", "body": body})
        else:
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [[b"content-type", b"text/plain"]],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b"Not Found",
                }
            )


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8001"))
    uvicorn.run(mcp_asgi_app, host=host, port=port)
