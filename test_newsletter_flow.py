"""
Local checks for newsletter render + MCP tool wiring (no real email/Vercel unless env set).
Run from repo root: uv run python test_newsletter_flow.py
"""
import asyncio
import json
import os
import sys

# Ensure app is importable when run as script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_render():
    from app.services.newsletter_render import render_newsletter_html

    news = [
        {"title": "Test headline", "description": "Short summary.", "url": "https://example.com/news"},
    ]
    repos = [{"title": "org/ai-tool", "description": "A repo.", "url": "https://github.com/org/ai-tool"}]
    html = render_newsletter_html(news, repos)
    assert "<!DOCTYPE html>" in html
    assert "Test headline" in html
    assert "org/ai-tool" in html
    print("render_newsletter_html: ok")


def test_deploy_resolver():
    from app.mcp_server import _resolve_newsletter_html

    html, err = _resolve_newsletter_html(
        {
            "news_json": json.dumps(
                [{"title": "A", "description": "B", "url": "https://example.com"}]
            ),
            "github_repos_json": "[]",
        }
    )
    assert err is None and html and "A" in html
    h2, e2 = _resolve_newsletter_html({})
    assert e2
    print("_resolve_newsletter_html: ok")


async def test_list_tools():
    from app.mcp_server import read_tools

    tools = await read_tools()
    names = {t.name for t in tools}
    for n in (
        "get_news",
        "get_github_repos",
        "filter_ai_news",
        "deploy_newsletter_page",
        "send_email",
    ):
        assert n in names, f"missing tool {n}"
    print("MCP list_tools: ok")


def main():
    test_render()
    test_deploy_resolver()
    asyncio.run(test_list_tools())
    print("All local newsletter checks passed.")


if __name__ == "__main__":
    main()
