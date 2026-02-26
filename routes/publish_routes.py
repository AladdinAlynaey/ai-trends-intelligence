"""
Publishing routes — queue, publish, schedule, preview.
"""
from flask import Blueprint, request, jsonify, g
from security.auth import login_required, admin_required
from services.publisher import (
    add_to_queue, process_queue, get_queue_status, get_platform_status,
)
from data.store import read_json, find_item
from config import Config

publish_bp = Blueprint("publish", __name__, url_prefix="/api/publish")


@publish_bp.route("/queue", methods=["POST"])
@login_required
def add_to_publish_queue():
    """Add content to the publishing queue."""
    data = request.get_json(silent=True) or {}
    article_id = data.get("article_id", "")
    platforms = data.get("platforms", [])
    content = data.get("content", {})
    scheduled_at = data.get("scheduled_at")
    auto_publish = data.get("auto_publish", False)

    if not article_id:
        return jsonify({"error": "article_id is required"}), 400
    if not platforms:
        return jsonify({"error": "At least one platform required"}), 400

    article = find_item(Config.ARTICLES_FILE, "id", article_id)
    if not article:
        return jsonify({"error": "Article not found"}), 404

    item = add_to_queue(
        article_id=article_id,
        content=content,
        platforms=platforms,
        scheduled_at=scheduled_at,
        auto_publish=auto_publish,
    )

    return jsonify({"message": "Added to queue", "item": item}), 201


@publish_bp.route("/process", methods=["POST"])
@admin_required
def process_publish_queue():
    """Process the publishing queue (admin only)."""
    results = process_queue()

    # Send Telegram notifications
    from services.telegram_bot import notify_publishing
    for item in results:
        article = find_item(Config.ARTICLES_FILE, "id", item.get("article_id", ""))
        title = article.get("title", "Unknown") if article else "Unknown"
        notify_publishing(title, item.get("platforms", []), item.get("results", {}))

    return jsonify({
        "message": f"Processed {len(results)} items",
        "results": results,
    })


@publish_bp.route("/queue", methods=["GET"])
@login_required
def get_queue():
    """Get publishing queue items."""
    queue = read_json(Config.PUBLISH_QUEUE_FILE, [])
    status_filter = request.args.get("status")

    if status_filter:
        queue = [q for q in queue if q.get("status") == status_filter]

    return jsonify({"queue": queue, "stats": get_queue_status()})


@publish_bp.route("/history", methods=["GET"])
@login_required
def get_history():
    """Get publishing history."""
    history = read_json(Config.PUBLISH_HISTORY_FILE, [])
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    total = len(history)
    start = (page - 1) * per_page
    page_items = history[start:start + per_page]

    return jsonify({
        "history": page_items,
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@publish_bp.route("/platforms", methods=["GET"])
@login_required
def get_platforms():
    """Get platform status."""
    return jsonify({"platforms": get_platform_status()})


@publish_bp.route("/preview", methods=["POST"])
@login_required
def preview_post():
    """Generate a preview of what will be published."""
    data = request.get_json(silent=True) or {}
    article_id = data.get("article_id", "")
    platform = data.get("platform", "general")

    article = find_item(Config.ARTICLES_FILE, "id", article_id)
    if not article:
        return jsonify({"error": "Article not found"}), 404

    from agents.content_agent import generate_content
    from agents.hashtag_agent import generate_hashtags

    trends = read_json(Config.TRENDS_FILE, [])
    trend = None
    for t in trends:
        if t.get("article_id") == article_id:
            trend = t
            break

    content = generate_content(
        title=article.get("title", ""),
        summary=article.get("summary", ""),
        category=trend.get("category", "") if trend else "",
        platform=platform,
        trend_score=trend.get("trend_score", 50) if trend else 50,
    )

    hashtags = generate_hashtags(
        title=article.get("title", ""),
        category=trend.get("category", "") if trend else "",
        platform=platform,
    )

    return jsonify({
        "preview": {
            "content": content,
            "hashtags": hashtags,
            "platform": platform,
            "article": {
                "title": article.get("title"),
                "source": article.get("source"),
                "link": article.get("link"),
            },
        }
    })


@publish_bp.route("/telegram", methods=["POST"])
@login_required
def publish_to_telegram():
    """Send a complete trend post to Telegram (image + text + hashtags)."""
    data = request.get_json(silent=True) or {}
    article_id = data.get("article_id", "")
    custom_title = data.get("title", "")
    custom_body = data.get("body", "")
    custom_hashtags = data.get("hashtags", "")
    custom_cta = data.get("cta", "")
    generate_img = data.get("generate_image", False)

    # Get article info
    article = find_item(Config.ARTICLES_FILE, "id", article_id) if article_id else None

    title = custom_title or (article.get("title", "AI Trend") if article else "AI Trend Post")
    body = custom_body or (article.get("summary", "") if article else "")
    link = article.get("link", "") if article else ""

    # Get trend data for hashtags
    if not custom_hashtags and article:
        trends = read_json(Config.TRENDS_FILE, [])
        for t in trends:
            if t.get("article_id") == article_id:
                # Auto-generate some hashtags from category
                cat = t.get("category", "")
                custom_hashtags = f"#AI #{cat.replace(' ', '')} #ArtificialIntelligence #Tech"
                break
        if not custom_hashtags:
            custom_hashtags = "#AI #ArtificialIntelligence #MachineLearning #Tech"

    # Optionally generate image
    image_path = ""
    if generate_img:
        from agents.image_agent import generate_trend_image
        img_result = generate_trend_image(title, body)
        if img_result.get("success"):
            image_path = img_result.get("filepath", "")

    # Send to Telegram
    from services.telegram_bot import publish_trend_post
    result = publish_trend_post(
        title=title,
        body=body,
        hashtags=custom_hashtags,
        image_path=image_path,
        link=link,
        cta=custom_cta,
    )

    # Log to publish history
    from data.store import append_item, utcnow
    append_item(Config.PUBLISH_HISTORY_FILE, {
        "article_id": article_id,
        "platforms": ["telegram"],
        "results": {"telegram": result},
        "content": {"title": title, "body": body[:200], "hashtags": custom_hashtags},
    })

    return jsonify(result)


@publish_bp.route("/ai-status", methods=["GET"])
@login_required
def check_ai_status():
    """Check if OpenRouter AI is properly configured."""
    import os
    from agents.openrouter_client import is_configured
    return jsonify({
        "ai_configured": is_configured(),
        "telegram_enabled": Config.TELEGRAM_ENABLED,
        "telegram_configured": bool(Config.TELEGRAM_BOT_TOKEN and Config.TELEGRAM_ADMIN_CHAT_ID),
        "twitter_configured": bool(os.getenv("TWITTER_API_KEY")),
        "linkedin_configured": bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
        "krea_configured": bool(os.getenv("KREA_API_KEY")),
    })


@publish_bp.route("/image-models", methods=["GET"])
@login_required
def get_image_models():
    """Return list of available image generation models."""
    from agents.image_agent import get_available_models
    return jsonify({"models": get_available_models()})


@publish_bp.route("/create-post", methods=["POST"])
@login_required
def create_and_publish_post():
    """Create a post from user-edited text and publish to connected platforms.
    Accepts: title, body, hashtags, cta, link, generate_image, image_model,
    language, platforms (telegram, twitter, linkedin, reddit).
    """
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    body = data.get("body", "").strip()
    hashtags = data.get("hashtags", "").strip()
    cta = data.get("cta", "").strip()
    link = data.get("link", "").strip()
    generate_img = data.get("generate_image", False)
    image_model = data.get("image_model", "auto")
    image_style = data.get("image_style", "auto")
    image_size = data.get("image_size", "auto")
    language = data.get("language", "en")
    platforms = data.get("platforms", ["telegram"])

    if not title and not body:
        return jsonify({"error": "Title or body is required"}), 400

    results = {}

    # Generate image if requested
    image_path = ""
    image_url = ""
    if generate_img:
        from agents.image_agent import generate_trend_image
        img_result = generate_trend_image(
            title or body[:100], body[:200], model=image_model,
            style=image_style, size=image_size,
        )
        if img_result.get("success"):
            image_path = img_result.get("filepath", "")
            image_url = img_result.get("url", "")

    # Send to Telegram
    if "telegram" in platforms:
        from services.telegram_bot import publish_trend_post
        tg_result = publish_trend_post(
            title=title, body=body, hashtags=hashtags,
            image_path=image_path, link=link, cta=cta,
        )
        results["telegram"] = tg_result

    # Twitter (stub — requires API key configuration)
    if "twitter" in platforms:
        import os
        if os.getenv("TWITTER_API_KEY"):
            results["twitter"] = _post_to_twitter(title, body, hashtags, image_path, link)
        else:
            results["twitter"] = {"success": False, "error": "Twitter API key not configured. Add TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET in Settings."}

    # LinkedIn (stub — requires API key configuration)
    if "linkedin" in platforms:
        import os
        if os.getenv("LINKEDIN_ACCESS_TOKEN"):
            results["linkedin"] = _post_to_linkedin(title, body, hashtags, image_path, link)
        else:
            results["linkedin"] = {"success": False, "error": "LinkedIn not configured. Add LINKEDIN_ACCESS_TOKEN in Settings."}

    # Log to publish history
    from data.store import append_item, utcnow
    append_item(Config.PUBLISH_HISTORY_FILE, {
        "type": "custom_post",
        "platforms": platforms,
        "results": results,
        "content": {"title": title, "body": body[:500], "hashtags": hashtags},
        "image_url": image_url,
        "language": language,
    })

    all_success = all(r.get("success", False) for r in results.values()) if results else False

    return jsonify({
        "success": all_success,
        "results": results,
        "image_url": image_url,
        "platforms_sent": list(results.keys()),
    })


def _post_to_twitter(title, body, hashtags, image_path, link):
    """Post to Twitter/X using API v2."""
    import os
    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
        )
        text = f"{title}\n\n{body[:200]}"
        if hashtags:
            text += f"\n\n{hashtags}"
        if link:
            text += f"\n{link}"
        text = text[:280]  # Twitter limit
        resp = client.create_tweet(text=text)
        return {"success": True, "tweet_id": str(resp.data.get("id", "")), "message": "Posted to Twitter!"}
    except ImportError:
        return {"success": False, "error": "tweepy not installed. Run: pip install tweepy"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _post_to_linkedin(title, body, hashtags, image_path, link):
    """Post to LinkedIn using REST API."""
    import os
    try:
        import requests as req
        token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        # Get user profile
        profile_resp = req.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        user_sub = profile_resp.json().get("sub", "")

        text = f"{title}\n\n{body[:700]}"
        if hashtags:
            text += f"\n\n{hashtags}"
        if link:
            text += f"\n\n{link}"

        post_data = {
            "author": f"urn:li:person:{user_sub}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        resp = req.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=post_data, timeout=15,
        )
        if resp.status_code in (200, 201):
            return {"success": True, "message": "Posted to LinkedIn!"}
        return {"success": False, "error": f"LinkedIn API error: {resp.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

