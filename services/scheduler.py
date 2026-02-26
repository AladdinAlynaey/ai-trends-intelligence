"""
Scheduler — manages periodic background tasks.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler = None


def init_scheduler(app):
    """Initialize and start the background scheduler."""
    global _scheduler

    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(daemon=True)

    from config import Config

    # RSS feed refresh
    _scheduler.add_job(
        func=_job_fetch_feeds,
        trigger=IntervalTrigger(minutes=Config.RSS_FETCH_INTERVAL),
        id="fetch_feeds",
        name="Fetch RSS Feeds",
        replace_existing=True,
        kwargs={"app": app},
    )

    # Process publishing queue
    _scheduler.add_job(
        func=_job_process_queue,
        trigger=IntervalTrigger(minutes=15),
        id="process_queue",
        name="Process Publishing Queue",
        replace_existing=True,
        kwargs={"app": app},
    )

    # Analyze new articles
    _scheduler.add_job(
        func=_job_analyze_articles,
        trigger=IntervalTrigger(minutes=Config.RSS_FETCH_INTERVAL + 5),
        id="analyze_articles",
        name="Analyze New Articles",
        replace_existing=True,
        kwargs={"app": app},
    )

    _scheduler.start()
    logger.info("Scheduler started with %d jobs", len(_scheduler.get_jobs()))


def _job_fetch_feeds(app):
    """Background job: fetch all RSS feeds."""
    with app.app_context():
        try:
            from services.rss_engine import fetch_all_feeds
            result = fetch_all_feeds()
            logger.info(
                "Feed fetch complete: %d new articles from %d feeds",
                result["total_new"],
                result["feeds_processed"],
            )
            if result["total_new"] > 0:
                from services.telegram_bot import notify_new_trends
                # Will be triggered after analysis
        except Exception as e:
            logger.error("Feed fetch job failed: %s", e)
            from services.telegram_bot import notify_error
            notify_error("Feed Fetch Error", str(e))


def _job_process_queue(app):
    """Background job: process publishing queue."""
    with app.app_context():
        try:
            from services.publisher import process_queue
            results = process_queue()
            if results:
                logger.info("Processed %d queue items", len(results))
        except Exception as e:
            logger.error("Queue processing job failed: %s", e)


def _job_analyze_articles(app):
    """Background job: analyze unprocessed articles with AI."""
    with app.app_context():
        try:
            from services.rss_engine import get_unanalyzed_articles, mark_articles_analyzed
            from agents.trend_agent import batch_analyze
            from data.store import read_json, write_json
            from config import Config

            unanalyzed = get_unanalyzed_articles()
            if not unanalyzed:
                return

            # Get existing titles for dedup
            existing = read_json(Config.ARTICLES_FILE, [])
            existing_titles = [a.get("title", "") for a in existing if a.get("analyzed")]

            # Analyze in batches
            batch_size = 10
            all_trends = read_json(Config.TRENDS_FILE, [])

            for i in range(0, len(unanalyzed), batch_size):
                batch = unanalyzed[i:i + batch_size]
                results = batch_analyze(batch, existing_titles)

                for result in results:
                    if not result.get("is_duplicate_likely", False):
                        all_trends.append(result)

                # Mark as analyzed
                mark_articles_analyzed([a["id"] for a in batch])

            write_json(Config.TRENDS_FILE, all_trends)

            # Notify about high-scoring trends
            high_scoring = [t for t in all_trends
                            if t.get("trend_score", 0) >= Config.TREND_SCORE_THRESHOLD]
            if high_scoring:
                from services.telegram_bot import notify_new_trends
                notify_new_trends(high_scoring[-5:])

            logger.info("Analyzed %d articles, %d trends stored",
                        len(unanalyzed), len(all_trends))

        except Exception as e:
            logger.error("Article analysis job failed: %s", e)
