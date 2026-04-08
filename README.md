# AI Newsletter

Python **MCP (Model Context Protocol) server** and a small **FastAPI** chat API that fetch AI-related news, optionally rank articles with OpenRouter, render a **responsive HTML newsletter**, **deploy** it as static `index.html` on **Vercel**, and **send** mail through the **Resend** HTTP API.

---

## What runs where

| Component | Entry | Role |
| --------- | ----- | ---- |
| **MCP server** | `mcp_app.py` | `GET /mcp/sse`, `POST /mcp/messages` — tools (news, deploy, email). Deploy this as its own Render Web Service. |
| **Chat API** | `app.main:app` | `GET /`, `POST /chat` — agent talks to OpenRouter and calls MCP over SSE. Second Render Web Service. |

`app/agent.py` uses **`MCP_SSE_URL`** (default `http://127.0.0.1:8001/mcp/sse` for local MCP). On Render, set it to your MCP service, e.g. `https://ai-newsletter-mcp.onrender.com/mcp/sse`.

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

| Tool                     | Module                                                   | Notes                                                                                       |
| ------------------------ | -------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `get_news`               | `app/services/api_tools.py`                              | `GNEWS_API_KEY` and/or `NEWS_DATA_API_KEY`                                                  |
| `get_github_repos`       | `app/services/api_tools.py`                              | Unauthenticated GitHub API (rate limits apply)                                              |
| `filter_ai_news`         | `app/services/api_tools.py`                              | OpenRouter; optional `OPENROUTER_HTTP_REFERER` / `OPENROUTER_APP_TITLE` for the API         |
| `deploy_newsletter_page` | `app/services/vercel_deploy.py` + `newsletter_render.py` | `VERCEL_TOKEN`, `VERCEL_PROJECT_ID`; optional `VERCEL_PROJECT_NAME`, `VERCEL_TEAM_ID`       |
| `send_email`             | `app/services/email_sender.py`                           | Resend: `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_FROM_NAME`                                   |

MCP wiring: `app/mcp_server.py`. SSE handlers: `app/routes/mcp.py`.

---

## Environment variables

**News & filtering**

- `GNEWS_API_KEY` — GNews search.
- `NEWS_DATA_API_KEY` — NewsData.io; merged into `get_news` when set.
- `OPENROUTER_API_KEY` — Article ranking in `filter_ai_news`.
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

- `MCP_SSE_URL` — Full SSE URL for the MCP service (required in production when API and MCP are separate).
- `PORT` — Set by Render on each service; `mcp_app.py` and `app.main` read it when present.

---

## Project layout (main files)

```
ai_newsletter/
├── render.yaml                # Blueprint: two Web Services (MCP + API)
├── requirements.txt           # pip install for Render build
├── mcp_app.py                 # MCP-only ASGI (Render or local :8001)
├── app/
│   ├── main.py                # FastAPI chat API only
│   ├── agent.py               # OpenRouter + MCP client (SSE)
│   ├── mcp_server.py          # MCP tool definitions & handlers
│   ├── config/settings.py     # Env loading
│   ├── routes/
│   │   ├── mcp.py             # SSE + POST message handlers (used by mcp_app)
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

**Terminal 1 — MCP**

```bash
uv run python mcp_app.py
```

Defaults to `http://127.0.0.1:8001` (`GET /mcp/sse`).

**Terminal 2 — API**

```bash
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Chat: `POST http://127.0.0.1:8000/chat`
- Optional: `MCP_SSE_URL=http://127.0.0.1:8001/mcp/sse` in `.env` (same as default).

---

## Deploy on Render

1. Push the repo and create a **Blueprint** from `render.yaml`, or create two **Web Services** manually from the same repo.
2. **MCP service**: start command `python mcp_app.py`, root `mcp_app.py` / repo root.
3. **API service**: start command `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. On the **API** service, set **`MCP_SSE_URL`** to `https://<your-mcp-service>.onrender.com/mcp/sse`.
5. Add the same API keys and tokens to **both** services (or use a Render **Environment Group**): `GNEWS_API_KEY`, `NEWS_DATA_API_KEY`, `OPENROUTER_API_KEY`, `RESEND_API_KEY`, `EMAIL_FROM`, `VERCEL_*`, etc.

External MCP clients (e.g. Cursor) can use the public **`https://…/mcp/sse`** URL of the MCP service.

---

## Testing

```bash
uv run python test_newsletter_flow.py
```

This checks Jinja rendering, deploy input resolution, and MCP tool registration. It does not call Vercel or Resend unless you add integration tests with real credentials.

---

## Performance note

**OpenRouter**, **Vercel**, and **Resend** add network latency; tune timeouts in `api_tools.py`, `vercel_deploy.py`, and `email_sender.py` if needed.

---

## Example user request (for an MCP-aware agent)

> Send the AI newsletter to `reader@example.com`.

The agent should pick a date range, call the tools in order, deploy the HTML issue, then email a digest with **`issue_url`** and **`highlights`** from the news.
