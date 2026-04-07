from mcp.server.sse import SseServerTransport
from app.mcp_server import mcp_server

# Client POST URL must stay /mcp/messages (same origin as SSE).
sse = SseServerTransport("/mcp/messages")


async def handle_sse(scope, receive, send):
    async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())


async def handle_messages(scope, receive, send):
    await sse.handle_post_message(scope, receive, send)


class MCPSubApp:
    """
    ASGI app mounted at /mcp on FastAPI. Starlette strips the mount prefix, so paths are /sse and /messages.
    """

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
            return

        if scope["type"] != "http":
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [[b"content-type", b"text/plain"]],
                }
            )
            await send({"type": "http.response.body", "body": b"Not Found"})
            return

        path = (scope.get("path") or "").split("?", 1)[0].rstrip("/") or "/"
        if path == "/sse":
            await handle_sse(scope, receive, send)
        elif path == "/messages":
            await handle_messages(scope, receive, send)
        else:
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [[b"content-type", b"text/plain"]],
                }
            )
            await send({"type": "http.response.body", "body": b"Not Found"})


mcp_subapp = MCPSubApp()
