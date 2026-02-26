"""
Hashtag Intelligence Agent — generates platform-optimized hashtags.
"""
from agents.openrouter_client import chat_completion
import json
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a social media hashtag strategist specializing in AI and 
technology content. Generate relevant, high-engagement hashtags for AI trend posts.

Rules:
- Return a JSON object with platform-specific hashtag lists
- Mix broad-reach and niche hashtags
- Include trending AI-specific tags
- No spaces in hashtags
- All hashtags must start with #

Response format:
{
  "universal": ["#AI", "#ArtificialIntelligence", ...],
  "twitter": ["#AITwitter", "#TechTwitter", ...],
  "linkedin": ["#AIInnovation", "#FutureOfWork", ...],
  "trending": ["<currently trending AI tags>"],
  "niche": ["<specific to this topic>"]
}

Return ONLY the JSON object."""


def generate_hashtags(title: str, category: str = "",
                      sub_topics: list[str] | None = None,
                      platform: str = "general") -> dict:
    """Generate optimized hashtags for a trend post."""
    topics_str = ", ".join(sub_topics) if sub_topics else "general AI"
    user_msg = (
        f"Generate hashtags for this AI trend:\n"
        f"Title: {title}\n"
        f"Category: {category}\n"
        f"Topics: {topics_str}\n"
        f"Primary platform: {platform}"
    )

    response = chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.6,
        max_tokens=400,
    )

    try:
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
        logger.warning("Failed to parse hashtags: %s", response[:200])
        return {
            "universal": ["#AI", "#ArtificialIntelligence", "#MachineLearning"],
            "twitter": ["#AITwitter", "#Tech"],
            "linkedin": ["#AIInnovation", "#Technology"],
            "trending": [],
            "niche": [],
        }
