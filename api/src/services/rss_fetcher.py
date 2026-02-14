import logging
import feedparser
import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

RSS_SOURCES = {
    "coindesk": {
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml",
        "fetch_interval": 30,
        "timeout": 30,
        "max_retries": 3,
    },
    "cointelegraph": {
        "url": "https://cointelegraph.com/rss",
        "fetch_interval": 30,
        "timeout": 30,
        "max_retries": 3,
    },
    "cryptopotato": {
        "url": "https://cryptopotato.com/feed/",
        "fetch_interval": 30,
        "timeout": 30,
        "max_retries": 3,
    },
    "cryptoslate": {
        "url": "https://cryptoslate.com/feed/",
        "fetch_interval": 30,
        "timeout": 30,
        "max_retries": 3,
    },
    "thedefiant": {
        "url": "https://thedefiant.io/feed/",
        "fetch_interval": 60,
        "timeout": 45,
        "max_retries": 2,
    },
    "bitcoinist": {
        "url": "https://bitcoinist.com/feed/",
        "fetch_interval": 60,
        "timeout": 45,
        "max_retries": 2,
    },
    "newsbtc": {
        "url": "https://www.newsbtc.com/feed/",
        "fetch_interval": 60,
        "timeout": 45,
        "max_retries": 2,
    },
    "cryptonews": {
        "url": "https://cryptonews.com/news/feed/",
        "fetch_interval": 60,
        "timeout": 45,
        "max_retries": 2,
    },
    "smartliquidity": {
        "url": "https://smartliquidity.info/feed/",
        "fetch_interval": 60,
        "timeout": 45,
        "max_retries": 2,
    },
    "benjaminion": {
        "url": "https://benjaminion.xyz/newineth2/rss_feed.xml",
        "fetch_interval": 120,
        "timeout": 45,
        "max_retries": 2,
    },
    "yahoo_finance": {
        "url": "https://finance.yahoo.com/news/rssindex",
        "fetch_interval": 120,
        "timeout": 60,
        "max_retries": 2,
    },
    "cnbc": {
        "url": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
        "fetch_interval": 120,
        "timeout": 60,
        "max_retries": 2,
    },
    "time_nextadvisor": {
        "url": "https://time.com/nextadvisor/feed/",
        "fetch_interval": 180,
        "timeout": 60,
        "max_retries": 2,
    },
}


class RSSFetcher:
    def __init__(self):
        self.timeout = httpx.Timeout(30.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def fetch_feed(self, source: str) -> list[dict]:
        config = RSS_SOURCES[source]
        url = config["url"]
        timeout = config.get("timeout", 30)

        logger.info(f"Fetching RSS feed: {source}")

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

        parsed = feedparser.parse(response.text)
        articles = []

        for entry in parsed.entries:
            try:
                article = {
                    "source": source,
                    "title": entry.get("title", "").strip(),
                    "summary": entry.get(
                        "summary", entry.get("description", "")
                    ).strip(),
                    "link": entry.get("link", "").strip(),
                    "published": self._parse_date(entry),
                }
                if article["title"] and article["link"]:
                    articles.append(article)
            except Exception as e:
                logger.warning(f"Failed to parse entry from {source}: {e}")
                continue

        logger.info(f"Fetched {len(articles)} articles from {source}")
        return articles

    def _parse_date(self, entry) -> Optional[str]:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            from time import mktime

            return str(entry.published_parsed)
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            from time import mktime

            return str(entry.updated_parsed)
        return None

    async def fetch_all(self, sources: list[str]) -> dict[str, list[dict]]:
        results = {}
        for source in sources:
            try:
                articles = await self.fetch_feed(source)
                results[source] = articles
            except Exception as e:
                logger.error(f"Failed to fetch {source}: {e}")
                results[source] = []
        return results
