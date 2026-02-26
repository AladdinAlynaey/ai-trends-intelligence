"""
Trend routes — articles, trends, analysis, content generation.
"""
from flask import Blueprint, request, jsonify, g

from security.auth import login_required, admin_required
from data.store import read_json, write_json, find_item, update_item
from config import Config

trends_bp = Blueprint("trends", __name__, url_prefix="/api/trends")


@trends_bp.route("", methods=["GET"])
@login_required
def get_trends():
    """Get all trends with filtering and sorting."""
    trends = read_json(Config.TRENDS_FILE, [])
    articles = read_json(Config.ARTICLES_FILE, [])

    # Build article lookup
    art_map = {a["id"]: a for a in articles}

    # Filters
    category = request.args.get("category")
    min_score = request.args.get("min_score", type=int)
    max_score = request.args.get("max_score", type=int)
    search = request.args.get("search", "").lower()
    sort_by = request.args.get("sort", "trend_score")
    order = request.args.get("order", "desc")
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    filtered = []
    for t in trends:
        if category and t.get("category", "").lower() != category.lower():
            continue
        if min_score is not None and t.get("trend_score", 0) < min_score:
            continue
        if max_score is not None and t.get("trend_score", 0) > max_score:
            continue

        # Enrich with article data
        art = art_map.get(t.get("article_id", ""), {})
        t["article_title"] = art.get("title", "")
        t["article_link"] = art.get("link", "")
        t["article_source"] = art.get("source", "")
        t["article_summary"] = art.get("summary", "")
        t["published_at"] = art.get("published_at", "")

        if search:
            searchable = (
                t.get("article_title", "").lower()
                + t.get("category", "").lower()
                + t.get("impact_summary", "").lower()
                + " ".join(t.get("sub_topics", [])).lower()
            )
            if search not in searchable:
                continue

        filtered.append(t)

    # Sort
    reverse = order == "desc"
    if sort_by == "trend_score":
        filtered.sort(key=lambda x: x.get("trend_score", 0), reverse=reverse)
    elif sort_by == "date":
        filtered.sort(key=lambda x: x.get("published_at", ""), reverse=reverse)
    elif sort_by == "category":
        filtered.sort(key=lambda x: x.get("category", ""), reverse=reverse)

    # Paginate
    total = len(filtered)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = filtered[start:end]

    return jsonify({
        "trends": page_items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    })


@trends_bp.route("/articles", methods=["GET"])
@login_required
def get_articles():
    """Get all articles with optional search and category filter."""
    articles = read_json(Config.ARTICLES_FILE, [])
    limit = request.args.get("limit", 500, type=int)

    search = request.args.get("search", "").lower()
    category = request.args.get("category", "")

    if search:
        articles = [a for a in articles if
                    search in (a.get("title") or "").lower() or
                    search in (a.get("source") or "").lower() or
                    search in (a.get("summary") or "").lower()]
    if category:
        articles = [a for a in articles if a.get("category") == category]

    # Sort newest first by default
    articles.sort(key=lambda a: a.get("published") or a.get("fetched_at") or "", reverse=True)
    articles = articles[:limit]

    return jsonify({"articles": articles, "total": len(articles)})


@trends_bp.route("/scrape-article", methods=["POST"])
@login_required
def scrape_article():
    """Scrape article content from a URL for post creation."""
    import requests as req
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"success": False, "error": "URL is required"}), 400

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        resp = req.get(url, headers=headers, timeout=15, allow_redirects=True)
        resp.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove noise
        for tag in soup(["script", "style", "nav", "header", "footer",
                         "aside", "iframe", "noscript", "form", "button"]):
            tag.decompose()

        # Try to find main article content
        article = soup.find("article") or soup.find("main") or soup.find(
            "div", class_=lambda c: c and ("article" in c or "content" in c or "post" in c)
        )

        if article:
            text = article.get_text(separator="\n", strip=True)
        else:
            # Fallback: grab all paragraphs
            paragraphs = soup.find_all("p")
            text = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30)

        # Clean up
        lines = [line.strip() for line in text.split("\n") if line.strip() and len(line.strip()) > 15]
        content = "\n".join(lines[:50])[:3000]

        if len(content) < 50:
            return jsonify({"success": False, "error": "Could not extract meaningful content"})

        return jsonify({"success": True, "content": content, "length": len(content)})
    except req.exceptions.Timeout:
        return jsonify({"success": False, "error": "Request timed out"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@trends_bp.route("/<trend_id>", methods=["GET"])
@login_required
def get_trend_detail(trend_id):
    """Get detailed information about a specific trend."""
    trends = read_json(Config.TRENDS_FILE, [])
    trend = None
    for t in trends:
        if t.get("article_id") == trend_id or t.get("id") == trend_id:
            trend = t
            break

    if not trend:
        return jsonify({"error": "Trend not found"}), 404

    # Enrich
    articles = read_json(Config.ARTICLES_FILE, [])
    for a in articles:
        if a["id"] == trend.get("article_id"):
            trend["article"] = a
            break

    return jsonify(trend)


@trends_bp.route("/categories", methods=["GET"])
@login_required
def get_categories():
    """Get all unique categories with counts."""
    trends = read_json(Config.TRENDS_FILE, [])
    cats = {}
    for t in trends:
        cat = t.get("category", "Unknown")
        cats[cat] = cats.get(cat, 0) + 1

    return jsonify({
        "categories": [
            {"name": k, "count": v}
            for k, v in sorted(cats.items(), key=lambda x: x[1], reverse=True)
        ]
    })


@trends_bp.route("/stats", methods=["GET"])
@login_required
def get_stats():
    """Get trend statistics."""
    articles = read_json(Config.ARTICLES_FILE, [])
    trends = read_json(Config.TRENDS_FILE, [])
    feeds = read_json(Config.FEEDS_FILE, [])

    scores = [t.get("trend_score", 0) for t in trends if t.get("trend_score")]
    avg_score = sum(scores) / len(scores) if scores else 0

    # Category distribution
    cats = {}
    for t in trends:
        cat = t.get("category", "Unknown")
        cats[cat] = cats.get(cat, 0) + 1

    # Source distribution
    sources = {}
    for a in articles:
        src = a.get("source", "Unknown")
        sources[src] = sources.get(src, 0) + 1

    return jsonify({
        "total_articles": len(articles),
        "total_trends": len(trends),
        "total_feeds": len(feeds),
        "active_feeds": sum(1 for f in feeds if f.get("enabled")),
        "average_score": round(avg_score, 1),
        "high_impact_count": sum(1 for s in scores if s >= 70),
        "categories": cats,
        "top_sources": dict(sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10]),
    })


@trends_bp.route("/generate-content", methods=["POST"])
@login_required
def generate_content():
    """Generate AI content for a trend."""
    data = request.get_json(silent=True) or {}
    article_id = data.get("article_id", "")
    platform = data.get("platform", "general")

    article = find_item(Config.ARTICLES_FILE, "id", article_id)
    if not article:
        return jsonify({"error": "Article not found"}), 404

    # Get trend data
    trends = read_json(Config.TRENDS_FILE, [])
    trend = None
    for t in trends:
        if t.get("article_id") == article_id:
            trend = t
            break

    from agents.content_agent import generate_content as gen
    content = gen(
        title=article.get("title", ""),
        summary=article.get("summary", ""),
        category=trend.get("category", "") if trend else "",
        platform=platform,
        trend_score=trend.get("trend_score", 50) if trend else 50,
    )

    from agents.hashtag_agent import generate_hashtags
    hashtags = generate_hashtags(
        title=article.get("title", ""),
        category=trend.get("category", "") if trend else "",
        sub_topics=trend.get("sub_topics", []) if trend else [],
        platform=platform,
    )

    return jsonify({
        "content": content,
        "hashtags": hashtags,
        "article_id": article_id,
        "platform": platform,
    })


@trends_bp.route("/generate-image", methods=["POST"])
@login_required
def generate_image_route():
    """Generate an AI image for a trend."""
    data = request.get_json(silent=True) or {}
    article_id = data.get("article_id", "")

    article = find_item(Config.ARTICLES_FILE, "id", article_id)
    if not article:
        return jsonify({"error": "Article not found"}), 404

    from agents.image_agent import generate_trend_image
    result = generate_trend_image(
        title=article.get("title", ""),
        summary=article.get("summary", ""),
    )

    return jsonify(result)


@trends_bp.route("/create-post", methods=["POST"])
@login_required
def create_ai_post():
    """Generate AI content from an article and send it to Telegram."""
    data = request.get_json(silent=True) or {}
    article_id = data.get("article_id", "")
    platform = data.get("platform", "telegram")
    language = data.get("language", "en")

    article = find_item(Config.ARTICLES_FILE, "id", article_id)
    if not article:
        return jsonify({"error": "Article not found"}), 404

    # Get trend data
    trends = read_json(Config.TRENDS_FILE, [])
    trend = None
    for t in trends:
        if t.get("article_id") == article_id:
            trend = t
            break

    # Generate content with AI
    from agents.content_agent import generate_content as gen
    content = gen(
        title=article.get("title", ""),
        summary=article.get("summary", ""),
        category=trend.get("category", "AI") if trend else "AI",
        platform=platform,
        trend_score=trend.get("trend_score", 50) if trend else 50,
        language=language,
    )

    # Generate hashtags
    from agents.hashtag_agent import generate_hashtags
    hashtags = generate_hashtags(
        title=article.get("title", ""),
        category=trend.get("category", "AI") if trend else "AI",
        sub_topics=trend.get("sub_topics", []) if trend else [],
        platform=platform,
    )

    # Build post text
    title_text = content.get("title", article.get("title", ""))
    body_text = content.get("body", article.get("summary", ""))
    cta_text = content.get("cta", "")
    all_tags = " ".join(
        (hashtags.get("universal", []) + hashtags.get("niche", []))[:10]
    )
    link = article.get("link", "")

    # Send to Telegram
    from services.telegram_bot import publish_trend_post
    tg_result = publish_trend_post(
        title=title_text,
        body=body_text,
        hashtags=all_tags,
        link=link,
        cta=cta_text,
    )

    # Log to history
    from data.store import append_item as db_append
    db_append(Config.PUBLISH_HISTORY_FILE, {
        "article_id": article_id,
        "platforms": ["telegram"],
        "results": {"telegram": tg_result},
        "content": {
            "title": title_text,
            "body": body_text[:200],
            "hashtags": all_tags,
        },
    })

    return jsonify({
        "success": tg_result.get("success", False),
        "content": content,
        "hashtags": hashtags,
        "telegram": tg_result,
        "article_id": article_id,
    })


@trends_bp.route("/refresh", methods=["POST"])
@login_required
def refresh_articles():
    """Any logged-in user can trigger a feed refresh."""
    from services.rss_engine import fetch_all_feeds
    result = fetch_all_feeds()
    return jsonify(result)
