"""
SMTP (Gmail-compatible) or SendGrid mail delivery.
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx

from app.config.settings import (
    EMAIL_FROM,
    EMAIL_FROM_NAME,
    EMAIL_PASS,
    EMAIL_SMTP_HOST,
    EMAIL_SMTP_PORT,
    EMAIL_USER,
    SENDGRID_API_KEY,
)

logger = logging.getLogger(__name__)


def send_email(recipients: list[str], subject: str, html_content: str) -> dict[str, Any]:
    """
    Send HTML email. Prefers SendGrid when SENDGRID_API_KEY is set; otherwise SMTP.
    Returns: {"success": bool, "error": str | None, "provider": str}
    """
    cleaned = [r.strip() for r in recipients if r and r.strip()]
    if not cleaned:
        logger.warning("send_email: no recipients")
        return {"success": False, "error": "No recipients", "provider": "none"}

    if SENDGRID_API_KEY:
        return _send_sendgrid(cleaned, subject, html_content)
    return _send_smtp(cleaned, subject, html_content)


def _send_sendgrid(recipients: list[str], subject: str, html_content: str) -> dict[str, Any]:
    from_addr = EMAIL_FROM
    if not from_addr:
        logger.error("send_email SendGrid: EMAIL_FROM / EMAIL_USER not configured")
        return {"success": False, "error": "EMAIL_FROM or EMAIL_USER required for SendGrid", "provider": "sendgrid"}

    payload = {
        "personalizations": [{"to": [{"email": e} for e in recipients]}],
        "from": {"email": from_addr, "name": EMAIL_FROM_NAME},
        "subject": subject,
        "content": [{"type": "text/html", "value": html_content}],
    }
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {SENDGRID_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if r.status_code in (200, 202):
            logger.info("send_email: SendGrid accepted (%s recipients)", len(recipients))
            return {"success": True, "error": None, "provider": "sendgrid"}
        err = r.text[:500] if r.text else r.reason_phrase
        logger.error("send_email SendGrid HTTP %s: %s", r.status_code, err)
        return {"success": False, "error": f"SendGrid HTTP {r.status_code}: {err}", "provider": "sendgrid"}
    except Exception as e:
        logger.exception("send_email SendGrid failed")
        return {"success": False, "error": str(e), "provider": "sendgrid"}


def _send_smtp(recipients: list[str], subject: str, html_content: str) -> dict[str, Any]:
    if not EMAIL_USER or not EMAIL_PASS:
        logger.error("send_email SMTP: EMAIL_USER / EMAIL_PASS not configured")
        return {"success": False, "error": "EMAIL_USER and EMAIL_PASS required for SMTP", "provider": "smtp"}

    from_addr = EMAIL_FROM or EMAIL_USER
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{EMAIL_FROM_NAME} <{from_addr}>"
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.sendmail(from_addr, recipients, msg.as_string())
        logger.info("send_email: SMTP sent (%s recipients)", len(recipients))
        return {"success": True, "error": None, "provider": "smtp"}
    except Exception as e:
        logger.exception("send_email SMTP failed")
        return {"success": False, "error": str(e), "provider": "smtp"}
