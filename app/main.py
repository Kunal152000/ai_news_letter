from fastapi import FastAPI
import uvicorn
from app.routes.news import router as news_router
from app.routes.chat import router as chat_router

app = FastAPI(
    title="AI Newsletter System",
    description="Backend service that fetches and filters AI-related news.",
    version="1.0.0"
)

# Include routers
app.include_router(news_router)
app.include_router(chat_router)

# To check backend is working
@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Newsletter System"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
