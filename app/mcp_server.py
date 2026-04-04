import json
import logging

from mcp.server import Server
from mcp.types import TextContent, Tool

from app.services.api_tools import filter_ai_news, get_github_repos, get_news
from app.services.email_sender import send_email
from app.services.newsletter_render import render_newsletter_html
from app.services.vercel_deploy import deploy_newsletter_page

logger = logging.getLogger(__name__)

mcp_server = Server("ai-news-mcp")

_NEWSLETTER_FLOW = (
    "Newsletter pipeline: (1) get_news (2) get_github_repos (3) filter_ai_news on the news articles only (4) merge news + repos lists"
    "(5) deploy_newsletter_page with news_json "
    "and github_repos_json OR prebuilt html_content (6) send_email with a short HTML summary "
    "and link to deploy result public_url."
)


@mcp_server.list_tools()
async def read_tools():
    return [
        Tool(
            name="get_news",
            description="Fetch AI news from GNews and NewsData.io (merged, URL-deduped) for the query and date range.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for news."},
                    "from_date": {"type": "string", "description": "Start date in YYYY-MM-DD format."},
                    "to_date": {"type": "string", "description": "End date in YYYY-MM-DD format."},
                },
                "required": ["query", "from_date", "to_date"],
            },
        ),
        Tool(
            name="get_github_repos",
            description="Fetch AI-related GitHub repositories. " + _NEWSLETTER_FLOW,
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "GitHub search query (e.g., 'topic:machine-learning sort:updated').",
                    }
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="filter_ai_news",
            description="Filter and rank news articles (pass news items only, not GitHub repos). "
            + _NEWSLETTER_FLOW,
            inputSchema={
                "type": "object",
                "properties": {
                    "articles_json": {
                        "type": "string",
                        "description": "JSON array of objects with title, description, url.",
                    }
                },
                "required": ["articles_json"],
            },
        ),
        Tool(
            name="deploy_newsletter_page",
            description=(
                "Deploy static newsletter HTML to Vercel (existing project). "
                "Either pass html_content OR pass news_json (array JSON string) to render with Jinja2; "
                "github_repos_json optional. Returns public_url. "
            )
            + _NEWSLETTER_FLOW,
            inputSchema={
                "type": "object",
                "properties": {
                    "html_content": {
                        "type": "string",
                        "description": "Full HTML document. If empty, news_json is required.",
                    },
                    "news_json": {
                        "type": "string",
                        "description": "JSON array of {title, description, url} for server-side template render.",
                    },
                    "github_repos_json": {
                        "type": "string",
                        "description": "Optional JSON array of {title, description, url} (GitHub repos).",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="send_email",
            description="Send HTML email via SendGrid (if SENDGRID_API_KEY) or SMTP. " + _NEWSLETTER_FLOW,
            inputSchema={
                "type": "object",
                "properties": {
                    "recipients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Recipient email addresses.",
                    },
                    "subject": {"type": "string"},
                    "html_content": {"type": "string", "description": "HTML body (e.g. summary + link)."},
                },
                "required": ["recipients", "subject", "html_content"],
            },
        ),
    ]


def _resolve_newsletter_html(arguments: dict) -> tuple[str | None, str | None]:
    raw_html = (arguments.get("html_content") or "").strip()
    if raw_html:
        return raw_html, None
    news_json = arguments.get("news_json")
    if not news_json or not str(news_json).strip():
        return None, "Provide html_content or news_json"
    try:
        news = json.loads(news_json)
        if not isinstance(news, list):
            return None, "news_json must be a JSON array"
    except json.JSONDecodeError as e:
        return None, f"Invalid news_json: {e}"

    repos = []
    gh = arguments.get("github_repos_json")
    if gh and str(gh).strip():
        try:
            parsed = json.loads(gh)
            if isinstance(parsed, list):
                repos = parsed
            else:
                return None, "github_repos_json must be a JSON array"
        except json.JSONDecodeError as e:
            return None, f"Invalid github_repos_json: {e}"

    try:
        html = render_newsletter_html(news, repos)
    except Exception as e:
        logger.exception("render_newsletter_html")
        return None, str(e)
    return html, None


@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    arguments = arguments or {}

    if name == "get_news":
        try:
            articles = get_news(
                arguments.get("query"),
                arguments.get("from_date"),
                arguments.get("to_date"),
            )
            logger.info("get_news: %s articles", len(articles))
            return [TextContent(type="text", text=json.dumps(articles))]
        except Exception as e:
            logger.exception("get_news")
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    if name == "get_github_repos":
        try:
            repos = get_github_repos(arguments.get("query"))
            logger.info("get_github_repos: %s repos", len(repos))
            return [TextContent(type="text", text=json.dumps(repos))]
        except Exception as e:
            logger.exception("get_github_repos")
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    if name == "filter_ai_news":
        try:
            parsed = json.loads(arguments.get("articles_json") or "[]")
            filtered = filter_ai_news(parsed)
            logger.info("filter_ai_news: %s items", len(filtered))
            return [TextContent(type="text", text=json.dumps(filtered))]
        except Exception as e:
            logger.exception("filter_ai_news")
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    if name == "deploy_newsletter_page":
        try:
            html, err = _resolve_newsletter_html(arguments)
            if err:
                return [TextContent(type="text", text=json.dumps({"success": False, "error": err}))]
            out = deploy_newsletter_page(html)
            logger.info("deploy_newsletter_page: success=%s", out.get("success"))
            return [TextContent(type="text", text=json.dumps(out))]
        except Exception as e:
            logger.exception("deploy_newsletter_page")
            return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}))]

    if name == "send_email":
        try:
            recipients = arguments.get("recipients") or []
            subject = arguments.get("subject") or ""
            body = arguments.get("html_content") or ""
            out = send_email(recipients, subject, body)
            logger.info("send_email: success=%s provider=%s", out.get("success"), out.get("provider"))
            return [TextContent(type="text", text=json.dumps(out))]
        except Exception as e:
            logger.exception("send_email")
            return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}))]

    raise ValueError(f"Unknown tool: {name}")
