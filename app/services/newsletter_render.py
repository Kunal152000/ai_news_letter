"""
Jinja2 rendering for the static newsletter HTML shell (layout fixed; content injected).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config.settings import NEWSLETTER_SITE_URL

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    enable_async=False,
)


def render_newsletter_html(
    news_items: list[dict[str, Any]],
    github_items: list[dict[str, Any]] | None = None,
    *,
    issue_title: str = "AI Weekly",
    published_at: str | None = None,
    site_url: str | None = None,
) -> str:
    """
    Build a full HTML document from structured tool outputs (title, description, url).
    """
    github_items = github_items or []
    if published_at is None:
        published_at = datetime.now(timezone.utc).strftime("%B %d, %Y")
    site = site_url or NEWSLETTER_SITE_URL or ""

    try:
        tpl = _env.get_template("newsletter.html.j2")
        html = tpl.render(
            issue_title=issue_title,
            published_at=published_at,
            top_news=news_items,
            github_tools=github_items,
            site_url=site,
        )
        logger.debug("render_newsletter_html: %s news, %s repos", len(news_items), len(github_items))
        return html
    except Exception as e:
        logger.exception("render_newsletter_html failed")
        raise RuntimeError(f"Template render failed: {e}") from e
