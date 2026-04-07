import os
from dotenv import load_dotenv

load_dotenv()

GNEWS_API_KEY = (os.getenv("GNEWS_API_KEY") or "").strip()
NEWS_DATA_API_KEY = (os.getenv("NEWS_DATA_API_KEY") or "").strip()
OPENROUTER_API_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip()
OPENROUTER_HTTP_REFERER = (os.getenv("OPENROUTER_HTTP_REFERER") or "").strip()
OPENROUTER_APP_TITLE = (os.getenv("OPENROUTER_APP_TITLE") or "AI Newsletter").strip()
MCP_SSE_URL = (os.getenv("MCP_SSE_URL") or "").strip()

_IS_RENDER = (os.getenv("RENDER") or "").lower() in ("true", "1", "yes")
_MCP_IS_LOCAL = "127.0.0.1" in MCP_SSE_URL or "localhost" in MCP_SSE_URL.lower()
if _IS_RENDER and _MCP_IS_LOCAL:
    print(
        "ERROR: On Render, MCP_SSE_URL must be your MCP service HTTPS URL "
        "(e.g. https://your-mcp-service.onrender.com/mcp/sse), not localhost. "
        "Set MCP_SSE_URL in the API service Environment tab."
    )
RESEND_API_KEY = (os.getenv("RESEND_API_KEY") or "").strip()
EMAIL_FROM = (os.getenv("EMAIL_FROM") or "").strip()
EMAIL_FROM_NAME = (os.getenv("EMAIL_FROM_NAME") or "AI Newsletter").strip()

VERCEL_TOKEN = (os.getenv("VERCEL_TOKEN") or "").strip()
VERCEL_PROJECT_ID = (os.getenv("VERCEL_PROJECT_ID") or "").strip()
VERCEL_PROJECT_NAME = (os.getenv("VERCEL_PROJECT_NAME") or "").strip()
VERCEL_TEAM_ID = (os.getenv("VERCEL_TEAM_ID") or "").strip()

if not GNEWS_API_KEY:
    print("Warning: GNEWS_API_KEY is not set in the environment variables.")
if not NEWS_DATA_API_KEY:
    print("Warning: NEWS_DATA_API_KEY is not set in the environment variables.")
if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY is not set in the environment variables.")
if not RESEND_API_KEY:
    print("Warning: RESEND_API_KEY is not set in the environment variables.")
if not EMAIL_FROM:
    print("Warning: EMAIL_FROM is not set in the environment variables.")
if not VERCEL_TOKEN:
    print("Warning: VERCEL_TOKEN is not set in the environment variables.")
if not VERCEL_PROJECT_ID:
    print("Warning: VERCEL_PROJECT_ID is not set in the environment variables.")
if not VERCEL_PROJECT_NAME:
    print("Warning: VERCEL_PROJECT_NAME is not set in the environment variables.")
