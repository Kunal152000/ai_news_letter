import html as html_module
import logging
import re
from typing import Any

import httpx

from app.config.settings import EMAIL_FROM, EMAIL_FROM_NAME, RESEND_API_KEY

logger = logging.getLogger(__name__)

_RESEND_API = "https://api.resend.com/emails"

# Fixed narrative for the digest email; `highlights` replace the “quick preview” bullets.
_EMAIL_GREETING = "Hi there,"
_EMAIL_INTRO = (
    "The AI world just moved fast again — and we’ve distilled the most important updates for you."
)
_EMAIL_PREVIEW_LABEL = "Here’s a quick preview 👇"
_EMAIL_AFTER_PREVIEW = (
    "This is just the surface.\n\n"
    "We’ve put together a clean, no-noise breakdown with insights, tools, and real impact — all in one place."
)
_EMAIL_CTA_LINE = "👉 Read the full newsletter here:"
_EMAIL_CLOSING = (
    "If you want to stay ahead in AI without information overload, this is for you.\n\n"
    "See you inside,\n"
    "AI Weekly"
)
_EMAIL_FOOTER = "You’re receiving this because you asked for the AI newsletter."


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
    highlights = [h.strip() for h in (highlights or []) if h and str(h).strip()][:8]
    title = issue_title.strip() if issue_title and issue_title.strip() else None
    safe_href = html_module.escape(issue_url.strip(), quote=True)
    safe_url_visible = html_module.escape(issue_url.strip(), quote=False)

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
            '<tr><td style="padding:16px;font-family:Georgia,serif;font-size:16px;color:#444;line-height:1.5;">'
            "<em>Your live headlines will appear here when highlights are passed from the latest issue—"
            "open the full newsletter for the complete breakdown.</em>"
            "</td></tr>"
        )

    extra_block = ""
    if extra_html and extra_html.strip():
        extra_block = (
            '<tr><td style="padding:16px 24px 0;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;'
            'font-size:14px;color:#334155;line-height:1.55;">'
            f"{extra_html.strip()}"
            "</td></tr>"
        )

    after_preview_html = html_module.escape(_EMAIL_AFTER_PREVIEW).replace("\n", "<br/>")
    closing_html = html_module.escape(_EMAIL_CLOSING).replace("\n", "<br/>")

    optional_title = ""
    if title:
        optional_title = (
            f'<h1 style="margin:0 0 16px;font-size:22px;line-height:1.3;color:#0f172a;font-weight:700;">'
            f"{html_module.escape(title)}</h1>"
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
          <td style="padding:28px 24px 12px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">
            <p style="margin:0 0 16px;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#64748b;">
              AI Weekly
            </p>
            {optional_title}
            <p style="margin:0 0 12px;font-size:17px;line-height:1.5;color:#0f172a;font-weight:600;">
              {html_module.escape(_EMAIL_GREETING)}
            </p>
            <p style="margin:0 0 20px;font-size:16px;line-height:1.6;color:#475569;">
              {html_module.escape(_EMAIL_INTRO)}
            </p>
            <p style="margin:0 0 12px;font-size:16px;line-height:1.5;color:#334155;font-weight:600;">
              {html_module.escape(_EMAIL_PREVIEW_LABEL)}
            </p>
          </td>
        </tr>
        <tr><td style="padding:0 8px 0;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;border-radius:8px;">
            {rows}
          </table>
        </td></tr>
        {extra_block}
        <tr>
          <td style="padding:24px 24px 8px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;
            font-size:16px;line-height:1.6;color:#475569;">
            <p style="margin:0;">{after_preview_html}</p>
          </td>
        </tr>
        <tr>
          <td style="padding:8px 24px 20px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">
            <p style="margin:0 0 12px;font-size:16px;line-height:1.5;color:#334155;font-weight:600;">
              {html_module.escape(_EMAIL_CTA_LINE)}
            </p>
            <p style="margin:0 0 16px;text-align:center;">
              <a href="{safe_href}" style="display:inline-block;padding:14px 28px;background:linear-gradient(135deg,#0d9488,#6366f1);
                color:#ffffff;text-decoration:none;font-size:16px;font-weight:600;border-radius:10px;">
                Read the full newsletter
              </a>
            </p>
            <p style="margin:0;font-size:14px;color:#64748b;word-break:break-all;line-height:1.5;">
              <a href="{safe_href}" style="color:#0d9488;text-decoration:underline;">{safe_url_visible}</a>
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:0 24px 28px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;
            font-size:16px;line-height:1.6;color:#475569;">
            <p style="margin:0;">{closing_html}</p>
          </td>
        </tr>
        <tr>
          <td style="padding:0 24px 24px;font-size:12px;color:#94a3b8;text-align:center;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">
            {html_module.escape(_EMAIL_FOOTER)}
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
    title = (issue_title or "").strip()
    lines: list[str] = ["AI Weekly\n"]
    if title:
        lines.append(f"{title}\n\n")
    lines.append(f"{_EMAIL_GREETING}\n\n")
    lines.append(f"{_EMAIL_INTRO}\n\n")
    lines.append(f"{_EMAIL_PREVIEW_LABEL}\n\n")
    for h in highlights or []:
        if h and str(h).strip():
            lines.append(f"→ {str(h).strip()[:400]}\n")
    if not any(h and str(h).strip() for h in (highlights or [])):
        lines.append(
            "(Live headlines from this issue appear here when highlights are included—see the full newsletter for details.)\n"
        )
    lines.append("\n")
    if extra_text and extra_text.strip():
        lines.append(extra_text.strip() + "\n\n")
    lines.append(_EMAIL_AFTER_PREVIEW + "\n\n")
    lines.append(f"{_EMAIL_CTA_LINE}\n{issue_url.strip()}\n\n")
    lines.append(_EMAIL_CLOSING + "\n\n")
    lines.append(_EMAIL_FOOTER + "\n")
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
    Send email via Resend. If `issue_url` is set, builds the digest template; optional `html_content` is appended.
    If `issue_url` is omitted, `html_content` is required as the body.
    """
    cleaned = [r.strip() for r in recipients if r and r.strip()]
    if not cleaned:
        logger.warning("send_email: no recipients")
        return {"success": False, "error": "No recipients", "provider": "none"}

    if not RESEND_API_KEY:
        logger.error("send_email: RESEND_API_KEY not configured")
        return {"success": False, "error": "RESEND_API_KEY is required", "provider": "none"}

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

    from_header = f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>" if EMAIL_FROM_NAME else EMAIL_FROM
    payload: dict[str, Any] = {
        "from": from_header,
        "to": cleaned if len(cleaned) > 1 else cleaned[0],
        "subject": subject,
        "html": final_html,
    }
    if plain:
        payload["text"] = plain

    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.post(
                _RESEND_API,
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        data = r.json() if r.content else {}
        if r.status_code not in (200, 201):
            err = data.get("message") if isinstance(data.get("message"), str) else None
            msg = err or (r.text[:800] if r.text else r.reason_phrase)
            logger.error("send_email: Resend HTTP %s %s", r.status_code, msg)
            return {"success": False, "error": f"Resend HTTP {r.status_code}: {msg}", "provider": "resend"}

        rid = data.get("id") if isinstance(data.get("id"), str) else None
        logger.info("send_email: Resend ok (%s recipients, id=%s)", len(cleaned), rid)
        return {"success": True, "error": None, "provider": "resend", "id": rid}
    except Exception as e:
        logger.exception("send_email: Resend request failed")
        return {"success": False, "error": str(e), "provider": "resend"}
