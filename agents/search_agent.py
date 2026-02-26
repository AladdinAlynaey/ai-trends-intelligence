"""
Research & Search Agent — Ultra-powerful AI search engine.
Combines: local article database + real-time web scraping + AI analysis.
More powerful than basic search — scrapes DuckDuckGo for live results.
"""
from agents.openrouter_client import chat_completion, is_configured
from data.store import read_json
from config import Config
import json
import logging
import requests
import re

logger = logging.getLogger(__name__)

SEARCH_SYSTEM_PROMPT = """You are an elite AI Research Analyst and Trend Intelligence Expert.
You are the most powerful AI search engine for technology and AI trends.

You have access to:
1. A curated database of recent AI articles from 50+ top sources
2. Live web search results from the internet

Your job is to provide COMPREHENSIVE, EXPERT-LEVEL answers that rival Perplexity AI.

Requirements:
- Write detailed, insightful analysis (minimum 4-6 paragraphs)
- Include specific data points, names, dates, and numbers
- Cite sources inline using [Source Name] notation
- Highlight emerging patterns and make predictions
- Compare different perspectives and viewpoints
- Include actionable takeaways
- Be specific — never give generic answers

You MUST also generate a suggested social media post about this topic.

Response format (strict JSON):
{
  "answer": "<comprehensive markdown answer — minimum 500 words, use headers, bold, lists>",
  "key_insights": ["<insight 1>", "<insight 2>", "<insight 3>", "<insight 4>", "<insight 5>"],
  "related_trends": ["<trend>", "<trend>"],
  "confidence": <float 0-1>,
  "sources_used": [{"title": "<str>", "url": "<str>", "relevance": "<high/medium/low>"}],
  "suggested_post": {
    "title": "<catchy social media headline>",
    "body": "<engaging post body, 200-500 chars with emojis>",
    "hashtags": "#AI #MachineLearning #relevant #tags",
    "cta": "<call to action>"
  }
}

Write in English. Return ONLY the JSON — no extra text."""


def _scrape_web_results(query: str, max_results: int = 10) -> list[dict]:
    """Scrape real search results from DuckDuckGo HTML (no API key needed)."""
    results = []

    # Method 1: DuckDuckGo HTML scraping
    try:
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            timeout=10,
        )
        if resp.ok:
            html = resp.text
            # Parse results from DuckDuckGo HTML
            result_blocks = re.findall(
                r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.*?)</a>.*?'
                r'<a class="result__snippet"[^>]*>(.*?)</a>',
                html, re.DOTALL
            )
            for url, title, snippet in result_blocks[:max_results]:
                title_clean = re.sub(r'<[^>]+>', '', title).strip()
                snippet_clean = re.sub(r'<[^>]+>', '', snippet).strip()
                if title_clean and snippet_clean:
                    # Decode DuckDuckGo redirect URL
                    if "uddg=" in url:
                        import urllib.parse
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                        url = parsed.get("uddg", [url])[0]
                    results.append({
                        "title": title_clean,
                        "text": snippet_clean,
                        "url": url,
                        "source": "web",
                    })
    except Exception as e:
        logger.warning("DuckDuckGo HTML scraping failed: %s", e)

    # Method 2: DuckDuckGo API (for instant answers)
    if len(results) < 3:
        try:
            resp = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
                timeout=8,
                headers={"User-Agent": "AITrendsPlatform/1.0"},
            )
            data = resp.json()
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", "DuckDuckGo"),
                    "text": data["AbstractText"],
                    "url": data.get("AbstractURL", ""),
                    "source": "encyclopedia",
                })
            for topic in data.get("RelatedTopics", [])[:5]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "text": topic.get("Text", ""),
                        "url": topic.get("FirstURL", ""),
                        "source": "related",
                    })
        except Exception:
            pass

    return results[:max_results]


def search_trends(query: str, max_context_articles: int = 30,
                  include_web: bool = True) -> dict:
    """Ultra-powerful search: local database + live web + AI synthesis."""

    # Load local articles and trends
    articles = read_json(Config.ARTICLES_FILE, [])
    trends = read_json(Config.TRENDS_FILE, [])

    # Score articles by relevance
    query_lower = query.lower()
    query_words = [w for w in query_lower.split() if len(w) > 2]
    scored_articles = []
    for article in articles:
        score = 0
        title = article.get("title", "").lower()
        summary = article.get("summary", "").lower()
        category = article.get("category", "").lower()
        for word in query_words:
            if word in title:
                score += 5
            if word in summary:
                score += 2
            if word in category:
                score += 1
        if score > 0:
            scored_articles.append((score, article))

    scored_articles.sort(key=lambda x: x[0], reverse=True)
    top_articles = scored_articles[:max_context_articles]

    # Build context from local database
    db_parts = []
    for _, art in top_articles:
        trend_info = ""
        for t in trends:
            if t.get("article_id") == art.get("id"):
                trend_info = f" | Score: {t.get('trend_score', 'N/A')} | Category: {t.get('category', 'N/A')}"
                break
        db_parts.append(
            f"- [{art.get('source', 'Unknown')}] {art.get('title', 'Untitled')}"
            f"{trend_info}\n  {art.get('summary', '')[:400]}"
            f"\n  Link: {art.get('link', '')}"
        )

    # Scrape real web results
    web_results = []
    web_context = ""
    if include_web:
        web_results = _scrape_web_results(f"{query} AI technology 2024 2025")
        if web_results:
            web_parts = []
            for wr in web_results:
                web_parts.append(
                    f"- [{wr.get('source', 'Web')}] {wr.get('title', '')}\n"
                    f"  {wr.get('text', '')[:400]}\n"
                    f"  URL: {wr.get('url', '')}"
                )
            web_context = "\n\n── LIVE WEB RESULTS ──\n" + "\n\n".join(web_parts)

    db_context = "\n\n".join(db_parts) if db_parts else "No matching articles in database."

    user_msg = (
        f"User Question: {query}\n\n"
        f"── OUR DATABASE ({len(top_articles)} matches from {len(articles)} total articles) ──\n\n"
        f"{db_context}"
        f"{web_context}"
    )

    # Call AI for synthesis
    if not is_configured():
        return {
            "query": query,
            "answer": "⚠️ AI not configured. Add your OpenRouter API key in Settings to enable AI-powered search.",
            "key_insights": [],
            "related_trends": [],
            "confidence": 0,
            "sources_used": [],
            "suggested_post": None,
            "articles_searched": len(articles),
            "articles_matched": len(top_articles),
            "web_results": len(web_results),
        }

    response = chat_completion(
        messages=[
            {"role": "system", "content": SEARCH_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.4,
        max_tokens=4000,
    )

    # Parse response
    try:
        text = response.strip()
        # Clean markdown code fences
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        if text.startswith("json"):
            text = text[4:].strip()
        result = json.loads(text)
        result["query"] = query
        result["articles_searched"] = len(articles)
        result["articles_matched"] = len(top_articles)
        result["web_results"] = len(web_results)
        return result
    except json.JSONDecodeError:
        logger.warning("Failed to parse search response: %s", response[:300])
        return {
            "query": query,
            "answer": response if "[AI" not in response else "Search failed — check AI configuration.",
            "key_insights": [],
            "related_trends": [],
            "confidence": 0.5,
            "sources_used": [],
            "suggested_post": None,
            "articles_searched": len(articles),
            "articles_matched": len(top_articles),
            "web_results": len(web_results),
        }
