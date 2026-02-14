import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class NewsScheduler:
    def __init__(self, news_service):
        self.news_service = news_service
        self.scheduler = AsyncIOScheduler()

    def start(self):
        self.scheduler.add_job(
            self.news_service.fetch_active_sources,
            trigger=IntervalTrigger(minutes=30),
            id="fetch_news",
            replace_existing=True,
            name="Fetch news from RSS feeds",
        )

        self.scheduler.add_job(
            self.news_service.refresh_materialized_view,
            trigger=IntervalTrigger(minutes=15),
            id="refresh_view",
            replace_existing=True,
            name="Refresh sentiment materialized view",
        )

        self.scheduler.start()
        logger.info("News scheduler started - fetching every 30 minutes")

    def shutdown(self):
        self.scheduler.shutdown()
        logger.info("News scheduler stopped")

    def get_next_fetch_time(self):
        job = self.scheduler.get_job("fetch_news")
        if job:
            return job.next_run_time.isoformat()
        return None
