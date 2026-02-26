"""
Admin routes — system management, user management, feed management.
"""
from flask import Blueprint, request, jsonify, g
from security.auth import admin_required, login_required
from data.store import (
    read_json, write_json, find_item, update_item,
    delete_item, append_item, generate_id, utcnow, append_audit_log,
)
from security.validation import validate_url, sanitize_html
from config import Config

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ── User Management ───────────────────────────────

@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    users = read_json(Config.USERS_FILE, [])
    # Strip password hashes
    safe = []
    for u in users:
        safe.append({
            "id": u["id"],
            "username": u["username"],
            "email": u.get("email", ""),
            "role": u.get("role", "user"),
            "active": u.get("active", True),
            "created_at": u.get("created_at"),
        })
    return jsonify({"users": safe, "total": len(safe)})


@admin_bp.route("/users/<user_id>", methods=["PUT"])
@admin_required
def update_user(user_id):
    data = request.get_json(silent=True) or {}

    allowed = {"role", "active"}
    updates = {k: v for k, v in data.items() if k in allowed}

    result = update_item(Config.USERS_FILE, user_id, updates)
    if not result:
        return jsonify({"error": "User not found"}), 404

    append_audit_log(Config.AUDIT_LOG_DIR, "admin_update_user",
                     user_id=g.current_user_id,
                     details=f"Updated user {user_id}: {updates}",
                     ip=request.remote_addr)

    return jsonify({"message": "User updated", "user_id": user_id})


@admin_bp.route("/users/<user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    if user_id == g.current_user_id:
        return jsonify({"error": "Cannot delete yourself"}), 400

    if not delete_item(Config.USERS_FILE, user_id):
        return jsonify({"error": "User not found"}), 404

    append_audit_log(Config.AUDIT_LOG_DIR, "admin_delete_user",
                     user_id=g.current_user_id,
                     details=f"Deleted user {user_id}",
                     ip=request.remote_addr)

    return jsonify({"message": "User deleted"})


# ── Feed Management ───────────────────────────────

@admin_bp.route("/feeds", methods=["GET"])
@admin_required
def list_feeds():
    feeds = read_json(Config.FEEDS_FILE, [])
    return jsonify({"feeds": feeds, "total": len(feeds)})


@admin_bp.route("/feeds", methods=["POST"])
@admin_required
def add_feed():
    data = request.get_json(silent=True) or {}
    name = sanitize_html(data.get("name", "").strip())
    url = data.get("url", "").strip()
    category = sanitize_html(data.get("category", "General").strip())

    if not name or len(name) < 2:
        return jsonify({"error": "Feed name required"}), 400
    if not validate_url(url):
        return jsonify({"error": "Invalid feed URL"}), 400

    # Check duplicate
    if find_item(Config.FEEDS_FILE, "url", url):
        return jsonify({"error": "Feed URL already exists"}), 409

    feed = append_item(Config.FEEDS_FILE, {
        "name": name,
        "url": url,
        "category": category,
        "enabled": True,
        "last_fetched": None,
        "article_count": 0,
        "error_count": 0,
        "owner": g.current_user_id,
    })

    return jsonify({"message": "Feed added", "feed": feed}), 201


@admin_bp.route("/feeds/<feed_id>", methods=["PUT"])
@admin_required
def update_feed(feed_id):
    data = request.get_json(silent=True) or {}
    allowed = {"name", "url", "category", "enabled"}
    updates = {k: v for k, v in data.items() if k in allowed}

    result = update_item(Config.FEEDS_FILE, feed_id, updates)
    if not result:
        return jsonify({"error": "Feed not found"}), 404

    return jsonify({"message": "Feed updated", "feed": result})


@admin_bp.route("/feeds/<feed_id>", methods=["DELETE"])
@admin_required
def delete_feed(feed_id):
    if not delete_item(Config.FEEDS_FILE, feed_id):
        return jsonify({"error": "Feed not found"}), 404
    return jsonify({"message": "Feed deleted"})


@admin_bp.route("/feeds/refresh", methods=["POST"])
@admin_required
def refresh_feeds():
    """Manually trigger feed refresh."""
    from services.rss_engine import fetch_all_feeds
    result = fetch_all_feeds()

    append_audit_log(Config.AUDIT_LOG_DIR, "admin_feed_refresh",
                     user_id=g.current_user_id,
                     details=f"Fetched {result['total_new']} new articles",
                     ip=request.remote_addr)

    return jsonify(result)


# ── System Management ─────────────────────────────

@admin_bp.route("/system/stats", methods=["GET"])
@admin_required
def system_stats():
    articles = read_json(Config.ARTICLES_FILE, [])
    trends = read_json(Config.TRENDS_FILE, [])
    feeds = read_json(Config.FEEDS_FILE, [])
    users = read_json(Config.USERS_FILE, [])
    queue = read_json(Config.PUBLISH_QUEUE_FILE, [])
    history = read_json(Config.PUBLISH_HISTORY_FILE, [])

    return jsonify({
        "articles": {"total": len(articles),
                     "analyzed": sum(1 for a in articles if a.get("analyzed"))},
        "trends": {"total": len(trends)},
        "feeds": {"total": len(feeds),
                  "active": sum(1 for f in feeds if f.get("enabled"))},
        "users": {"total": len(users),
                  "admins": sum(1 for u in users if u.get("role") == "admin")},
        "publishing": {
            "queue_pending": sum(1 for q in queue if q.get("status") == "pending"),
            "total_published": len(history),
        },
    })


@admin_bp.route("/system/analyze", methods=["POST"])
@admin_required
def trigger_analysis():
    """Manually trigger trend analysis on unprocessed articles."""
    from services.rss_engine import get_unanalyzed_articles, mark_articles_analyzed
    from agents.trend_agent import batch_analyze

    unanalyzed = get_unanalyzed_articles()
    if not unanalyzed:
        return jsonify({"message": "No articles to analyze", "analyzed": 0})

    existing = read_json(Config.ARTICLES_FILE, [])
    existing_titles = [a.get("title", "") for a in existing if a.get("analyzed")]

    all_trends = read_json(Config.TRENDS_FILE, [])
    results = batch_analyze(unanalyzed[:20], existing_titles)

    for result in results:
        if not result.get("is_duplicate_likely", False):
            all_trends.append(result)

    mark_articles_analyzed([a["id"] for a in unanalyzed[:20]])
    write_json(Config.TRENDS_FILE, all_trends)

    return jsonify({
        "message": f"Analyzed {min(len(unanalyzed), 20)} articles",
        "analyzed": min(len(unanalyzed), 20),
        "new_trends": len(results),
    })


@admin_bp.route("/audit-logs", methods=["GET"])
@admin_required
def get_audit_logs():
    """Get recent audit logs."""
    import os
    import json

    logs = []
    if os.path.isdir(Config.AUDIT_LOG_DIR):
        files = sorted(os.listdir(Config.AUDIT_LOG_DIR), reverse=True)[:7]
        for fname in files:
            fpath = os.path.join(Config.AUDIT_LOG_DIR, fname)
            try:
                with open(fpath, "r") as f:
                    entries = json.load(f)
                    logs.extend(entries)
            except (json.JSONDecodeError, IOError):
                continue

    logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return jsonify({"logs": logs[:100]})
