import html as html_module
import logging
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from app.config.settings import EMAIL_FROM, EMAIL_FROM_NAME, SMTP_GMAIL_ADDRESS, SMTP_GMAIL_PASSWORD

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
    Send HTML email (Gmail SMTP). If `issue_url` is set, builds the welcoming digest template;
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
        return _send_gmail_smtp(cleaned, subject, final_html, plain_text=plain)

    logger.error("send_email: no provider configured — set SMTP_GMAIL_ADDRESS and SMTP_GMAIL_PASSWORD")
    return {"success": False, "error": "No email provider configured", "provider": "none"}


def _send_gmail_smtp(
    recipients: list[str],
    subject: str,
    html_content: str,
    *,
    plain_text: str | None = None,
) -> dict[str, Any]:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{EMAIL_FROM_NAME} <{SMTP_GMAIL_ADDRESS}>"
        msg["To"] = ", ".join(recipients)

        if plain_text:
            msg.attach(MIMEText(plain_text, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_GMAIL_ADDRESS, SMTP_GMAIL_PASSWORD)
            server.sendmail(SMTP_GMAIL_ADDRESS, recipients, msg.as_string())

        logger.info("send_email: Gmail SMTP accepted (%s recipients)", len(recipients))
        return {"success": True, "error": None, "provider": "gmail"}

    except smtplib.SMTPAuthenticationError:
        logger.error("send_email Gmail: Authentication failed - check credentials")
        return {"success": False, "error": "Gmail authentication failed", "provider": "gmail"}

    except smtplib.SMTPException as e:
        logger.error("send_email Gmail SMTP error: %s", str(e))
        return {"success": False, "error": f"Gmail SMTP error: {str(e)}", "provider": "gmail"}

    except Exception as e:
        logger.exception("send_email Gmail failed")
        return {"success": False, "error": str(e), "provider": "gmail"}
