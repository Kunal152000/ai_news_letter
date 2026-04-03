import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

from app.config.settings import GNEWS_API_KEY

def fetch_ai_news_gnews() -> Optional[List[Dict]]:
    """
    Fetch AI-related news from the Mediastack API.
    Handles timeout, error handling, and status code checks.
    """
    if not GNEWS_API_KEY:
        print("Error: GNEWS_API_KEY is missing.")
        return None

    url = "https://gnews.io/api/v4/search"
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday() + 7)  # last Monday
    end_of_week = start_of_week + timedelta(days=6)
    params = {
        "apikey": GNEWS_API_KEY,
        "q":"\"AI\" OR \"artificial intelligence\" OR \"machine learning\" OR \"LLM\" OR \"generative AI\" OR \"ChatGPT\" OR \"OpenAI\" OR \"Gemini AI\" OR \"Claude AI\" OR \"AI startup\" OR \"AI research\"",
        "lang":"en",
        "max":100,
        "sortby":"relevance",
        "from":start_of_week,
        "to":end_of_week
    }
    
    try:
        response = requests.get(url, params=params,  headers={"Accept": "application/json"}, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        # print("data", data)
        articles = data.get("articles", [])
        
        structured_articles = []
        for article in articles:
            structured_articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "url": article.get("url", ""),
            })
        # print("Structured articles", structured_articles)
        if structured_articles:
            return structured_articles
        else:
            print("Error: No articles fetched from GNews api")
            return None
        
    except requests.exceptions.Timeout:
        print("Error: The request to GNEWS API timed out.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news from GNEWS API: {e}")
        return None
