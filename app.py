"""
AI Trends Intelligence Platform — Flask Application Factory
"""
import os
import logging
from flask import Flask, jsonify, request
from config import Config


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    # ── Load configuration ────────────────────────
    app.config.from_object(Config)
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_EXPIRES"] = Config.JWT_ACCESS_EXPIRES
    app.config["JWT_REFRESH_EXPIRES"] = Config.JWT_REFRESH_EXPIRES
    app.config["TOKENS_FILE"] = Config.TOKENS_FILE

    # ── Ensure directories exist ──────────────────
    for d in [Config.DATA_DIR, Config.AUDIT_LOG_DIR,
              Config.GENERATED_DIR, Config.IMAGES_DIR]:
        os.makedirs(d, exist_ok=True)

    # ── Logging ───────────────────────────────────
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Rate Limiting ─────────────────────────────
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[Config.RATE_LIMIT_DEFAULT],
        storage_uri="memory://",
        app=app,
    )

    # ── Security Headers ──────────────────────────
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'"
        )
        return response

    # ── Register Blueprints ───────────────────────
    from routes.auth_routes import auth_bp
    from routes.trend_routes import trends_bp
    from routes.search_routes import search_bp
    from routes.publish_routes import publish_bp
    from routes.admin_routes import admin_bp
    from routes.page_routes import pages_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(trends_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(publish_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(pages_bp)

    # Serve generated images
    from flask import send_from_directory

    @app.route("/static/generated/images/<filename>")
    def serve_generated_image(filename):
        return send_from_directory(Config.IMAGES_DIR, filename)

    # ── Error Handlers ────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        return app.send_static_file("404.html") if os.path.exists(
            os.path.join(app.static_folder, "404.html")
        ) else (jsonify({"error": "Not found"}), 404)

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({"error": "Rate limit exceeded. Try again later."}), 429

    @app.errorhandler(500)
    def internal_error(e):
        from services.telegram_bot import notify_error
        notify_error("500 Internal Error", str(e))
        return jsonify({"error": "Internal server error"}), 500

    # ── Initialize Services ───────────────────────
    with app.app_context():
        from services.rss_engine import initialize_feeds
        initialize_feeds()

    # ── Start Scheduler ───────────────────────────
    from services.scheduler import init_scheduler
    init_scheduler(app)

    # Create default admin if none exists
    with app.app_context():
        _ensure_admin()

    logging.getLogger(__name__).info(
        "🚀 AI Trends Intelligence Platform initialized"
    )
    return app


def _ensure_admin():
    """Create a default admin user if no admins exist."""
    from data.store import read_json, find_item
    from config import Config

    users = read_json(Config.USERS_FILE, [])
    has_admin = any(u.get("role") == "admin" for u in users)

    if not has_admin:
        from data.store import append_item
        from security.auth import hash_password

        append_item(Config.USERS_FILE, {
            "username": "admin",
            "email": "admin@aitrends.local",
            "password_hash": hash_password("Admin@2024!"),
            "role": "admin",
            "active": True,
            "preferences": {"feeds": [], "platforms": []},
        })
        logging.getLogger(__name__).info(
            "Default admin created (username: admin, password: Admin@2024!)"
        )


# ── Entry Point ───────────────────────────────────

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG,
    )
