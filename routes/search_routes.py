"""
Search routes — Perplexity-style AI-powered search.
"""
from flask import Blueprint, request, jsonify, g
from security.auth import login_required
from agents.search_agent import search_trends
from data.store import read_json, append_item
from config import Config
from security.validation import sanitize_search_query

search_bp = Blueprint("search", __name__, url_prefix="/api/search")


@search_bp.route("", methods=["POST"])
@login_required
def search():
    """Perform AI-powered search across trends."""
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()

    if not query or len(query) < 3:
        return jsonify({"error": "Query must be at least 3 characters"}), 400

    query = sanitize_search_query(query)

    # Check cache
    cache = read_json(Config.SEARCH_CACHE_FILE, [])
    for cached in cache:
        if cached.get("query", "").lower() == query.lower():
            # Return cached if less than 1 hour old
            from dateutil import parser as dp
            from datetime import datetime, timezone, timedelta
            try:
                cached_time = dp.parse(cached.get("cached_at", ""))
                if datetime.now(timezone.utc) - cached_time < timedelta(hours=1):
                    return jsonify({"result": cached["result"], "cached": True})
            except (ValueError, TypeError):
                pass

    # Perform AI search
    result = search_trends(query)

    # Cache result
    append_item(Config.SEARCH_CACHE_FILE, {
        "query": query,
        "result": result,
        "user_id": g.current_user_id,
        "cached_at": result.get("timestamp", ""),
    })

    return jsonify({"result": result, "cached": False})


@search_bp.route("/suggestions", methods=["GET"])
@login_required
def get_suggestions():
    """Get search suggestions based on recent trends."""
    trends = read_json(Config.TRENDS_FILE, [])

    # Extract unique categories and topics
    categories = set()
    topics = set()
    entities = set()

    for t in trends[-50:]:  # Last 50 trends
        if t.get("category"):
            categories.add(t["category"])
        for topic in t.get("sub_topics", []):
            topics.add(topic)
        for entity in t.get("key_entities", []):
            entities.add(entity)

    suggestions = [
        {"type": "category", "text": f"Latest in {cat}"} for cat in list(categories)[:5]
    ] + [
        {"type": "topic", "text": topic} for topic in list(topics)[:10]
    ] + [
        {"type": "entity", "text": f"News about {ent}"} for ent in list(entities)[:5]
    ]

    return jsonify({"suggestions": suggestions})


@search_bp.route("/history", methods=["GET"])
@login_required
def search_history():
    """Get user's search history."""
    cache = read_json(Config.SEARCH_CACHE_FILE, [])
    user_searches = [
        {"query": c.get("query"), "timestamp": c.get("cached_at")}
        for c in cache
        if c.get("user_id") == g.current_user_id
    ]
    return jsonify({"history": user_searches[-20:]})
