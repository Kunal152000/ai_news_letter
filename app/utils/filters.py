import json
import os
import re
from typing import List, Dict
import requests
from app.config.settings import OPENROUTER_API_KEY

def filter_ai_articles(articles: List[Dict]) -> List[Dict]:
    """
    Filter articles to ensure they are relevant to AI using Mistral-7B-Instruct.
    """
    if not articles:
        return []
        
    if not OPENROUTER_API_KEY:
        print("Warning: OPENROUTER_API_KEY is missing. Returning all articles.")
        return articles

    # 1. Prepare the prompt
    articles_text = ""
    for idx, article in enumerate(articles):
        title = article.get("title", "")
        desc = article.get("description", "")
        articles_text += f"[{idx}] Title: {title}\n    Description: {desc}\n\n"

    prompt = """You are an AI news filter.
Task:
- Read each article's description carefully.
- Select ONLY articles truly related to AI (LLMs, GenAI, ML, AI products, major updates) and developers tech.
- Ignore unrelated or weak mentions.
Priority:
- Keep only high-impact news (model releases, APIs, funding, breakthroughs).

Output:
- Return ONLY a JSON array of article indices.
- Order by importance (most important first).
- No explanation. No extra text.
Articles:
""" + articles_text 

    # 2. Call OpenRouter API
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "openrouter/free",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        print("Calling OpenRouter API for filtering...")
        response = requests.post(
            url, 
            headers=headers, 
            json=data
        )   
        response.raise_for_status()
        
        # 3. Parse the result string to get JSON
        result = response.json()
        print("result", result)
        
        if "choices" in result and len(result["choices"]) > 0:
            generated_text = result["choices"][0]["message"]["content"].strip()
            print(f"Raw LLM response: {generated_text}")
            
            # Clean up the generated text
            if generated_text.startswith("```json"):
                generated_text = generated_text[7:]
            elif generated_text.startswith("```"):
                generated_text = generated_text[3:]
            if generated_text.endswith("```"):
                generated_text = generated_text[:-3]
                
            generated_text = generated_text.strip()
            
            try:
                # Try parsing as JSON first
                indices = json.loads(generated_text)
                if not isinstance(indices, list):
                    indices = [indices]
            except json.JSONDecodeError:
                # Fallback: extract all numbers from the text using regex
                numbers = re.findall(r'\d+', generated_text)
                indices = [int(n) for n in numbers]
                
            print(f"Parsed indices: {indices}")
            
            # Verify indices and map to the actual article dictionaries
            valid_articles = []
            for idx in indices:
                try:
                    i = int(idx)
                    if 0 <= i < len(articles):
                        valid_articles.append(articles[i])
                except (ValueError, TypeError):
                    pass
            
            if not valid_articles and indices:
                # If we parsed numbers but none were valid indices, fallback
                print("Parsed indices but none were valid. Returning all articles.")
                return articles
                
            return valid_articles
        else:
            print(f"Unexpected API response format: {result}")
            return articles
            
    except Exception as e:
        print(f"Error calling OpenRouter: {e}")
        return articles

def save_to_json(articles: List[Dict], filepath: str = "data/news.json") -> bool:
    """
    Save the filtered articles to a JSON file. Overwrites the file each time.
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        return False
