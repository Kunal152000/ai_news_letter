import httpx
import logging
from typing import Any

from app.config.settings import (
    EMAIL_FROM,
    EMAIL_FROM_NAME,
    RESEND_API_KEY
)
logger = logging.getLogger(__name__)

def send_email(recipients: list[str], subject: str, html_content: str) -> dict[str, Any]:
    """
    Send HTML email.
    Returns: {"success": bool, "error": str | None, "provider": str}
    """
    cleaned = [r.strip() for r in recipients if r and r.strip()]
    if not cleaned:
        logger.warning("send_email: no recipients")
        return {"success": False, "error": "No recipients", "provider": "none"}

    if not EMAIL_FROM:
        logger.error("send_email: EMAIL_FROM not configured")
        return {"success": False, "error": "EMAIL_FROM is required", "provider": "none"}

    if RESEND_API_KEY:
        return _send_resend(cleaned, subject, html_content)

    logger.error("send_email: no provider configured — set RESEND_API_KEY")
    return {"success": False, "error": "No email provider configured", "provider": "none"}


def _send_resend(recipients: list[str], subject: str, html_content: str) -> dict[str, Any]:
    payload = {
        "from": f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>",
        "to": recipients,
        "subject": subject,
        "html": html_content,
    }
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if r.status_code in (200, 201):
            logger.info("send_email: Resend accepted (%s recipients)", len(recipients))
            return {"success": True, "error": None, "provider": "resend"}
        err = r.text[:500] if r.text else r.reason_phrase
        logger.error("send_email Resend HTTP %s: %s", r.status_code, err)
        return {"success": False, "error": f"Resend HTTP {r.status_code}: {err}", "provider": "resend"}
    except Exception as e:
        logger.exception("send_email Resend failed")
        return {"success": False, "error": str(e), "provider": "resend"}