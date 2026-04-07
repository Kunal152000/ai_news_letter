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

# Shared JSON-Schema fragment for news/repo rows (avoid nested JSON strings in tool args).
_ARTICLE_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "url": {"type": "string"},
    },
}


def _coerce_article_list(arguments: dict, *, array_key: str, json_key: str) -> tuple[list | None, str | None]:
    """Prefer native JSON array on the tool call; fall back to legacy JSON string."""
    raw = arguments.get(array_key)
    if raw is not None:
        if isinstance(raw, list):
            return raw, None
        return None, f"{array_key} must be a JSON array, not {type(raw).__name__}"
    blob = arguments.get(json_key)
    if blob is not None and str(blob).strip():
        try:
            data = json.loads(blob) if isinstance(blob, str) else blob
        except json.JSONDecodeError as e:
            return None, f"Invalid {json_key} (malformed JSON, often caused by quotes in URLs): {e}"
        if isinstance(data, list):
            return data, None
        return None, f"{json_key} must be a JSON array"
    return None, None

_NEWSLETTER_FLOW = (
    "Newsletter pipeline: (1) get_news (2) get_github_repos (3) filter_ai_news with `articles` array "
    "(4) deploy_newsletter_page with `news` array + optional `github_repos` or html_content "
    "(5) send_email with summary + public_url. Use JSON arrays for article lists, not stringified JSON."
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
            description=(
                "Filter and rank news articles (news only, not GitHub repos). "
                "IMPORTANT: pass `articles` as a JSON array of objects (title, description, url). "
                "Do NOT use a string field with JSON inside it—URLs break escaping. "
                + _NEWSLETTER_FLOW
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "articles": {
                        "type": "array",
                        "description": "Output of get_news (array of {title, description, url}).",
                        "items": _ARTICLE_ITEM_SCHEMA,
                    },
                    "articles_json": {
                        "type": "string",
                        "description": "Legacy only: escaped JSON array string. Prefer `articles`.",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="deploy_newsletter_page",
            description=(
                "Deploy static newsletter HTML to Vercel (existing project). "
                "Either pass html_content OR pass `news` as a JSON array for Jinja render; "
                "optional `github_repos` array. Prefer arrays over news_json/github_repos_json strings. "
                "Returns public_url. "
            )
            + _NEWSLETTER_FLOW,
            inputSchema={
                "type": "object",
                "properties": {
                    "html_content": {
                        "type": "string",
                        "description": "Full HTML document. If empty, pass `news` array.",
                    },
                    "news": {
                        "type": "array",
                        "description": "Filtered news rows {title, description, url}.",
                        "items": _ARTICLE_ITEM_SCHEMA,
                    },
                    "github_repos": {
                        "type": "array",
                        "description": "Optional GitHub rows {title, description, url}.",
                        "items": _ARTICLE_ITEM_SCHEMA,
                    },
                    "news_json": {
                        "type": "string",
                        "description": "Legacy: JSON array string. Prefer `news`.",
                    },
                    "github_repos_json": {
                        "type": "string",
                        "description": "Legacy: JSON array string. Prefer `github_repos`.",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="send_email",
            description=(
                "Send email via Resend (RESEND_API_KEY, EMAIL_FROM). Prefer issue_url from deploy_newsletter_page "
                "plus highlights[] (4–8 teaser lines from live news) to fill the email's 'quick preview' block; "
                "optional html_content appends after the preview. Or send raw html_content only without issue_url. "
            )
            + _NEWSLETTER_FLOW,
            inputSchema={
                "type": "object",
                "properties": {
                    "recipients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Recipient email addresses.",
                    },
                    "subject": {"type": "string"},
                    "issue_url": {
                        "type": "string",
                        "description": "public_url from deploy_newsletter_page. Wraps body in a welcoming template + CTA.",
                    },
                    "highlights": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "4–8 lines shown under 'Here’s a quick preview' (real headlines/summaries from this issue).",
                    },
                    "issue_title": {
                        "type": "string",
                        "description": "Optional email headline (default: friendly generic title).",
                    },
                    "html_content": {
                        "type": "string",
                        "description": "Optional extra HTML block inside the digest, or sole body if issue_url omitted.",
                    },
                },
                "required": ["recipients", "subject"],
            },
        ),
    ]


def _resolve_newsletter_html(arguments: dict) -> tuple[str | None, str | None]:
    raw_html = (arguments.get("html_content") or "").strip()
    if raw_html:
        return raw_html, None

    news, nerr = _coerce_article_list(arguments, array_key="news", json_key="news_json")
    if nerr:
        return None, nerr
    if not news:
        return None, "Provide html_content, or `news` as a JSON array (or legacy news_json)"

    repos, gerr = _coerce_article_list(arguments, array_key="github_repos", json_key="github_repos_json")
    if gerr:
        return None, gerr
    repos = repos or []

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
            articles, err = _coerce_article_list(arguments, array_key="articles", json_key="articles_json")
            if err:
                return [TextContent(type="text", text=json.dumps({"error": err}))]
            if articles is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": "Missing articles: pass `articles` as a JSON array from get_news "
                                "(do not stringify the array)."
                            }
                        ),
                    )
                ]
            normalized = []
            for a in articles:
                if not isinstance(a, dict):
                    continue
                normalized.append(
                    {
                        "title": str(a.get("title", "") or ""),
                        "description": str(a.get("description", "") or ""),
                        "url": str(a.get("url", "") or ""),
                    }
                )
            filtered = filter_ai_news(normalized)
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
            body = arguments.get("html_content")
            issue_url = arguments.get("issue_url")
            highlights = arguments.get("highlights")
            issue_title = arguments.get("issue_title")
            if highlights is not None and not isinstance(highlights, list):
                highlights = None
            out = send_email(
                recipients,
                subject,
                body,
                issue_url=issue_url,
                highlights=highlights,
                issue_title=issue_title,
            )
            logger.info("send_email: success=%s provider=%s", out.get("success"), out.get("provider"))
            return [TextContent(type="text", text=json.dumps(out))]
        except Exception as e:
            logger.exception("send_email")
            return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}))]

    raise ValueError(f"Unknown tool: {name}")
