import os
from dotenv import load_dotenv

load_dotenv()

GNEWS_API_KEY = (os.getenv("GNEWS_API_KEY") or "").strip()
NEWS_DATA_API_KEY = (os.getenv("NEWS_DATA_API_KEY") or "").strip()
OPENROUTER_API_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip()
OPENROUTER_HTTP_REFERER = (os.getenv("OPENROUTER_HTTP_REFERER") or "").strip()
OPENROUTER_APP_TITLE = (os.getenv("OPENROUTER_APP_TITLE") or "AI Newsletter").strip()
_IS_RENDER = (os.getenv("RENDER") or "").lower() in ("true", "1", "yes")

# Chat agent connects to MCP over HTTP/SSE. Priority:
# 1) MCP_SSE_URL if set
# 2) On Render only: same-service URL from RENDER_EXTERNAL_URL (MCP mounted on app.main at /mcp/sse)
# 3) Local dev: http://127.0.0.1:{PORT}/mcp/sse (same uvicorn as /chat)
# For a remote MCP service only, set MCP_SSE_URL to its public /mcp/sse URL.
_explicit_mcp = (os.getenv("MCP_SSE_URL") or "").strip()
_render_external = (os.getenv("RENDER_EXTERNAL_URL") or "").strip().rstrip("/")
_local_port = (os.getenv("PORT") or "8000").strip()

if _explicit_mcp:
    MCP_SSE_URL = _explicit_mcp
elif _render_external and _IS_RENDER:
    MCP_SSE_URL = f"{_render_external}/mcp/sse"
else:
    MCP_SSE_URL = f"http://127.0.0.1:{_local_port}/mcp/sse"
_MCP_IS_LOCAL = "127.0.0.1" in MCP_SSE_URL or "localhost" in MCP_SSE_URL.lower()
if _IS_RENDER and _MCP_IS_LOCAL:
    print(
        "ERROR: On Render, MCP_SSE_URL must be a public https URL (or unset to use RENDER_EXTERNAL_URL). "
        "Do not use localhost on the API service."
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
