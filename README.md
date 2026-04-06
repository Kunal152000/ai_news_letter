# AI Newsletter

Python backend and **MCP (Model Context Protocol) server** that fetch AI-related news, optionally rank it with an LLM, render a **responsive HTML newsletter**, **deploy** it as static `index.html` on **Vercel**, and **send** it by email (SMTP or SendGrid).

---

## What runs where

| Component             | Entry          | Port (default) | Role                                                       |
| --------------------- | -------------- | -------------- | ---------------------------------------------------------- |
| **FastAPI app**       | `app.main:app` | `8000`         | REST: `/chat` (MCP-backed agent)                           |
| **MCP over HTTP/SSE** | `mcp_app.py`   | `8001`         | MCP tools for clients (Cursor, Claude Code, custom agents) |

The chat route (`app/routes/chat.py`) uses `app/agent.py`, which connects to the MCP server at `http://127.0.0.1:8001/mcp/sse`. For full newsletter flows, **start the MCP server first**, then the API.

---

## End-to-end newsletter flow (agent / MCP client)

1. **`get_news`** — GNews API (`query`, `from_date`, `to_date`).
2. **`get_github_repos`** — GitHub search (`query`).
3. Merge lists; run **`filter_ai_news`** on **news articles only** (JSON array of `{title, description, url}`).
4. **`deploy_newsletter_page`** — Either:
   - pass **`html_content`** (full page), or
   - pass **`news_json`** and optional **`github_repos_json`** so the server renders with **Jinja2** (`app/templates/newsletter.html.j2`).
5. **`send_email`** — `recipients`, `subject`, `html_content` (short summary + link to `public_url` from step 4).

Each tool returns JSON text; failures include an `error` field where applicable.

---

## MCP tools

| Tool                     | Module                                                   | Notes                                                                                       |
| ------------------------ | -------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `get_news`               | `app/services/api_tools.py`                              | `GNEWS_API_KEY` and/or `NEWS_DATA_API_KEY`                                                  |
| `get_github_repos`       | `app/services/api_tools.py`                              | Unauthenticated GitHub API (rate limits apply)                                              |
| `filter_ai_news`         | `app/services/api_tools.py`                              | OpenRouter; needs `OPENROUTER_API_KEY` (otherwise returns input unchanged)                  |
| `deploy_newsletter_page` | `app/services/vercel_deploy.py` + `newsletter_render.py` | Needs `VERCEL_TOKEN`, `VERCEL_PROJECT_ID`; optional `VERCEL_PROJECT_NAME`, `VERCEL_TEAM_ID` |
| `send_email`             | `app/services/email_sender.py`                           | SendGrid if `SENDGRID_API_KEY`, else SMTP (`EMAIL_USER`, `EMAIL_PASS`)                      |

MCP wiring lives in `app/mcp_server.py`; SSE routes in `app/routes/mcp.py`.

---

## Environment variables

**News & filtering**

- `GNEWS_API_KEY` — GNews search.
- `OPENROUTER_API_KEY` — Article ranking in `filter_ai_news`.
- `NEWS_DATA_API_KEY` — NewsData.io; merged into `get_news` with GNews when set.

**Email**

- `SENDGRID_API_KEY` — If set, mail is sent via SendGrid.
- Otherwise **SMTP**: `EMAIL_USER`, `EMAIL_PASS`, optional `EMAIL_SMTP_HOST` (default `smtp.gmail.com`), `EMAIL_SMTP_PORT` (default `587`), `EMAIL_FROM`, `EMAIL_FROM_NAME`.

**Vercel**

- `VERCEL_TOKEN` — Bearer token.
- `VERCEL_PROJECT_ID` — Target project (e.g. `prj_...`).
- `VERCEL_PROJECT_NAME` — Project name/slug for the deployments API (if omitted, the code tries to resolve it via the Vercel API).
- `VERCEL_TEAM_ID` — Optional, for team-owned projects.

---

## Project layout (main files)

```
ai_newsletter/
├── mcp_app.py                 # ASGI entry: MCP SSE on :8001
├── app/
│   ├── main.py                # FastAPI app
│   ├── agent.py               # OpenRouter + MCP client (multi-round tools)
│   ├── mcp_server.py          # MCP tool definitions & handlers
│   ├── config/settings.py     # Env loading
│   ├── routes/
│   │   ├── mcp.py             # /mcp/sse, /mcp/messages
│   │   └── chat.py            # POST /chat
│   ├── services/
│   │   ├── api_tools.py       # get_news, get_github_repos, filter_ai_news
│   │   ├── email_sender.py
│   │   ├── vercel_deploy.py
│   │   ├── newsletter_render.py
│   │   └── fetch_news_NewsData.py
│   ├── templates/
│   │   └── newsletter.html.j2
│   └── utils/filters.py
├── test_newsletter_flow.py    # Local smoke tests (render + MCP tool list)
├── pyproject.toml
└── README.md
```

---

## Setup

Requires **Python ≥ 3.12** and **[uv](https://github.com/astral-sh/uv)**.

```bash
uv sync
```

Create a `.env` in the project root with the variables you need (see above). Do not commit `.env`.

---

## Running

**MCP server (required for tool-using chat):**

```bash
uv run python mcp_app.py
```

**FastAPI API:**

```bash
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

On some Windows setups, `uv run uvicorn ...` fails with `uv trampoline failed to canonicalize script path`. Using `python -m uvicorn` avoids that. Alternatively: `.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.

**Cursor / Claude Code:** Point the MCP client at the SSE URL your deployment exposes (locally: `http://127.0.0.1:8001/mcp/sse`), using the transport your client expects (HTTP+SSE as implemented here).

---

## Testing

```bash
uv run python test_newsletter_flow.py
```

This checks Jinja rendering, deploy input resolution, and that all five MCP tools are registered. It does **not** call Vercel or send mail unless you build separate integration tests with real credentials.

---

## Performance note

The original design target was a very fast end-to-end run; in practice **OpenRouter**, **Vercel**, and **SMTP/SendGrid** latency often push total time above a few seconds. Tune timeouts in `api_tools.py` / `vercel_deploy.py` / `email_sender.py` if needed.

---

## Example user request (for an MCP-aware agent)

> Send AI newsletter to these emails: `reader@example.com`

The agent should compute a recent date range, call the tools in order, then send email HTML that summarizes the issue and links to the deployed `public_url`.
