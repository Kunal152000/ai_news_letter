from fastapi import FastAPI
import uvicorn
from app.routes.chat import router as chat_router

app = FastAPI(
    title="AI Newsletter System",
    description="Chat API backed by MCP tools (e.g. get_news).",
    version="1.0.0"
)

app.include_router(chat_router)

# To check backend is working
@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Newsletter System"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
