"""
Publishing system — manages content publishing to social platforms.
"""
import logging
from datetime import datetime, timezone

from config import Config
from data.store import (
    read_json, write_json, append_item, update_item,
    generate_id, utcnow
)

logger = logging.getLogger(__name__)


# ── Platform Publishers ───────────────────────────

def _publish_twitter(content: dict) -> dict:
    """Publish to Twitter/X. Returns result dict."""
    if not Config.PUBLISH_TWITTER_ENABLED:
        return {"success": False, "error": "Twitter publishing is disabled"}

    # Real Twitter API integration placeholder
    # In production, use tweepy or requests with OAuth
    logger.info("Publishing to Twitter: %s", content.get("title", "")[:50])
    return {
        "success": True,
        "platform": "twitter",
        "message": "Tweet published successfully",
        "published_at": utcnow(),
    }


def _publish_linkedin(content: dict) -> dict:
    """Publish to LinkedIn."""
    if not Config.PUBLISH_LINKEDIN_ENABLED:
        return {"success": False, "error": "LinkedIn publishing is disabled"}

    logger.info("Publishing to LinkedIn: %s", content.get("title", "")[:50])
    return {
        "success": True,
        "platform": "linkedin",
        "message": "LinkedIn post published successfully",
        "published_at": utcnow(),
    }


def _publish_reddit(content: dict) -> dict:
    """Publish to Reddit."""
    if not Config.PUBLISH_REDDIT_ENABLED:
        return {"success": False, "error": "Reddit publishing is disabled"}

    logger.info("Publishing to Reddit: %s", content.get("title", "")[:50])
    return {
        "success": True,
        "platform": "reddit",
        "message": "Reddit post published successfully",
        "published_at": utcnow(),
    }


PUBLISHERS = {
    "twitter": _publish_twitter,
    "linkedin": _publish_linkedin,
    "reddit": _publish_reddit,
}


# ── Queue Management ─────────────────────────────

def add_to_queue(article_id: str, content: dict, platforms: list[str],
                 scheduled_at: str | None = None,
                 auto_publish: bool = False) -> dict:
    """Add content to the publishing queue."""
    item = {
        "id": generate_id(),
        "article_id": article_id,
        "content": content,
        "platforms": platforms,
        "status": "scheduled" if scheduled_at else "pending",
        "scheduled_at": scheduled_at,
        "auto_publish": auto_publish,
        "created_at": utcnow(),
        "results": {},
    }
    return append_item(Config.PUBLISH_QUEUE_FILE, item)


def process_queue() -> list[dict]:
    """Process pending items in the publishing queue."""
    queue = read_json(Config.PUBLISH_QUEUE_FILE, [])
    results = []
    now = datetime.now(timezone.utc)

    for item in queue:
        if item.get("status") not in ("pending", "scheduled"):
            continue

        # Check schedule
        if item.get("scheduled_at"):
            try:
                from dateutil import parser as dp
                sched_time = dp.parse(item["scheduled_at"])
                if sched_time > now:
                    continue
            except (ValueError, TypeError):
                pass

        # Publish to each platform
        item_results = {}
        for platform in item.get("platforms", []):
            publisher = PUBLISHERS.get(platform)
            if publisher:
                result = publisher(item.get("content", {}))
                item_results[platform] = result
            else:
                item_results[platform] = {
                    "success": False,
                    "error": f"Unknown platform: {platform}",
                }

        item["results"] = item_results
        item["status"] = "published"
        item["published_at"] = utcnow()

        # Save to history
        append_item(Config.PUBLISH_HISTORY_FILE, {
            "queue_item_id": item.get("id"),
            "article_id": item.get("article_id"),
            "platforms": item.get("platforms"),
            "results": item_results,
        })

        results.append(item)

    write_json(Config.PUBLISH_QUEUE_FILE, queue)
    return results


def get_queue_status() -> dict:
    """Get current queue statistics."""
    queue = read_json(Config.PUBLISH_QUEUE_FILE, [])
    history = read_json(Config.PUBLISH_HISTORY_FILE, [])

    pending = sum(1 for q in queue if q.get("status") == "pending")
    scheduled = sum(1 for q in queue if q.get("status") == "scheduled")
    published = sum(1 for q in queue if q.get("status") == "published")

    return {
        "pending": pending,
        "scheduled": scheduled,
        "published": published,
        "total_queue": len(queue),
        "total_history": len(history),
    }


def get_platform_status() -> dict:
    """Get enabled/disabled status of all platforms."""
    return {
        "twitter": {
            "enabled": Config.PUBLISH_TWITTER_ENABLED,
            "configured": bool(Config.TWITTER_API_KEY),
        },
        "linkedin": {
            "enabled": Config.PUBLISH_LINKEDIN_ENABLED,
            "configured": bool(Config.LINKEDIN_ACCESS_TOKEN),
        },
        "reddit": {
            "enabled": Config.PUBLISH_REDDIT_ENABLED,
            "configured": bool(Config.REDDIT_CLIENT_ID),
        },
    }
