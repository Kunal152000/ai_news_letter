import logging
import os

import uvicorn
from fastapi import FastAPI

from app.routes.chat import router as chat_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="AI Newsletter API",
    description="Chat API. MCP runs as a separate process (see mcp_app.py / Render).",
    version="1.0.0",
)

app.include_router(chat_router)


@app.get("/")
def read_root():
    return {
        "message": "AI Newsletter API",
        "chat": "POST/chat",
        "docs": "/docs",
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
