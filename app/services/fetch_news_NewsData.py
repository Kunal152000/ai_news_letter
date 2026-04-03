import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

from app.config.settings import NEWS_DATA_API_KEY

def fetch_ai_news_news_data() -> Optional[List[Dict]]:
    """
    Fetch AI-related news from the Mediastack API.
    Handles timeout, error handling, and status code checks.
    """
    if not NEWS_DATA_API_KEY:
        print("Error: NEWS_DATA_API_KEY is missing.")
        return None
    # This api only provides data from past 48 hours
    url = "https://newsdata.io/api/1/latest"
    params = {
        "apikey": NEWS_DATA_API_KEY,
        "q":"AI OR artificial intelligence OR machine learning OR LLM OR generative AI OR ChatGPT OR OpenAI",
        "language":"en",
        "category":"technology",    
        "sort":"relevancy"
    }
    
    try:
        response = requests.get(url, params=params,  headers={"Accept": "application/json"}, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print("data", data)
        articles = data.get("results", [])
        
        structured_articles = []
        for article in articles:
            structured_articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "url": article.get("link", ""),
            })
        # print("Structured articles", structured_articles)
        if structured_articles:
            return structured_articles
        else:
            print("Error: No articles fetched from NEWS_DATA api")
            return None
        
    except requests.exceptions.Timeout:
        print("Error: The request to NEWS_DATA API timed out.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news from NEWS_DATA API: {e}")
        return None
