from fastapi import Request, Response
from mcp.server.sse import SseServerTransport
from app.mcp_server import mcp_server

sse = SseServerTransport("/mcp/messages")

async def handle_sse(scope, receive, send):
    async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())

async def handle_messages(scope, receive, send):
    await sse.handle_post_message(scope, receive, send)
