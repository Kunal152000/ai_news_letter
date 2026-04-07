import os
from dotenv import load_dotenv

load_dotenv()


def get_mcp_sse_url() -> str:
    """
    URL the chat agent uses to reach the MCP SSE endpoint.
    On Fly.io (or any single-host deploy), default http://127.0.0.1:$PORT/mcp/sse hits the same process.
    Set MCP_SSE_URL or PUBLIC_BASE_URL when the client must use a public URL.
    """
    explicit = (os.getenv("MCP_SSE_URL") or "").strip()
    if explicit:
        return explicit
    base = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if base:
        return f"{base}/mcp/sse"
    port = (os.getenv("PORT") or "8000").strip()
    return f"http://127.0.0.1:{port}/mcp/sse"


GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
NEWS_DATA_API_KEY = os.getenv("NEWS_DATA_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# Email: SMTP only (e.g. Gmail with an App Password)
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "AI Weekly")
SMTP_GMAIL_ADDRESS = os.getenv("SMTP_GMAIL_ADDRESS")
SMTP_GMAIL_PASSWORD = os.getenv("SMTP_GMAIL_PASSWORD")
SMTP_HOST = (os.getenv("SMTP_HOST") or "smtp.gmail.com").strip()
SMTP_MODE = (os.getenv("SMTP_MODE") or "auto").strip().lower()  # auto | starttls | ssl
_p = (os.getenv("SMTP_PORT") or "").strip()
SMTP_PORT = int(_p) if _p.isdigit() else None
try:
    SMTP_TIMEOUT = int(os.getenv("SMTP_TIMEOUT", "30"))
except ValueError:
    SMTP_TIMEOUT = 30
## Vercel static deploy (single index.html)  
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")
VERCEL_PROJECT_ID = os.getenv("VERCEL_PROJECT_ID")
VERCEL_PROJECT_NAME = os.getenv("VERCEL_PROJECT_NAME")
# VERCEL_TEAM_ID = os.getenv("VERCEL_TEAM_ID")

if not GNEWS_API_KEY:
    print("Warning: GNEWS_API_KEY is not set in the environment variables.")
if not NEWS_DATA_API_KEY:
    print("Warning: NEWS_DATA_API_KEY is not set in the environment variables.")
if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY is not set in the environment variables.")
if not EMAIL_FROM:
    print("Warning: EMAIL_FROM is not set in the environment variables.")
if not EMAIL_FROM_NAME:
    print("Warning: EMAIL_FROM_NAME is not set in the environment variables.")
if not VERCEL_TOKEN:
    print("Warning: VERCEL_TOKEN is not set in the environment variables.")
if not VERCEL_PROJECT_ID:
    print("Warning: VERCEL_PROJECT_ID is not set in the environment variables.")
if not VERCEL_PROJECT_NAME:
    print("Warning: VERCEL_PROJECT_NAME is not set in the environment variables.")
if not SMTP_GMAIL_ADDRESS:
    print("Warning: SMTP_GMAIL_ADDRESS is not set in the environment variables.")
if not SMTP_GMAIL_PASSWORD:
    print("Warning: SMTP_GMAIL_PASSWORD is not set in the environment variables.")