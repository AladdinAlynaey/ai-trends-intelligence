"""
RSS Feed Engine — fetches, parses, deduplicates, and stores AI-related articles.
Uses requests with explicit timeouts to avoid hanging on slow feeds.
Covers AI, ML, Cybersecurity, Developer Tools, Robotics, and more.
"""
import hashlib
import logging
import re
import time
from datetime import datetime, timezone
from dateutil import parser as dateutil_parser
from io import BytesIO

import requests
import feedparser

from config import Config
from data.store import (
    read_json, write_json, append_item, find_item, generate_id, utcnow
)

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; AITrendsPlatform/1.0; +https://localhost)"

# ── 50+ RSS Feeds: AI, ML, Cybersecurity, Tools, Research ──

DEFAULT_FEEDS = [
    # ── Core AI & ML Labs ──────────────────────────────
    {"name": "MIT Technology Review – AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed", "category": "Research"},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "category": "Industry"},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/", "category": "Research"},
    {"name": "DeepMind Blog", "url": "https://deepmind.google/blog/rss.xml", "category": "Research"},
    {"name": "Anthropic Blog", "url": "https://www.anthropic.com/blog/rss.xml", "category": "Research"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml", "category": "Open Source"},
    {"name": "Papers With Code", "url": "https://paperswithcode.com/latest.rss", "category": "Research"},
    {"name": "The Batch (Andrew Ng)", "url": "https://www.deeplearning.ai/the-batch/feed/", "category": "Research"},
    {"name": "Microsoft AI Blog", "url": "https://blogs.microsoft.com/ai/feed/", "category": "Industry"},
    {"name": "AWS Machine Learning", "url": "https://aws.amazon.com/blogs/machine-learning/feed/", "category": "Industry"},
    {"name": "NVIDIA AI Blog", "url": "https://blogs.nvidia.com/feed/", "category": "Industry"},
    {"name": "Meta AI Blog", "url": "https://ai.meta.com/blog/rss/", "category": "Research"},
    {"name": "Stability AI Blog", "url": "https://stability.ai/blog/rss.xml", "category": "Research"},
    {"name": "Cohere Blog", "url": "https://cohere.com/blog/rss.xml", "category": "Industry"},
    {"name": "Mistral AI Blog", "url": "https://mistral.ai/news/rss.xml", "category": "Research"},
    {"name": "AI21 Labs Blog", "url": "https://www.ai21.com/blog/rss.xml", "category": "Research"},
    {"name": "Together AI Blog", "url": "https://www.together.ai/blog/rss.xml", "category": "Industry"},
    {"name": "Apple ML Research", "url": "https://machinelearning.apple.com/rss.xml", "category": "Research"},
    {"name": "Salesforce AI Research", "url": "https://blog.salesforceairesearch.com/rss/", "category": "Research"},
    {"name": "Allen AI (AI2)", "url": "https://blog.allenai.org/feed", "category": "Research"},

    # ── AI Industry News ────────────────────────────
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "category": "Industry"},
    {"name": "TechCrunch – AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "category": "Industry"},
    {"name": "The Verge – AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "category": "Industry"},
    {"name": "Wired – AI", "url": "https://www.wired.com/feed/tag/ai/latest/rss", "category": "Industry"},
    {"name": "ZDNet – AI", "url": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml", "category": "Industry"},
    {"name": "AI News", "url": "https://www.artificialintelligence-news.com/feed/", "category": "Industry"},
    {"name": "Unite.AI", "url": "https://www.unite.ai/feed/", "category": "Industry"},
    {"name": "SiliconAngle – AI", "url": "https://siliconangle.com/category/ai/feed/", "category": "Industry"},
    {"name": "AI Business", "url": "https://aibusiness.com/rss.xml", "category": "Industry"},
    {"name": "Forbes – AI", "url": "https://www.forbes.com/ai/feed/", "category": "Industry"},
    {"name": "The Register – AI", "url": "https://www.theregister.com/software/ai_ml/headlines.atom", "category": "Industry"},
    {"name": "CIO – AI", "url": "https://www.cio.com/category/artificial-intelligence/feed/", "category": "Industry"},
    {"name": "TechRadar – AI", "url": "https://www.techradar.com/rss/news/computing/artificial-intelligence", "category": "Industry"},
    {"name": "Ars Technica – AI", "url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "category": "Industry"},

    # ── Research & Academic ─────────────────────────
    {"name": "Towards Data Science", "url": "https://towardsdatascience.com/feed", "category": "Research"},
    {"name": "Synced Review", "url": "https://syncedreview.com/feed/", "category": "Research"},
    {"name": "Import AI Newsletter", "url": "https://importai.substack.com/feed", "category": "Research"},
    {"name": "Singularity Hub", "url": "https://singularityhub.com/feed/", "category": "Research"},
    {"name": "Machine Learning Mastery", "url": "https://machinelearningmastery.com/feed/", "category": "Research"},
    {"name": "KDnuggets", "url": "https://www.kdnuggets.com/feed", "category": "Research"},
    {"name": "InfoQ – AI/ML", "url": "https://feed.infoq.com/ai-ml-data-eng/", "category": "Research"},
    {"name": "Analytics India Magazine", "url": "https://analyticsindiamag.com/feed/", "category": "Research"},
    {"name": "Last Week in AI", "url": "https://lastweekin.ai/feed", "category": "Research"},
    {"name": "arXiv – CS.AI", "url": "https://rss.arxiv.org/rss/cs.AI", "category": "Research"},
    {"name": "arXiv – CS.LG", "url": "https://rss.arxiv.org/rss/cs.LG", "category": "Research"},
    {"name": "arXiv – CS.CL (NLP)", "url": "https://rss.arxiv.org/rss/cs.CL", "category": "Research"},
    {"name": "arXiv – CS.CV (Vision)", "url": "https://rss.arxiv.org/rss/cs.CV", "category": "Research"},
    {"name": "Distill.pub", "url": "https://distill.pub/rss.xml", "category": "Research"},
    {"name": "Sebastian Raschka Blog", "url": "https://magazine.sebastianraschka.com/feed", "category": "Research"},

    # ── AI Newsletters & Curated ─────────────────────
    {"name": "The Neuron", "url": "https://www.theneurondaily.com/feed", "category": "Newsletter"},
    {"name": "Ben's Bites", "url": "https://bensbites.beehiiv.com/feed", "category": "Newsletter"},
    {"name": "Superhuman AI", "url": "https://www.superhuman.ai/feed", "category": "Newsletter"},
    {"name": "AI Tool Report", "url": "https://aitoolreport.beehiiv.com/feed", "category": "Newsletter"},
    {"name": "TLDR AI", "url": "https://tldr.tech/ai/rss", "category": "Newsletter"},
    {"name": "The Rundown AI", "url": "https://www.therundown.ai/feed", "category": "Newsletter"},
    {"name": "Latent Space Podcast", "url": "https://www.latent.space/feed", "category": "Newsletter"},

    # ── AI Security (AI-related only) ──────────────────
    {"name": "The Hacker News", "url": "https://feeds.feedburner.com/TheHackersNews", "category": "AI Security"},
    {"name": "Dark Reading – AI", "url": "https://www.darkreading.com/rss.xml", "category": "AI Security"},

    # ── AI Developer Tools & Open Source ───────────────
    {"name": "GitHub Blog", "url": "https://github.blog/feed/", "category": "Tools"},
    {"name": "Dev.to – AI", "url": "https://dev.to/feed/tag/ai", "category": "Tools"},
    {"name": "Hacker News – AI", "url": "https://hnrss.org/best?q=AI+OR+LLM+OR+GPT", "category": "Tools"},
    {"name": "Product Hunt – AI", "url": "https://www.producthunt.com/feed?category=artificial-intelligence", "category": "Tools"},
    {"name": "Dev.to – Machine Learning", "url": "https://dev.to/feed/tag/machinelearning", "category": "Tools"},
    {"name": "Dev.to – LLM", "url": "https://dev.to/feed/tag/llm", "category": "Tools"},
    {"name": "Ollama Blog", "url": "https://ollama.com/blog/feed.xml", "category": "Open Source"},
    {"name": "LangChain Blog", "url": "https://blog.langchain.dev/rss/", "category": "Tools"},
    {"name": "LlamaIndex Blog", "url": "https://www.llamaindex.ai/blog/rss.xml", "category": "Tools"},

    # ── AI Ethics, Policy, Regulation ───────────────
    {"name": "AI Ethics Brief", "url": "https://brief.montrealethics.ai/feed", "category": "Ethics"},
    {"name": "Future of Life Institute", "url": "https://futureoflife.org/feed/", "category": "Ethics"},
    {"name": "OECD AI Policy", "url": "https://oecd.ai/en/feed", "category": "Ethics"},
    {"name": "Brookings – AI Policy", "url": "https://www.brookings.edu/topic/artificial-intelligence/feed/", "category": "Ethics"},

    # ── AI Robotics ─────────────────────────────────
    {"name": "IEEE Spectrum – Robotics", "url": "https://spectrum.ieee.org/feeds/topic/robotics.rss", "category": "AI Robotics"},
    {"name": "TechCrunch – Robotics", "url": "https://techcrunch.com/category/robotics/feed/", "category": "AI Robotics"},
    {"name": "The Robot Report", "url": "https://www.therobotreport.com/feed/", "category": "AI Robotics"},

    # ── AI in Verticals ──────────────────────────────
    {"name": "AI in Healthcare – Nature", "url": "https://www.nature.com/natmachintell.rss", "category": "AI Healthcare"},
    {"name": "Healthcare IT News – AI", "url": "https://www.healthcareitnews.com/topic/artificial-intelligence/feed", "category": "AI Healthcare"},

    # ── Cloud & Enterprise AI ────────────────────────
    {"name": "Google Cloud AI Blog", "url": "https://cloud.google.com/blog/products/ai-machine-learning/rss", "category": "Industry"},
    {"name": "Azure AI Blog", "url": "https://techcommunity.microsoft.com/plugins/custom/microsoft/o365/custom-blog-rss?board=Azure-AI-Services-blog", "category": "Industry"},
    {"name": "IBM AI Blog", "url": "https://www.ibm.com/blog/category/artificial-intelligence/feed/", "category": "Industry"},
    {"name": "Oracle AI Blog", "url": "https://blogs.oracle.com/ai-and-datascience/rss", "category": "Industry"},

    # ── AI Creative (Image, Video, Audio) ────────────
    {"name": "Runway ML Blog", "url": "https://runwayml.com/blog/rss.xml", "category": "AI Creative"},
    {"name": "ElevenLabs Blog", "url": "https://elevenlabs.io/blog/rss.xml", "category": "AI Creative"},
    {"name": "Midjourney Blog", "url": "https://www.midjourney.com/blog/rss.xml", "category": "AI Creative"},

    # ── AI Funding & Startups ────────────────────────
    {"name": "AI Fund Blog", "url": "https://aifund.ai/blog/feed/", "category": "AI Funding"},
    {"name": "CB Insights – AI", "url": "https://www.cbinsights.com/research/artificial-intelligence/feed/", "category": "AI Funding"},
    {"name": "Y Combinator Blog", "url": "https://www.ycombinator.com/blog/rss/", "category": "AI Funding"},
]


def initialize_feeds() -> None:
    """Seed the feeds JSON if it doesn't exist."""
    feeds = read_json(Config.FEEDS_FILE, [])
    if feeds:
        # Add any new feeds that don't exist yet
        existing_urls = {f.get("url") for f in feeds}
        added = 0
        for feed_data in DEFAULT_FEEDS:
            if feed_data["url"] not in existing_urls:
                feed_data["id"] = generate_id()
                feed_data["enabled"] = True
                feed_data["last_fetched"] = None
                feed_data["created_at"] = utcnow()
                feed_data["article_count"] = 0
                feed_data["error_count"] = 0
                feed_data["owner"] = "system"
                feeds.append(feed_data)
                added += 1
        if added:
            write_json(Config.FEEDS_FILE, feeds)
            logger.info("Added %d new RSS feeds (total: %d)", added, len(feeds))
        return

    for feed_data in DEFAULT_FEEDS:
        feed_data["id"] = generate_id()
        feed_data["enabled"] = True
        feed_data["last_fetched"] = None
        feed_data["created_at"] = utcnow()
        feed_data["article_count"] = 0
        feed_data["error_count"] = 0
        feed_data["owner"] = "system"
        feeds.append(feed_data)
    write_json(Config.FEEDS_FILE, feeds)
    logger.info("Initialized %d default RSS feeds", len(feeds))


def _article_hash(title: str, link: str) -> str:
    """Create a deduplication hash."""
    raw = f"{title.strip().lower()}|{link.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _parse_date(entry) -> str:
    """Extract and parse a date from a feedparser entry."""
    for field in ("published", "updated", "created"):
        raw = entry.get(field)
        if raw:
            try:
                dt = dateutil_parser.parse(raw)
                return dt.astimezone(timezone.utc).isoformat()
            except (ValueError, TypeError):
                continue
    return utcnow()


def _clean_html(text: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:1000]


def _download_feed(url: str, timeout: int = 12) -> feedparser.FeedParserDict:
    """Download feed content using requests with timeout, then parse with feedparser."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            allow_redirects=True,
        )
        resp.raise_for_status()
        return feedparser.parse(resp.content)
    except requests.exceptions.Timeout:
        logger.debug("Timeout fetching feed: %s", url)
        return feedparser.FeedParserDict(entries=[], bozo=True)
    except requests.exceptions.RequestException as e:
        logger.debug("Failed to download feed %s: %s", url, str(e)[:100])
        return feedparser.FeedParserDict(entries=[], bozo=True)


def fetch_feed(feed: dict) -> list[dict]:
    """Fetch and parse a single RSS feed. Returns list of new articles."""
    url = feed.get("url", "")
    if not url:
        return []

    parsed = _download_feed(url)
    if not parsed.entries:
        return []

    existing = read_json(Config.ARTICLES_FILE, [])
    existing_hashes = {a.get("hash") for a in existing}

    new_articles = []
    for entry in parsed.entries[:Config.RSS_MAX_ARTICLES]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        if not title or not link:
            continue

        h = _article_hash(title, link)
        if h in existing_hashes:
            continue

        summary = ""
        if entry.get("summary"):
            summary = entry.summary
        elif entry.get("description"):
            summary = entry.description

        summary = _clean_html(summary)

        # Extract image
        image_url = ""
        if entry.get("media_thumbnail"):
            image_url = entry["media_thumbnail"][0].get("url", "")
        elif entry.get("media_content"):
            for mc in entry["media_content"]:
                if mc.get("url") and "image" in mc.get("type", "image"):
                    image_url = mc["url"]
                    break

        article = {
            "id": generate_id(),
            "hash": h,
            "title": title,
            "link": link,
            "summary": summary,
            "source": feed.get("name", "Unknown"),
            "feed_id": feed.get("id", ""),
            "category": feed.get("category", "General"),
            "published_at": _parse_date(entry),
            "fetched_at": utcnow(),
            "trend_score": None,
            "analyzed": False,
            "image_url": image_url,
        }
        new_articles.append(article)
        existing_hashes.add(h)

    return new_articles


def fetch_all_feeds() -> dict:
    """Fetch all enabled feeds CONCURRENTLY and store new articles."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    feeds = read_json(Config.FEEDS_FILE, [])
    all_articles = read_json(Config.ARTICLES_FILE, [])
    existing_hashes = {a.get("hash") for a in all_articles}

    enabled_feeds = [f for f in feeds if f.get("enabled", True)]
    total_new = 0
    feeds_ok = 0
    feed_results = []
    new_articles_all = []

    def _fetch_one(feed):
        """Fetch a single feed (runs in thread)."""
        try:
            arts = fetch_feed(feed)
            # Filter already-existing
            fresh = [a for a in arts if a.get("hash") not in existing_hashes]
            return feed, fresh, None
        except Exception as e:
            return feed, [], str(e)

    # Concurrent fetch with 8 workers
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(_fetch_one, f): f for f in enabled_feeds}
        for future in as_completed(futures, timeout=90):
            try:
                feed, new_articles, error = future.result(timeout=30)
                if error:
                    logger.warning("Feed error %s: %s", feed.get("name", "?"), error)
                    feed["error_count"] = feed.get("error_count", 0) + 1
                else:
                    if new_articles:
                        new_articles_all.extend(new_articles)
                        for a in new_articles:
                            existing_hashes.add(a.get("hash"))
                    feeds_ok += 1
                    feed["error_count"] = 0

                feed["last_fetched"] = utcnow()
                feed["article_count"] = feed.get("article_count", 0) + len(new_articles)
                feed_results.append({
                    "name": feed.get("name"),
                    "new_articles": len(new_articles),
                    "error": error,
                })
            except Exception as e:
                logger.warning("Feed future error: %s", e)

    total_new = len(new_articles_all)

    # Persist
    if total_new > 0:
        all_articles.extend(new_articles_all)
        write_json(Config.ARTICLES_FILE, all_articles)
        logger.info("Saved %d new articles from %d/%d feeds",
                     total_new, feeds_ok, len(enabled_feeds))

    write_json(Config.FEEDS_FILE, feeds)

    # Telegram notification
    if total_new > 0:
        try:
            from services.telegram_bot import _send_message
            _send_message(
                f"📰 <b>New Articles Alert</b>\n\n"
                f"📥 Fetched <b>{total_new}</b> new articles from {feeds_ok}/{len(enabled_feeds)} feeds\n"
                f"📊 Total articles: {len(all_articles)}"
            )
        except Exception:
            pass

    return {
        "total_new": total_new,
        "feeds_processed": len(enabled_feeds),
        "feeds_ok": feeds_ok,
        "details": [r for r in feed_results if r.get("new_articles", 0) > 0 or r.get("error")],
        "timestamp": utcnow(),
    }


def get_unanalyzed_articles() -> list[dict]:
    """Return articles that haven't been analyzed yet."""
    articles = read_json(Config.ARTICLES_FILE, [])
    return [a for a in articles if not a.get("analyzed", False)]


def mark_articles_analyzed(article_ids: list[str]) -> None:
    """Mark articles as analyzed."""
    articles = read_json(Config.ARTICLES_FILE, [])
    ids_set = set(article_ids)
    for art in articles:
        if art.get("id") in ids_set:
            art["analyzed"] = True
    write_json(Config.ARTICLES_FILE, articles)
