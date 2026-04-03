import os
from dotenv import load_dotenv

load_dotenv()

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
NEWS_DATA_API_KEY = os.getenv("NEWS_DATA_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Email: SMTP (Gmail, etc.) or SendGrid (if SENDGRID_API_KEY is set, SendGrid wins)
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_FROM = os.getenv("EMAIL_FROM") or EMAIL_USER
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "AI Weekly")
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

# Vercel static deploy (single index.html)
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")
VERCEL_PROJECT_ID = os.getenv("VERCEL_PROJECT_ID")
VERCEL_PROJECT_NAME = os.getenv("VERCEL_PROJECT_NAME")
VERCEL_TEAM_ID = os.getenv("VERCEL_TEAM_ID")

# Optional CTA in rendered newsletter HTML
NEWSLETTER_SITE_URL = os.getenv("NEWSLETTER_SITE_URL")

if not GNEWS_API_KEY:
    print("Warning: GNEWS_API_KEY is not set in the environment variables.")
if not NEWS_DATA_API_KEY:
    print("Warning: NEWS_DATA_API_KEY is not set in the environment variables.")
if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY is not set in the environment variables.")
