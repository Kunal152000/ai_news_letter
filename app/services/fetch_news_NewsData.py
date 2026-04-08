from typing import Dict, List

import httpx

from app.config.settings import NEWS_DATA_API_KEY

_NEWSDATA_BASE = "https://newsdata.io/api/1"


def _normalize_newsdata_results(articles: list) -> List[Dict]:
    structured: List[Dict] = []
    for article in articles:
        desc = article.get("description") or ""
        if not desc and article.get("content"):
            desc = (article.get("content") or "")[:500]
        structured.append(
            {
                "title": article.get("title", ""),
                "description": desc,
                "url": article.get("link", ""),
            }
        )
    return structured


def fetch_newsdata_search(query: str, from_date: str, to_date: str) -> List[Dict]:
    """
    Fetch news from NewsData.io for a query and date range.
    Tries the archive endpoint first (respects from_date/to_date); falls back to /latest (past 48h).
    """
    if not NEWS_DATA_API_KEY:
        print("Error: NEWS_DATA_API_KEY is missing.")
        return []

    q = (query or "").strip() or "artificial intelligence OR machine learning"
    if len(q) > 512:
        q = q[:512]

    headers = {"Accept": "application/json"}
    common = {
        "apikey": NEWS_DATA_API_KEY,
        "q": q,
        "language": "en",
        "sort": "relevancy",
        "size": 10,
    }

    try:
        r = httpx.get(
            f"{_NEWSDATA_BASE}/archive",
            params={**common, "from_date": from_date, "to_date": to_date},
            headers=headers,
            timeout=10.0,
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "success":
                return _normalize_newsdata_results(data.get("results", []))
    except httpx.HTTPError as e:
        print(f"NewsData archive request failed: {e}")

    try:
        r = httpx.get(
            f"{_NEWSDATA_BASE}/latest",
            params={**common, "category": "technology"},
            headers=headers,
            timeout=10.0,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "success":
            print(f"NewsData latest API status: {data.get('status', data)}")
            return []
        return _normalize_newsdata_results(data.get("results", []))
    except httpx.TimeoutException:
        print("Error: The request to NEWS_DATA API timed out.")
        return []
    except httpx.HTTPError as e:
        print(f"Error fetching news from NEWS_DATA API: {e}")
        return []
