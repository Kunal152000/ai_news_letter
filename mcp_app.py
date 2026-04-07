"""
Optional standalone MCP server on port 8001 (SSE only).

Production / Fly.io: use a single process instead:

    uvicorn app.main:app --host 0.0.0.0 --port 8080

That serves POST /chat, GET /mcp/sse, POST /mcp/messages together.
"""
import logging

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
        if path == "/mcp/sse":
            await handle_sse(scope, receive, send)
        elif path == "/mcp/messages":
            await handle_messages(scope, receive, send)
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
    uvicorn.run(mcp_asgi_app, host="127.0.0.1", port=8001)
