import json
import re
from typing import Dict, List

import httpx

from app.config.settings import (
    GNEWS_API_KEY,
    OPENROUTER_API_KEY,
    OPENROUTER_APP_TITLE,
    OPENROUTER_HTTP_REFERER,
)
from app.services.fetch_news_NewsData import fetch_newsdata_search


def _normalize_url_key(url: str) -> str:
    return (url or "").strip().lower().rstrip("/")


def _dedupe_articles_by_url(items: List[Dict]) -> List[Dict]:
    seen: set[str] = set()
    out: List[Dict] = []
    for it in items:
        key = _normalize_url_key(it.get("url", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def _fetch_gnews(query: str, from_date: str, to_date: str) -> List[Dict]:
    if not GNEWS_API_KEY:
        print("Error: GNEWS_API_KEY is missing.")
        return []

    url = "https://gnews.io/api/v4/search"
    params = {
        "apikey": GNEWS_API_KEY,
        "q": query,
        "lang": "en",
        "max": 10,
        "sortby": "relevance",
        "from": from_date,
        "to": to_date,
    }
    try:
        response = httpx.get(url, params=params, headers={"Accept": "application/json"}, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])
        return [
            {
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
            }
            for a in articles
        ]
    except Exception as e:
        print(f"Error fetching GNews: {e}")
        return []


def get_news(query: str, from_date: str, to_date: str) -> List[Dict]:
    """
    Fetch news from GNews and NewsData.io, merge into one list (deduped by URL).
    Either source may be empty if its API key is missing or the request fails.
    """
    gnews_articles = _fetch_gnews(query, from_date, to_date)
    newsdata_articles = fetch_newsdata_search(query, from_date, to_date)
    return _dedupe_articles_by_url(gnews_articles + newsdata_articles)

def get_github_repos(query: str) -> List[Dict]:
    """
    Fetch GitHub repositories based on a query.
    """
    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": "updated",
        "per_page": 10
    }
    
    try:
        response = httpx.get(
            url, params=params, headers={"Accept": "application/vnd.github.v3+json"}, timeout=10.0
        )
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        
        return [
            {
                "title": repo.get("full_name", ""),
                "description": repo.get("description", ""),
                "url": repo.get("html_url", "")
            }
            for repo in items
        ]
    except Exception as e:
        print(f"Error fetching github repos: {e}")
        return []

def filter_ai_news(articles: List[Dict]) -> List[Dict]:
    """
    Filter articles to ensure they are relevant to AI using an LLM.
    """
    if not articles:
        return []
        
    if not OPENROUTER_API_KEY:
        print("Warning: OPENROUTER_API_KEY missing. Returning unfiltered.")
        return articles

    articles_text = ""
    for idx, article in enumerate(articles):
        title = article.get("title", "")
        desc = article.get("description", "")
        # truncate description
        desc = desc[:300] + "..." if len(desc) > 300 else desc
        articles_text += f"[{idx}] Title: {title}\n    Description: {desc}\n\n"

    prompt = f"""You are an AI news filter. Select ONLY articles truly related to AI and developer tech.
Output ONLY a JSON array of article indices, ordered by importance. No explanation.
Articles:
{articles_text}"""

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    if OPENROUTER_HTTP_REFERER:
        headers["HTTP-Referer"] = OPENROUTER_HTTP_REFERER
    if OPENROUTER_APP_TITLE:
        headers["X-Title"] = OPENROUTER_APP_TITLE
    data = {"model": "openrouter/free", "messages": [{"role": "user", "content": prompt}]}
    
    try:
        response = httpx.post(url, headers=headers, json=data, timeout=15.0)
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            generated_text = result["choices"][0]["message"]["content"].strip()
            
            # Clean up JSON formatting if present
            if generated_text.startswith("```json"):
                generated_text = generated_text[7:]
            elif generated_text.startswith("```"):
                generated_text = generated_text[3:]
            if generated_text.endswith("```"):
                generated_text = generated_text[:-3]
                
            generated_text = generated_text.strip()
            
            try:
                indices = json.loads(generated_text)
                if not isinstance(indices, list):
                    indices = [indices]
            except json.JSONDecodeError:
                numbers = re.findall(r'\d+', generated_text)
                indices = [int(n) for n in numbers]
                
            valid_articles = []
            for idx in indices:
                try:
                    i = int(idx)
                    if 0 <= i < len(articles):
                        valid_articles.append(articles[i])
                except (ValueError, TypeError):
                    pass
            
            return valid_articles if valid_articles else articles
            
        return articles
            
    except Exception as e:
        print(f"Error filtering news: {e}")
        return articles
