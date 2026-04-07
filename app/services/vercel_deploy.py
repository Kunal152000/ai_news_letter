"""
Deploy a single static HTML file to an existing Vercel project via REST API.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config.settings import (
    VERCEL_PROJECT_ID,
    VERCEL_PROJECT_NAME,
    VERCEL_TEAM_ID,
    VERCEL_TOKEN,
)

logger = logging.getLogger(__name__)

_VERCEL_API = "https://api.vercel.com"


def _project_display_name() -> str | None:
    if VERCEL_PROJECT_NAME:
        return VERCEL_PROJECT_NAME
    if not VERCEL_TOKEN or not VERCEL_PROJECT_ID:
        return None
    params: dict[str, str] = {}
    if VERCEL_TEAM_ID:
        params["teamId"] = VERCEL_TEAM_ID
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(
                f"{_VERCEL_API}/v9/projects/{VERCEL_PROJECT_ID}",
                headers={"Authorization": f"Bearer {VERCEL_TOKEN}"},
                params=params or None,
            )
        if r.status_code == 200:
            name = r.json().get("name")
            if isinstance(name, str) and name:
                return name
        logger.warning("vercel project lookup failed: HTTP %s %s", r.status_code, r.text[:200])
    except Exception as e:
        logger.warning("vercel project lookup error: %s", e)
    return None


def deploy_newsletter_page(html_content: str) -> dict[str, Any]:
    """
    Create a new production deployment with a single index.html.
    Returns: {"success": bool, "public_url": str | None, "error": str | None, "deployment_id": str | None}
    """
    if not VERCEL_TOKEN or not VERCEL_PROJECT_ID:
        logger.error("deploy_newsletter_page: VERCEL_TOKEN / VERCEL_PROJECT_ID missing")
        return {
            "success": False,
            "public_url": None,
            "error": "VERCEL_TOKEN and VERCEL_PROJECT_ID are required",
            "deployment_id": None,
        }

    name = _project_display_name()
    if not name:
        return {
            "success": False,
            "public_url": None,
            "error": "Could not resolve Vercel project name; set VERCEL_PROJECT_NAME or fix token/project id",
            "deployment_id": None,
        }

    body: dict[str, Any] = {
        "name": name,
        "project": VERCEL_PROJECT_ID,
        "target": "production",
        "files": [
            {
                "file": "index.html",
                "data": html_content,
                "encoding": "utf-8",
            }
        ],
        "projectSettings": {"framework": None},
    }

    params: dict[str, str] = {"skipAutoDetectionConfirmation": "1"}
    if VERCEL_TEAM_ID:
        params["teamId"] = VERCEL_TEAM_ID

    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.post(
                f"{_VERCEL_API}/v13/deployments",
                headers={"Authorization": f"Bearer {VERCEL_TOKEN}"},
                params=params,
                json=body,
            )
        data = r.json() if r.content else {}
        if r.status_code not in (200, 201):
            err = data.get("error", {}).get("message") if isinstance(data.get("error"), dict) else None
            msg = err or (r.text[:800] if r.text else r.reason_phrase)
            logger.error("deploy_newsletter_page: HTTP %s %s", r.status_code, msg)
            return {"success": False, "public_url": None, "error": f"Vercel HTTP {r.status_code}: {msg}", "deployment_id": None}

        url = data.get("url")
        if isinstance(url, str) and url:
            public = f"https://{url}"
        else:
            public = None
        dep_id = data.get("id") if isinstance(data.get("id"), str) else None
        logger.info("deploy_newsletter_page: deployment %s -> %s", dep_id, public)
        return {"success": True, "public_url": public, "error": None, "deployment_id": dep_id}
    except Exception as e:
        logger.exception("deploy_newsletter_page failed")
        return {"success": False, "public_url": None, "error": str(e), "deployment_id": None}
