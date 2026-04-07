import html as html_module
import logging
import re
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from app.config.settings import (
    EMAIL_FROM,
    EMAIL_FROM_NAME,
    SMTP_GMAIL_ADDRESS,
    SMTP_GMAIL_PASSWORD,
    SMTP_HOST,
    SMTP_MODE,
    SMTP_PORT,
    SMTP_TIMEOUT,
)

logger = logging.getLogger(__name__)


def _strip_html_to_plain(fragment: str) -> str:
    t = re.sub(r"<[^>]+>", " ", fragment)
    return " ".join(t.split())


def build_newsletter_invite_html(
    issue_url: str,
    highlights: list[str] | None = None,
    *,
    issue_title: str | None = None,
    extra_html: str | None = None,
) -> str:
    """
    Welcoming, mobile-friendly email body: intro, teaser bullets, CTA to full issue.
    `highlights` should be short lines (headlines or one-line summaries); full detail lives on the web page.
    """
    highlights = [h.strip() for h in (highlights or []) if h and str(h).strip()][:8]
    title = issue_title.strip() if issue_title and issue_title.strip() else "Your AI Weekly is ready"
    safe_href = html_module.escape(issue_url.strip(), quote=True)

    rows = ""
    if highlights:
        for line in highlights:
            esc = html_module.escape(line[:400])
            rows += (
                '<tr><td style="padding:12px 16px;font-family:Georgia,serif;font-size:16px;'
                'line-height:1.45;color:#1a1a1a;border-bottom:1px solid #ececec;">'
                f'<span style="color:#0d9488;font-weight:bold;margin-right:8px;">→</span>{esc}'
                "</td></tr>"
            )
    else:
        rows = (
            '<tr><td style="padding:16px;font-family:Georgia,serif;font-size:16px;color:#444;">'
            "We’ve pulled together the top AI headlines and tools—open the full issue for "
            "stories, links, and more context."
            "</td></tr>"
        )

    extra_block = ""
    if extra_html and extra_html.strip():
        extra_block = (
            '<tr><td style="padding:20px 16px 8px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;'
            'font-size:14px;color:#333;">'
            f"{extra_html.strip()}"
            "</td></tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/></head>
<body style="margin:0;padding:0;background:#f4f4f5;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:24px 12px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:560px;background:#ffffff;border-radius:12px;overflow:hidden;
        box-shadow:0 4px 24px rgba(0,0,0,.06);">
        <tr>
          <td style="padding:28px 24px 8px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">
            <p style="margin:0 0 8px;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#64748b;">
              AI Weekly
            </p>
            <h1 style="margin:0;font-size:24px;line-height:1.25;color:#0f172a;font-weight:700;">
              {html_module.escape(title)}
            </h1>
            <p style="margin:14px 0 0;font-size:16px;line-height:1.5;color:#475569;">
              Hi there—thanks for reading. Here’s a quick taste of what’s inside; tap below for the full layout, links, and extras.
            </p>
          </td>
        </tr>
        <tr><td style="padding:8px 8px 0;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;border-radius:8px;">
            {rows}
          </table>
        </td></tr>
        {extra_block}
        <tr>
          <td style="padding:28px 24px 32px;text-align:center;">
            <a href="{safe_href}" style="display:inline-block;padding:14px 28px;background:linear-gradient(135deg,#0d9488,#6366f1);
              color:#ffffff;text-decoration:none;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;
              font-size:16px;font-weight:600;border-radius:10px;">
              Read the full issue
            </a>
            <p style="margin:18px 0 0;font-size:13px;color:#94a3b8;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">
              Or paste this link in your browser:<br/>
              <span style="color:#64748b;word-break:break-all;">{safe_href}</span>
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:0 24px 24px;font-size:12px;color:#94a3b8;text-align:center;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">
            You’re receiving this because you asked for the AI newsletter. See you next time.
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def build_newsletter_invite_plain(
    issue_url: str,
    highlights: list[str] | None = None,
    *,
    issue_title: str | None = None,
    extra_text: str | None = None,
) -> str:
    title = (issue_title or "Your AI Weekly is ready").strip()
    lines = [f"{title}\n", "Hi there—here’s a quick taste of this issue. Open the link for the full newsletter.\n"]
    for h in (highlights or []):
        if h and str(h).strip():
            lines.append(f"• {str(h).strip()[:400]}\n")
    if not any(h and str(h).strip() for h in (highlights or [])):
        lines.append("(Full stories and links are on the web page.)\n")
    if extra_text and extra_text.strip():
        lines.append("\n" + extra_text.strip() + "\n")
    lines.append(f"\nRead the full issue: {issue_url.strip()}\n")
    return "".join(lines)


def send_email(
    recipients: list[str],
    subject: str,
    html_content: str | None = None,
    *,
    issue_url: str | None = None,
    highlights: list[str] | None = None,
    issue_title: str | None = None,
) -> dict[str, Any]:
    """
    Send HTML email via SMTP (e.g. Gmail + App Password). If `issue_url` is set, builds the welcoming digest template;
    optional `html_content` is appended inside the template. If `issue_url` is omitted, `html_content` is required.
    """
    cleaned = [r.strip() for r in recipients if r and r.strip()]
    if not cleaned:
        logger.warning("send_email: no recipients")
        return {"success": False, "error": "No recipients", "provider": "none"}

    if not EMAIL_FROM:
        logger.error("send_email: EMAIL_FROM not configured")
        return {"success": False, "error": "EMAIL_FROM is required", "provider": "none"}

    url = (issue_url or "").strip()
    body_html = (html_content or "").strip()

    if url:
        final_html = build_newsletter_invite_html(
            url,
            highlights,
            issue_title=issue_title,
            extra_html=body_html if body_html else None,
        )
        extra_plain = _strip_html_to_plain(body_html) if body_html else None
        plain = build_newsletter_invite_plain(
            url,
            highlights,
            issue_title=issue_title,
            extra_text=extra_plain if extra_plain else None,
        )
    elif body_html:
        final_html = body_html
        plain = None
    else:
        return {
            "success": False,
            "error": "Provide issue_url (recommended digest + CTA) or html_content (raw body).",
            "provider": "none",
        }

    if SMTP_GMAIL_ADDRESS and SMTP_GMAIL_PASSWORD:
        return _send_smtp(cleaned, subject, final_html, plain_text=plain)

    logger.error("send_email: set SMTP_GMAIL_ADDRESS and SMTP_GMAIL_PASSWORD")
    return {"success": False, "error": "No SMTP credentials configured", "provider": "none"}


def _smtp_attempt_starttls(host: str, port: int, msg: MIMEMultipart, user: str, password: str, timeout: int) -> None:
    ctx = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=timeout) as server:
        server.ehlo()
        server.starttls(context=ctx)
        server.ehlo()
        server.login(user, password)
        server.send_message(msg)


def _smtp_attempt_ssl(host: str, port: int, msg: MIMEMultipart, user: str, password: str, timeout: int) -> None:
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, timeout=timeout, context=ctx) as server:
        server.login(user, password)
        server.send_message(msg)


def _send_smtp(
    recipients: list[str],
    subject: str,
    html_content: str,
    *,
    plain_text: str | None = None,
) -> dict[str, Any]:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{EMAIL_FROM_NAME} <{SMTP_GMAIL_ADDRESS}>"
    msg["To"] = ", ".join(recipients)

    if plain_text:
        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    host = SMTP_HOST
    timeout = max(10, SMTP_TIMEOUT)
    mode = SMTP_MODE if SMTP_MODE in ("auto", "starttls", "ssl") else "auto"
    errors: list[str] = []

    def run(kind: str, port: int) -> bool:
        try:
            if kind == "starttls":
                _smtp_attempt_starttls(host, port, msg, SMTP_GMAIL_ADDRESS, SMTP_GMAIL_PASSWORD, timeout)
            else:
                _smtp_attempt_ssl(host, port, msg, SMTP_GMAIL_ADDRESS, SMTP_GMAIL_PASSWORD, timeout)
            return True
        except smtplib.SMTPAuthenticationError:
            raise
        except Exception as e:
            errors.append(f"{kind} port {port}: {e}")
            logger.warning("SMTP %s:%s failed: %s", host, port, e)
            return False

    try:
        if mode == "starttls":
            port = SMTP_PORT or 587
            if not run("starttls", port):
                return _smtp_failure(errors)
        elif mode == "ssl":
            port = SMTP_PORT or 465
            if not run("ssl", port):
                return _smtp_failure(errors)
        else:
            if SMTP_PORT is not None:
                if SMTP_PORT == 587:
                    attempts = [("starttls", 587), ("ssl", 465)]
                elif SMTP_PORT == 465:
                    attempts = [("ssl", 465), ("starttls", 587)]
                else:
                    attempts = [("starttls", SMTP_PORT), ("ssl", SMTP_PORT)]
            else:
                attempts = [("starttls", 587), ("ssl", 465)]
            for kind, port in attempts:
                if run(kind, port):
                    break
            else:
                return _smtp_failure(errors)
    except smtplib.SMTPAuthenticationError as e:
        logger.error("SMTP authentication failed: %s", e)
        return {
            "success": False,
            "error": (
                "SMTP authentication failed. For Gmail: enable 2FA and use a 16-character App Password, "
                "not your normal password."
            ),
            "provider": "smtp",
        }

    logger.info("send_email: SMTP ok (%s recipients, host=%s)", len(recipients), host)
    return {"success": True, "error": None, "provider": "smtp"}


def _smtp_failure(errors: list[str]) -> dict[str, Any]:
    detail = "; ".join(errors) if errors else "unknown"
    logger.error("send_email: all SMTP attempts failed: %s", detail)
    hint = (
        " Try SMTP_MODE=starttls or SMTP_MODE=ssl if only one port is blocked. "
        "If you see 'Network is unreachable' (errno 101) on both 587 and 465, the host is not routing "
        "to SMTP at all."
    )
    if "101" in detail or "Network is unreachable" in detail or "unreachable" in detail.lower():
        hint += (
            " Render’s free web services block outbound SMTP (ports 25, 465, 587)—use a paid Render "
            "instance for Gmail SMTP, or send mail from your laptop/local server, or use an email "
            "provider’s HTTPS API instead of SMTP."
        )
    return {"success": False, "error": f"SMTP failed ({detail}).{hint}", "provider": "smtp"}
