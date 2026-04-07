import logging
import os

import uvicorn
from fastapi import FastAPI

from app.routes.chat import router as chat_router
from app.routes.mcp import mcp_subapp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="AI Newsletter API",
    description="POST /chat + MCP SSE at /mcp/sse (same process). Optional: python mcp_app.py for MCP-only.",
    version="1.0.0",
)

app.include_router(chat_router)
app.mount("/mcp", mcp_subapp)


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
