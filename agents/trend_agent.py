"""
Trend Analysis Agent — scores and categorises incoming articles.
"""
from agents.openrouter_client import chat_completion
import json
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert AI Trend Analyst. Your role is to analyze AI-related 
news articles and produce structured intelligence.

For each article you receive, you MUST return a valid JSON object with these fields:
{
  "trend_score": <int 0-100>,
  "category": "<string: one of Research, Industry, Product, Policy, Ethics, Open Source, Funding, Hardware, Robotics, AGI, Cybersecurity, Healthcare, NLP, Computer Vision, Autonomous Vehicles, Education, Finance, Gaming, Climate, Defense, Enterprise AI, Generative AI, AI Infrastructure, AI Safety, AI Tools, Data Science, Edge AI, Quantum AI>",
  "sub_topics": ["<string>", ...],
  "impact_summary": "<string: 1-2 sentence impact analysis>",
  "key_entities": ["<company/org/person names>"],
  "is_duplicate_likely": <bool>,
  "duplicate_reason": "<string or null>"
}

Scoring guidelines:
- 90-100: Paradigm-shifting breakthrough (new architecture, major regulation)
- 70-89:  Significant industry impact (major product launch, large funding round)
- 50-69:  Noteworthy development (model update, partnership)
- 30-49:  Minor news (feature update, opinion piece)
- 0-29:   Low relevance or old news

Always respond with ONLY the JSON object, no extra text."""


def analyze_article(title: str, summary: str, source: str = "",
                    existing_titles: list[str] | None = None) -> dict:
    """Analyze a single article and return structured trend data."""
    context = ""
    if existing_titles:
        context = (
            "\n\nRecent article titles already processed (check for duplicates):\n"
            + "\n".join(f"- {t}" for t in existing_titles[:30])
        )

    user_msg = (
        f"Analyze this AI news article:\n\n"
        f"Title: {title}\n"
        f"Source: {source}\n"
        f"Summary: {summary}"
        f"{context}"
    )

    response = chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=500,
    )

    try:
        # Strip markdown code fences if present
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        if text.startswith("json"):
            text = text[4:].strip()
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse trend analysis response: %s", response[:200])
        return {
            "trend_score": 30,
            "category": "Industry",
            "sub_topics": [],
            "impact_summary": summary[:200] if summary else title,
            "key_entities": [],
            "is_duplicate_likely": False,
            "duplicate_reason": None,
        }


def batch_analyze(articles: list[dict],
                  existing_titles: list[str] | None = None) -> list[dict]:
    """Analyze a batch of articles. Returns list of analysis results."""
    results = []
    for article in articles:
        analysis = analyze_article(
            title=article.get("title", ""),
            summary=article.get("summary", ""),
            source=article.get("source", ""),
            existing_titles=existing_titles,
        )
        analysis["article_id"] = article.get("id", "")
        results.append(analysis)
        # Update existing titles for dedup
        if existing_titles is not None:
            existing_titles.append(article.get("title", ""))
    return results
