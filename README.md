# AI Newsletter

Python backend and **MCP (Model Context Protocol) server** that fetch AI-related news, optionally rank it with an LLM, render a **responsive HTML newsletter**, **deploy** it as static `index.html` on **Vercel**, and **send** it by email over **SMTP** (e.g. Gmail + App Password).

---

## What runs where

| Component | Entry | Role |
| --------- | ----- | ---- |
| **Unified app (recommended)** | `app.main:app` | `GET /`, `POST /chat`, **`GET /mcp/sse`**, **`POST /mcp/messages`** — one process (local, **Fly.io**, Docker). |

`app/agent.py` calls MCP at **`http://127.0.0.1:$PORT/mcp/sse`** by default (same machine). Override with **`MCP_SSE_URL`** or **`PUBLIC_BASE_URL`** if needed.

Optional legacy: **`mcp_app.py`** runs MCP only on port `8001` for local debugging.

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
| `send_email`             | `app/services/email_sender.py`                           | SMTP: `SMTP_GMAIL_ADDRESS`, `SMTP_GMAIL_PASSWORD`, `EMAIL_FROM`, etc. (see below)          |

MCP wiring lives in `app/mcp_server.py`; SSE routes in `app/routes/mcp.py`.

---

## Environment variables

**News & filtering**

- `GNEWS_API_KEY` — GNews search.
- `OPENROUTER_API_KEY` — Article ranking in `filter_ai_news`.
- `NEWS_DATA_API_KEY` — NewsData.io; merged into `get_news` with GNews when set.

**Email (SMTP only)**

- `SMTP_GMAIL_ADDRESS` — Gmail address used to sign in to SMTP.
- `SMTP_GMAIL_PASSWORD` — [Gmail App Password](https://support.google.com/accounts/answer/185833) (not your normal password).
- `EMAIL_FROM` — Required by the app; usually the same as `SMTP_GMAIL_ADDRESS`.
- `EMAIL_FROM_NAME` — Display name (default `AI Weekly`).
- `SMTP_HOST` — Default `smtp.gmail.com`.
- `SMTP_MODE` — `auto` (default: try port **587 STARTTLS**, then **465 SSL**), `starttls`, or `ssl`.
- `SMTP_PORT` — Optional override when using `starttls` or `ssl` mode.
- `SMTP_TIMEOUT` — Seconds (default `30`).

**Deploy / MCP URL**

- `PORT` — Listen port (default `8000` locally; **Fly.io sets this**, usually `8080`).
- `MCP_SSE_URL` — Full SSE URL if the agent must not use loopback (rare on single-host deploys).
- `PUBLIC_BASE_URL` — e.g. `https://your-app.fly.dev`; agent uses `{PUBLIC_BASE_URL}/mcp/sse` when set and `MCP_SSE_URL` is unset.

**Vercel**

- `VERCEL_TOKEN` — Bearer token.
- `VERCEL_PROJECT_ID` — Target project (e.g. `prj_...`).
- `VERCEL_PROJECT_NAME` — Project name/slug for the deployments API (if omitted, the code tries to resolve it via the Vercel API).
- `VERCEL_TEAM_ID` — Optional, for team-owned projects.

---

## Project layout (main files)

```
ai_newsletter/
├── Dockerfile
├── fly.toml
├── mcp_app.py                 # Optional: MCP-only dev server on :8001
├── app/
│   ├── main.py                # FastAPI + MCP mount at /mcp
│   ├── agent.py               # OpenRouter + MCP client (multi-round tools)
│   ├── mcp_server.py          # MCP tool definitions & handlers
│   ├── config/settings.py     # Env loading
│   ├── routes/
│   │   ├── mcp.py             # MCP ASGI handlers + mount sub-app
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

## Running (local)

**Single process (chat + MCP):**

```bash
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Chat: `POST http://127.0.0.1:8000/chat`
- MCP SSE: `http://127.0.0.1:8000/mcp/sse`

On some Windows setups, `uv run uvicorn ...` fails; use `python -m uvicorn` as above.

**Optional:** `uv run python mcp_app.py` — MCP only on `http://127.0.0.1:8001/mcp/sse` (then set `MCP_SSE_URL` for `/chat`).

## Deploy on Fly.io

1. Install [flyctl](https://fly.io/docs/hands-on/install-flyctl/), log in.
2. Edit **`fly.toml`** → set `app = "your-unique-app-name"`.
3. From the repo root:

```bash
fly launch --no-deploy   # merge generated config with existing fly.toml if prompted
fly secrets set GNEWS_API_KEY=... OPENROUTER_API_KEY=... SMTP_GMAIL_ADDRESS=... SMTP_GMAIL_PASSWORD=... EMAIL_FROM=... VERCEL_TOKEN=... VERCEL_PROJECT_ID=... VERCEL_PROJECT_NAME=...
fly deploy
```

4. Open **`https://<your-app>.fly.dev`** — health `GET /`. MCP clients: **`https://<your-app>.fly.dev/mcp/sse`**.

The **Dockerfile** uses `uv sync` and listens on **`PORT`** (Fly sets this to match `internal_port` in `fly.toml`, default **8080**).

Gmail SMTP from Fly machines is generally allowed on ports **587/465** (unlike Render’s free tier, which blocks outbound SMTP).

**Cursor / Claude Code:** Use your public **`https://…/mcp/sse`** when the IDE runs outside the Fly network.

---

## Testing

```bash
uv run python test_newsletter_flow.py
```

This checks Jinja rendering, deploy input resolution, and that all five MCP tools are registered. It does **not** call Vercel or send mail unless you build separate integration tests with real credentials.

---

## Performance note

The original design target was a very fast end-to-end run; in practice **OpenRouter**, **Vercel**, and **SMTP** latency often push total time above a few seconds. Tune timeouts in `api_tools.py` / `vercel_deploy.py` / `email_sender.py` if needed.

---

## Example user request (for an MCP-aware agent)

> Send AI newsletter to these emails: `reader@example.com`

The agent should compute a recent date range, call the tools in order, then send email HTML that summarizes the issue and links to the deployed `public_url`.
