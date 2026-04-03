import concurrent.futures
from fastapi import APIRouter, HTTPException
from app.services.fetch_news_GNEWS import fetch_ai_news_gnews
from app.services.fetch_news_NewsData import fetch_ai_news_news_data
from app.services.api_tools import get_github_repos
from app.utils.filters import filter_ai_articles, save_to_json

router = APIRouter()

@router.get("/fetch-news")
def fetch_news_endpoint():
    """
    Fetch news from APIs in parallel, filter by relevant keywords,
    save to JSON file, and return the summary.
    """
    # 1. Fetch news and github repos in parallelly 
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_gnews = executor.submit(fetch_ai_news_gnews)
        future_newsdata = executor.submit(fetch_ai_news_news_data)
        future_github = executor.submit(get_github_repos, "topic:ai OR topic:machine-learning OR topic:llm OR topic:generative-ai sort:updated stars:>50")
        
        gnews_articles = future_gnews.result() or []
        newsdata_articles = future_newsdata.result() or []
        github_articles = future_github.result() or []

        # print("gnews_articles", gnews_articles)
        # print("newsdata_articles", newsdata_articles)
        
    raw_articles = gnews_articles + newsdata_articles  

    if not raw_articles and not github_articles:
        raise HTTPException(status_code=500, detail="Failed to fetch news or tools from any sources")
    
    # 2. Filter news
    filtered_articles = filter_ai_articles(raw_articles) if raw_articles else []
    print("Filtered articles", filtered_articles)
    
    # 3. Append GitHub tools after the news
    final_articles = filtered_articles + github_articles
    
    # 4. Save to JSON
    success = save_to_json(final_articles, "data/news.json")
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save data to JSON")
        
    # 5. Return response
    return {
        "status": "success",
        "articles_saved": len(final_articles)
    }
