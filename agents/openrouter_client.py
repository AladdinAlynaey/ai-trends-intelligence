"""
OpenRouter API client — single gateway for all LLM and image-gen calls.
"""
import requests
import time
import logging
from config import Config

logger = logging.getLogger(__name__)

_HEADERS = {
    "Content-Type": "application/json",
    "HTTP-Referer": "https://ai-trends-platform.local",
    "X-Title": "AI Trends Intelligence Platform",
}


def _get_headers() -> dict:
    return {**_HEADERS, "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}"}


def is_configured() -> bool:
    """Check if OpenRouter API key is properly configured."""
    key = Config.OPENROUTER_API_KEY
    return bool(key) and key != "sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxx" and len(key) > 10


def chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    retries: int = 2,
) -> str:
    """Send a chat completion request to OpenRouter. Returns assistant text."""
    if not is_configured():
        logger.warning("OpenRouter API key not configured — skipping AI call")
        return "[AI Unavailable] OpenRouter API key is not configured. Add your key to the .env file."

    model = model or Config.OPENROUTER_LLM_MODEL
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    last_err = None
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                f"{Config.OPENROUTER_BASE_URL}/chat/completions",
                json=payload,
                headers=_get_headers(),
                timeout=60,
            )
            if resp.status_code == 401:
                logger.error("OpenRouter 401 Unauthorized — check your API key")
                return "[AI Error] Invalid OpenRouter API key. Check your .env OPENROUTER_API_KEY."
            if resp.status_code == 429:
                wait = 2 ** attempt
                logger.warning("Rate limited by OpenRouter, retrying in %ss", wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.HTTPError as e:
            last_err = e
            if attempt < retries:
                time.sleep(1)
                continue
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(1)
                continue

    logger.error("OpenRouter chat_completion failed: %s", last_err)
    return f"[AI Error] {last_err}"


def generate_image(
    prompt: str,
    model: str | None = None,
    retries: int = 2,
) -> str | None:
    """Generate an image via OpenRouter. Returns base64 data or URL."""
    if not is_configured():
        logger.warning("OpenRouter API key not configured — skipping image gen")
        return None

    model = model or Config.OPENROUTER_IMAGE_MODEL
    payload = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "response_format": "b64_json",
    }

    last_err = None
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                f"{Config.OPENROUTER_BASE_URL}/images/generations",
                json=payload,
                headers=_get_headers(),
                timeout=120,
            )
            if resp.status_code == 401:
                logger.error("OpenRouter 401 — invalid API key for image gen")
                return None
            if resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            data = resp.json()
            # OpenRouter may return b64_json or url
            item = data.get("data", [{}])[0]
            return item.get("b64_json") or item.get("url")
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(1)
                continue

    logger.error("OpenRouter image generation failed: %s", last_err)
    return None
