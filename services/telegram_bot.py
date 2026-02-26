"""
Telegram Bot — sends admin notifications AND full post publishing
with image + text + hashtags.
"""
import os
import logging
import requests
from config import Config

logger = logging.getLogger(__name__)


def _api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/{method}"


def _check_enabled() -> bool:
    if not Config.TELEGRAM_ENABLED:
        return False
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_ADMIN_CHAT_ID:
        logger.warning("Telegram bot token or chat ID not configured")
        return False
    return True


# ── Basic Message ──────────────────────────────────

def _send_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send a text message to the admin Telegram chat."""
    if not _check_enabled():
        return False

    payload = {
        "chat_id": Config.TELEGRAM_ADMIN_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
    }

    try:
        resp = requests.post(_api_url("sendMessage"), json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Failed to send Telegram message: %s", e)
        return False


# ── Photo Message ──────────────────────────────────

def send_photo(photo_path: str, caption: str = "",
               parse_mode: str = "HTML") -> bool:
    """Send a photo with caption to the admin Telegram chat."""
    if not _check_enabled():
        return False

    try:
        with open(photo_path, "rb") as photo_file:
            files = {"photo": photo_file}
            data = {
                "chat_id": Config.TELEGRAM_ADMIN_CHAT_ID,
                "caption": caption[:1024],  # Telegram caption limit
                "parse_mode": parse_mode,
            }
            resp = requests.post(
                _api_url("sendPhoto"), data=data, files=files, timeout=30
            )
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error("Failed to send Telegram photo: %s", e)
        return False


def send_photo_url(photo_url: str, caption: str = "",
                   parse_mode: str = "HTML") -> bool:
    """Send a photo by URL with caption to the admin Telegram chat."""
    if not _check_enabled():
        return False

    payload = {
        "chat_id": Config.TELEGRAM_ADMIN_CHAT_ID,
        "photo": photo_url,
        "caption": caption[:1024],
        "parse_mode": parse_mode,
    }

    try:
        resp = requests.post(_api_url("sendPhoto"), json=payload, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Failed to send Telegram photo URL: %s", e)
        return False


# ── Full Post Publishing ──────────────────────────

def publish_trend_post(title: str, body: str, hashtags: str = "",
                       image_path: str = "", link: str = "",
                       cta: str = "") -> dict:
    """
    Publish a complete trend post to Telegram with image + text + hashtags.
    Returns a result dict with success status.
    """
    if not _check_enabled():
        return {"success": False, "error": "Telegram is disabled"}

    # Build the caption/text
    parts = []
    parts.append(f"🔥 <b>{title}</b>")
    parts.append("")

    if body:
        parts.append(body)
        parts.append("")

    if cta:
        parts.append(f"💡 {cta}")
        parts.append("")

    if link:
        parts.append(f"🔗 <a href=\"{link}\">Read Full Article</a>")
        parts.append("")

    if hashtags:
        parts.append(hashtags)

    full_text = "\n".join(parts)

    # Send with photo if available
    if image_path and os.path.exists(image_path):
        # Photo caption has 1024 char limit — if text is long, send separately
        if len(full_text) <= 1024:
            success = send_photo(image_path, full_text)
            return {
                "success": success,
                "method": "photo_with_caption",
                "message": "Post with image sent to Telegram" if success else "Failed to send",
            }
        else:
            # Send photo first, then text
            photo_ok = send_photo(image_path, f"🔥 <b>{title}</b>")
            text_ok = _send_message(full_text)
            return {
                "success": photo_ok and text_ok,
                "method": "photo_then_text",
                "message": "Post with image sent to Telegram" if (photo_ok and text_ok) else "Partial send",
            }
    else:
        # Text-only post
        success = _send_message(full_text)
        return {
            "success": success,
            "method": "text_only",
            "message": "Text post sent to Telegram" if success else "Failed to send",
        }


# ── Notification Functions ────────────────────────

def notify_new_trends(trends: list[dict]) -> bool:
    """Notify admin about new high-scoring trends."""
    if not trends:
        return False

    msg = "🔥 <b>New AI Trends Detected</b>\n\n"
    for t in trends[:5]:
        score = t.get("trend_score", 0)
        emoji = "🚀" if score >= 80 else "📈" if score >= 60 else "📊"
        msg += (
            f"{emoji} <b>{t.get('title', 'Unknown')}</b>\n"
            f"   Score: {score}/100 | Category: {t.get('category', 'N/A')}\n"
            f"   {t.get('impact_summary', '')[:100]}\n\n"
        )

    if len(trends) > 5:
        msg += f"... and {len(trends) - 5} more trends\n"

    return _send_message(msg)


def notify_publishing(article_title: str, platforms: list[str],
                      results: dict) -> bool:
    """Notify admin about publishing actions."""
    msg = "📢 <b>Content Published</b>\n\n"
    msg += f"📝 <b>{article_title}</b>\n\n"

    for platform, result in results.items():
        status = "✅" if result.get("success") else "❌"
        msg += f"{status} {platform.title()}: {result.get('message', result.get('error', 'Unknown'))}\n"

    return _send_message(msg)


def notify_error(error_type: str, details: str) -> bool:
    """Notify admin about system errors."""
    msg = (
        f"⚠️ <b>System Alert: {error_type}</b>\n\n"
        f"{details[:500]}"
    )
    return _send_message(msg)


def notify_system_status(stats: dict) -> bool:
    """Send system status update."""
    msg = (
        "📊 <b>System Status Update</b>\n\n"
        f"📰 Articles: {stats.get('total_articles', 0)}\n"
        f"📈 Trends: {stats.get('total_trends', 0)}\n"
        f"📤 Published: {stats.get('total_published', 0)}\n"
        f"⏳ Queue: {stats.get('queue_pending', 0)} pending\n"
    )
    return _send_message(msg)
