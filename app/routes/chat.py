import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agent import process_chat_query

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    An agent endpoint that takes a user query, dynamically figures
    out which tools to hit via the local MCP server, and generates an answer.
    """
    try:
        answer = await process_chat_query(req.query)
        return ChatResponse(response=answer)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
