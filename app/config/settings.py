import os
from dotenv import load_dotenv

load_dotenv()

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
NEWS_DATA_API_KEY = os.getenv("NEWS_DATA_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# Email: SMTP (Gmail, etc.) or SendGrid (if SENDGRID_API_KEY is set, SendGrid wins)
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "AI Weekly")
SMTP_GMAIL_ADDRESS = os.getenv("SMTP_GMAIL_ADDRESS")
SMTP_GMAIL_PASSWORD = os.getenv("SMTP_GMAIL_PASSWORD")
## Vercel static deploy (single index.html)  
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")
VERCEL_PROJECT_ID = os.getenv("VERCEL_PROJECT_ID")
VERCEL_PROJECT_NAME = os.getenv("VERCEL_PROJECT_NAME")
# VERCEL_TEAM_ID = os.getenv("VERCEL_TEAM_ID")

if not GNEWS_API_KEY:
    print("Warning: GNEWS_API_KEY is not set in the environment variables.")
if not NEWS_DATA_API_KEY:
    print("Warning: NEWS_DATA_API_KEY is not set in the environment variables.")
if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY is not set in the environment variables.")
if not EMAIL_FROM:
    print("Warning: EMAIL_FROM is not set in the environment variables.")
if not EMAIL_FROM_NAME:
    print("Warning: EMAIL_FROM_NAME is not set in the environment variables.")
if not VERCEL_TOKEN:
    print("Warning: VERCEL_TOKEN is not set in the environment variables.")
if not VERCEL_PROJECT_ID:
    print("Warning: VERCEL_PROJECT_ID is not set in the environment variables.")
if not VERCEL_PROJECT_NAME:
    print("Warning: VERCEL_PROJECT_NAME is not set in the environment variables.")
if not SMTP_GMAIL_ADDRESS:
    print("Warning: SMTP_GMAIL_ADDRESS is not set in the environment variables.")
if not SMTP_GMAIL_PASSWORD:
    print("Warning: SMTP_GMAIL_PASSWORD is not set in the environment variables.")