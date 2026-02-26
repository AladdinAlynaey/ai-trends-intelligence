"""
Content Generation Agent — produces professional social-media-ready content.
"""
from agents.openrouter_client import chat_completion
import json
import logging

logger = logging.getLogger(__name__)

LANGUAGE_MAP = {
    "en": "English", "ar": "Arabic (العربية)", "fr": "French",
    "es": "Spanish", "de": "German", "zh": "Chinese (Mandarin)",
    "ja": "Japanese", "ko": "Korean", "pt": "Portuguese",
    "ru": "Russian", "tr": "Turkish", "hi": "Hindi",
}

SYSTEM_PROMPT = """You are an elite AI Content Strategist who creates premium, 
engaging social media content about AI trends. You write in a professional yet 
approachable style that balances technical depth with accessibility.

When given a trend/article, produce content optimized for the requested platform.

Always respond with a valid JSON object:
{
  "title": "<catchy headline>",
  "body": "<main content text>",
  "hook": "<attention-grabbing opening line>",
  "cta": "<call to action>",
  "key_points": ["<string>", ...]
}

Platform guidelines:
- Twitter/X: Max 280 chars for body. Punchy, direct, use emojis sparingly.
- LinkedIn: Professional tone, 500-1000 chars. Include insights and takeaways.
- Reddit: Informative, discussion-oriented, 300-800 chars.
- General: Balanced, 200-500 chars."""


def generate_content(title: str, summary: str, category: str = "",
                     platform: str = "general",
                     trend_score: int = 50,
                     language: str = "en") -> dict:
    """Generate platform-optimized content for an AI trend."""
    lang_name = LANGUAGE_MAP.get(language, "English")
    lang_instruction = ""
    if language != "en":
        lang_instruction = (
            f"\n\n⚠️ CRITICAL: Write ALL output in {lang_name}. "
            f"The title, body, hook, cta, and key_points MUST ALL be written in {lang_name}. "
            f"Do NOT write in English."
        )

    user_msg = (
        f"Create {platform} content for this AI trend:\n\n"
        f"Title: {title}\n"
        f"Category: {category}\n"
        f"Trend Score: {trend_score}/100\n"
        f"Summary: {summary}\n\n"
        f"Platform: {platform}"
        f"{lang_instruction}"
    )

    response = chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.7,
        max_tokens=1024,
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
        logger.warning("Failed to parse content generation: %s", response[:200])
        return {
            "title": title,
            "body": summary[:500] if summary else title,
            "hook": title,
            "cta": "What do you think about this AI development?",
            "key_points": [],
        }


def generate_multi_platform(title: str, summary: str, category: str = "",
                            trend_score: int = 50,
                            platforms: list[str] | None = None) -> dict:
    """Generate content for multiple platforms at once."""
    platforms = platforms or ["twitter", "linkedin", "general"]
    results = {}
    for platform in platforms:
        results[platform] = generate_content(
            title=title,
            summary=summary,
            category=category,
            platform=platform,
            trend_score=trend_score,
        )
    return results
