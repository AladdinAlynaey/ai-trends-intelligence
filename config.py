"""
Application configuration loaded from environment variables.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    # ── Flask ──────────────────────────────────────
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", os.urandom(64).hex())
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    PORT = int(os.getenv("FLASK_PORT", 5000))

    # ── JWT ────────────────────────────────────────
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.urandom(64).hex())
    JWT_ACCESS_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    )
    JWT_REFRESH_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 604800))
    )

    # ── OpenRouter ─────────────────────────────────
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )
    OPENROUTER_LLM_MODEL = os.getenv(
        "OPENROUTER_LLM_MODEL", "google/gemini-2.0-flash-001"
    )
    OPENROUTER_IMAGE_MODEL = os.getenv(
        "OPENROUTER_IMAGE_MODEL", "black-forest-labs/flux-1.1-pro"
    )

    # ── Telegram ───────────────────────────────────
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
    TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"

    # ── Publishing ─────────────────────────────────
    PUBLISH_TWITTER_ENABLED = (
        os.getenv("PUBLISH_TWITTER_ENABLED", "false").lower() == "true"
    )
    TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
    TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
    TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
    TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "")

    PUBLISH_LINKEDIN_ENABLED = (
        os.getenv("PUBLISH_LINKEDIN_ENABLED", "false").lower() == "true"
    )
    LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")

    PUBLISH_REDDIT_ENABLED = (
        os.getenv("PUBLISH_REDDIT_ENABLED", "false").lower() == "true"
    )
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "")
    REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "")

    # ── RSS ─────────────────────────────────────────
    RSS_FETCH_INTERVAL = int(os.getenv("RSS_FETCH_INTERVAL_MINUTES", 30))
    RSS_MAX_ARTICLES = int(os.getenv("RSS_MAX_ARTICLES_PER_FEED", 50))
    TREND_SCORE_THRESHOLD = int(os.getenv("TREND_SCORE_THRESHOLD", 40))

    # ── Rate Limiting ──────────────────────────────
    RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "100/hour")
    RATE_LIMIT_AUTH = os.getenv("RATE_LIMIT_AUTH", "20/minute")

    # ── Security ───────────────────────────────────
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5000").split(",")

    # ── Data Paths ─────────────────────────────────
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATA_DIR = os.path.join(BASE_DIR, os.getenv("DATA_DIR", "data"))
    AUDIT_LOG_DIR = os.path.join(BASE_DIR, os.getenv("AUDIT_LOG_DIR", "data/audit"))

    # Data file paths
    USERS_FILE = os.path.join(DATA_DIR, "users.json")
    ARTICLES_FILE = os.path.join(DATA_DIR, "articles.json")
    TRENDS_FILE = os.path.join(DATA_DIR, "trends.json")
    FEEDS_FILE = os.path.join(DATA_DIR, "feeds.json")
    PUBLISH_QUEUE_FILE = os.path.join(DATA_DIR, "publish_queue.json")
    PUBLISH_HISTORY_FILE = os.path.join(DATA_DIR, "publish_history.json")
    SEARCH_CACHE_FILE = os.path.join(DATA_DIR, "search_cache.json")
    TOKENS_FILE = os.path.join(DATA_DIR, "tokens.json")
    GENERATED_DIR = os.path.join(DATA_DIR, "generated")
    IMAGES_DIR = os.path.join(DATA_DIR, "generated", "images")
