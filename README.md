# AI Newsletter

Python **MCP (Model Context Protocol)** tools and a **FastAPI** app on one server: **`POST /chat`** (OpenRouter agent) and **`GET /mcp/sse`** + **`POST /mcp/messages`** (MCP over SSE). The stack fetches AI-related news, can rank articles with OpenRouter, renders a **responsive HTML newsletter**, **deploys** static `index.html` on **Vercel**, and **sends** mail via **Resend**.

---

## What runs where

One process: **`uvicorn app.main:app`**.

| Surface        | Paths                          | Role                                      |
| -------------- | ------------------------------ | ----------------------------------------- |
| Chat API       | `GET /`, `POST /chat`          | Agent → OpenRouter → MCP tools over SSE   |
| MCP (SSE)      | `GET /mcp/sse`, `POST /mcp/messages` | External MCP clients (e.g. Cursor)   |

`app/agent.py` uses **`MCP_SSE_URL`** when set; otherwise on Render it uses **`RENDER_EXTERNAL_URL/mcp/sse`** (same host). Locally it defaults to `http://127.0.0.1:{PORT}/mcp/sse`.

---

## End-to-end newsletter flow (agent / MCP client)

1. **`get_news`** — GNews + NewsData (`query`, `from_date`, `to_date`).
2. **`get_github_repos`** — GitHub search (`query`).
3. Merge lists; run **`filter_ai_news`** on **news articles only** (JSON array of `{title, description, url}`).
4. **`deploy_newsletter_page`** — Pass **`html_content`**, or **`news`** / **`github_repos`** arrays (or legacy `*_json` strings) for Jinja rendering (`app/templates/newsletter.html.j2`).
5. **`send_email`** — `recipients`, `subject`, plus **`issue_url`** (from deploy) and **`highlights`** for the digest, or raw **`html_content`**.

Each tool returns JSON text; failures include an `error` field where applicable.

---

## MCP tools

| Tool                     | Module                                                   | Notes                                                                                 |
| ------------------------ | -------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `get_news`               | `app/services/api_tools.py`                              | `GNEWS_API_KEY` and/or `NEWS_DATA_API_KEY`                                            |
| `get_github_repos`       | `app/services/api_tools.py`                              | Unauthenticated GitHub API (rate limits apply)                                        |
| `filter_ai_news`         | `app/services/api_tools.py`                              | OpenRouter; optional `OPENROUTER_HTTP_REFERER` / `OPENROUTER_APP_TITLE`              |
| `deploy_newsletter_page` | `app/services/vercel_deploy.py` + `newsletter_render.py` | `VERCEL_TOKEN`, `VERCEL_PROJECT_ID`; optional `VERCEL_PROJECT_NAME`, `VERCEL_TEAM_ID` |
| `send_email`             | `app/services/email_sender.py`                           | Resend: `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_FROM_NAME`                           |

MCP wiring: `app/mcp_server.py`. SSE handlers: `app/routes/mcp.py` (mounted from `app/main.py`).

---

## Environment variables

**News & filtering**

- `GNEWS_API_KEY` — GNews search.
- `NEWS_DATA_API_KEY` — NewsData.io; merged into `get_news` when set.
- `OPENROUTER_API_KEY` — Article ranking in `filter_ai_news` and the `/chat` agent.
- `OPENROUTER_HTTP_REFERER` — Optional; some OpenRouter setups expect a referer URL.
- `OPENROUTER_APP_TITLE` — Optional; sent as `X-Title` (default `AI Newsletter`).

**Email (Resend)**

- `RESEND_API_KEY` — [Resend](https://resend.com) API key.
- `EMAIL_FROM` — Verified sender in Resend (e.g. `newsletter@yourdomain.com`).
- `EMAIL_FROM_NAME` — Display name (default `AI Newsletter`).

**Deploy**

- `VERCEL_TOKEN`, `VERCEL_PROJECT_ID`, `VERCEL_PROJECT_NAME` — Vercel deployment API.
- `VERCEL_TEAM_ID` — Optional, for team-owned projects.

**Chat ↔ MCP**

- `MCP_SSE_URL` — Optional override for the SSE URL (e.g. remote MCP). If unset on Render, uses `RENDER_EXTERNAL_URL/mcp/sse`.
- `PORT` — Set by Render; uvicorn and settings use it.

---

## Project layout (main files)

```
ai_newsletter/
├── render.yaml
├── requirements.txt           # pip install for Render build
├── app/
│   ├── main.py                # FastAPI: /chat + MCP routes
│   ├── agent.py               # OpenRouter + MCP client (SSE)
│   ├── mcp_server.py          # MCP tool definitions & handlers
│   ├── config/settings.py     # Env loading
│   ├── routes/
│   │   ├── mcp.py             # SSE + POST message handlers
│   │   └── chat.py            # POST /chat
│   ├── services/
│   │   ├── api_tools.py
│   │   ├── email_sender.py
│   │   ├── vercel_deploy.py
│   │   ├── newsletter_render.py
│   │   └── fetch_news_NewsData.py
│   └── templates/
│       └── newsletter.html.j2
├── test_newsletter_flow.py
├── pyproject.toml
└── README.md
```

---

## Setup

Requires **Python ≥ 3.12** and **[uv](https://github.com/astral-sh/uv)**.

```bash
uv sync
```

Create a `.env` in the project root. Do not commit `.env`.

---

## Running (local)

```bash
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Chat: `POST http://127.0.0.1:8000/chat`
- MCP SSE: `http://127.0.0.1:8000/mcp/sse` (same origin as chat; no extra `MCP_SSE_URL` needed).

---

## Deploy on Render

1. Create one **Web Service** from this repo.
2. Start command: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Do **not** set `MCP_SSE_URL` unless MCP must live on another host; Render provides `RENDER_EXTERNAL_URL`.
4. Add API keys: `GNEWS_API_KEY`, `NEWS_DATA_API_KEY`, `OPENROUTER_API_KEY`, `RESEND_API_KEY`, `EMAIL_FROM`, `VERCEL_*`, etc.

External MCP clients can use **`https://<your-service>.onrender.com/mcp/sse`**.

---

## Testing

```bash
uv run python test_newsletter_flow.py
```

Checks Jinja rendering, deploy input resolution, and MCP tool registration (no real Vercel/Resend unless credentials are set).

---

## Performance note

**OpenRouter**, **Vercel**, and **Resend** add network latency; tune timeouts in `api_tools.py`, `vercel_deploy.py`, and `email_sender.py` if needed.

---

## Example user request (for an MCP-aware agent)

> Send the AI newsletter to `reader@example.com`.

The agent should pick a date range, call the tools in order, deploy the HTML issue, then email a digest with **`issue_url`** and **`highlights`** from the news.
