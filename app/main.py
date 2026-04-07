import logging

import uvicorn
from fastapi import FastAPI

from app.routes.chat import router as chat_router
from app.routes.mcp import mcp_subapp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="AI Newsletter System",
    description="Chat API + MCP over HTTP/SSE on the same service (/mcp/sse, /mcp/messages).",
    version="1.0.0",
)

app.include_router(chat_router)
app.mount("/mcp", mcp_subapp)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the AI Newsletter System",
        "mcp_sse": "/mcp/sse",
        "chat": "POST /chat",
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
