import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from .database import Database
from .rss_fetcher import RSSFetcher
from .sentiment_analyzer import SentimentAnalyzer
from .coin_detector import CoinDetector
from .failover_manager import FailoverManager

logger = logging.getLogger(__name__)


class NewsService:
    CACHE_TTL_HOURS = 1

    def __init__(self, db: Database):
        self.db = db
        self.fetcher = RSSFetcher()
        self.analyzer = SentimentAnalyzer()
        self.detector = CoinDetector()
        self.failover = FailoverManager()

    async def fetch_active_sources(self) -> dict:
        active_sources = self.failover.get_active_sources()
        logger.info(f"Fetching from active sources: {active_sources}")

        results = {}
        for source in active_sources:
            try:
                articles = await self.fetcher.fetch_feed(source)
                self.failover.record_success(source)
                results[source] = articles
                await self._process_articles_batch(source, articles)
            except Exception as e:
                logger.error(f"Failed to fetch {source}: {e}")
                self.failover.record_failure(source)
                results[source] = []

        return results

    async def _process_articles_batch(self, source: str, articles: List[dict]) -> None:
        processed = 0
        skipped = 0

        for article in articles:
            try:
                await self._process_article(source, article)
                processed += 1
            except Exception as e:
                logger.warning(f"Failed to process article from {source}: {e}")
                skipped += 1

        logger.info(f"Processed {processed} articles from {source}, skipped {skipped}")

    async def _process_article(self, source: str, article: dict) -> None:
        article_id = self._generate_article_id(article)

        exists = await self._article_exists(article_id)
        if exists:
            return

        sentiment = self.analyzer.analyze_article(
            article.get("title", ""), article.get("summary", "")
        )

        coins = self.detector.detect_coins(
            title=article.get("title", ""),
            summary=article.get("summary", ""),
        )

        await self._store_article(article_id, source, article, sentiment, coins)

    def _generate_article_id(self, article: dict) -> str:
        unique_string = f"{article.get('link', '')}{article.get('title', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    async def _article_exists(self, article_id: str) -> bool:
        query = "SELECT 1 FROM news_articles WHERE article_id = $1 LIMIT 1"
        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, article_id)
            return result is not None

    async def _store_article(
        self,
        article_id: str,
        source: str,
        article: dict,
        sentiment: dict,
        coins: List[dict],
    ) -> None:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=self.CACHE_TTL_HOURS)

        published_at = self._parse_published_date(article.get("published"))

        query_article = """
        INSERT INTO news_articles (article_id, source, title, summary, link, published_at, fetched_at, expires_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (article_id) DO NOTHING
        """
        query_sentiment = """
        INSERT INTO article_sentiment (article_id, compound_score, positive_score, negative_score, neutral_score)
        VALUES ($1, $2, $3, $4, $5)
        """
        query_coins = """
        INSERT INTO article_coins (article_id, coin_symbol, confidence)
        VALUES ($1, $2, $3)
        """

        async with self.db.acquire() as conn:
            await conn.execute(
                query_article,
                article_id,
                source,
                article.get("title", ""),
                article.get("summary", ""),
                article.get("link", ""),
                published_at,
                now,
                expires_at,
            )

            if coins:
                await conn.execute(
                    query_sentiment,
                    article_id,
                    sentiment["compound"],
                    sentiment["positive"],
                    sentiment["negative"],
                    sentiment["neutral"],
                )

                for coin in coins:
                    await conn.execute(
                        query_coins, article_id, coin["symbol"], coin["confidence"]
                    )

    def _parse_published_date(self, published: Optional[str]) -> datetime:
        if not published:
            return datetime.now(timezone.utc)
        try:
            if isinstance(published, str):
                from email.utils import parsedate_to_datetime

                return parsedate_to_datetime(published)
        except Exception:
            pass
        return datetime.now(timezone.utc)

    async def get_sentiment_by_coin(self, coin_symbol: str, hours: int = 24) -> dict:
        query = """
        SELECT 
            na.title,
            na.summary,
            na.link,
            na.source,
            na.published_at,
            ast.compound_score,
            ast.positive_score,
            ast.negative_score,
            ast.neutral_score
        FROM article_coins ac
        JOIN article_sentiment ast ON ac.article_id = ast.article_id
        JOIN news_articles na ON ac.article_id = na.article_id
        WHERE ac.coin_symbol = $1
          AND na.published_at > NOW() - INTERVAL '1 hour' * $2
          AND na.is_active = TRUE
        ORDER BY na.published_at DESC
        LIMIT 100
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, coin_symbol.upper(), hours)

        if not rows:
            return {"coin": coin_symbol.upper(), "articles": [], "summary": None}

        compound_scores = [r["compound_score"] for r in rows]
        avg_sentiment = (
            sum(compound_scores) / len(compound_scores) if compound_scores else 0
        )

        return {
            "coin": coin_symbol.upper(),
            "articles": [dict(r) for r in rows],
            "summary": {
                "average_sentiment": round(avg_sentiment, 4),
                "sentiment_label": self.analyzer.get_sentiment_label(avg_sentiment),
                "article_count": len(rows),
                "positive_ratio": sum(1 for s in compound_scores if s > 0.05)
                / len(rows)
                if compound_scores
                else 0,
                "negative_ratio": sum(1 for s in compound_scores if s < -0.05)
                / len(compound_scores)
                if compound_scores
                else 0,
                "time_range_hours": hours,
            },
        }

    async def get_articles(
        self,
        coin: Optional[str] = None,
        source: Optional[str] = None,
        sentiment_type: Optional[str] = None,
        limit: int = 50,
        hours: int = 24,
    ) -> List[dict]:
        conditions = ["na.is_active = TRUE", "na.expires_at > NOW()"]
        params = []
        param_idx = 1

        if coin:
            conditions.append(f"ac.coin_symbol = ${param_idx}")
            params.append(coin.upper())
            param_idx += 1

        if source:
            conditions.append(f"na.source = ${param_idx}")
            params.append(source)
            param_idx += 1

        if sentiment_type:
            if sentiment_type == "positive":
                conditions.append(f"ast.compound_score > 0.05")
            elif sentiment_type == "negative":
                conditions.append(f"ast.compound_score < -0.05")
            else:
                conditions.append(f"ast.compound_score BETWEEN -0.05 AND 0.05")

        conditions.append(f"na.published_at > NOW() - INTERVAL '1 hour' * ${param_idx}")
        params.append(hours)

        where_clause = " AND ".join(conditions)
        params.append(limit)

        query = f"""
        SELECT 
            na.article_id,
            na.source,
            na.title,
            na.summary,
            na.link,
            na.published_at,
            ast.compound_score,
            ast.positive_score,
            ast.negative_score,
            ast.neutral_score,
            array_agg(ac.coin_symbol) as coins
        FROM news_articles na
        JOIN article_sentiment ast ON na.article_id = ast.article_id
        LEFT JOIN article_coins ac ON na.article_id = ac.article_id
        WHERE {where_clause}
        GROUP BY na.article_id, na.source, na.title, na.summary, na.link, 
                 na.published_at, ast.compound_score, ast.positive_score, 
                 ast.negative_score, ast.neutral_score
        ORDER BY na.published_at DESC
        LIMIT ${param_idx}
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [dict(r) for r in rows]

    async def get_all_coins_sentiment(self, min_articles: int = 5) -> List[dict]:
        query = """
        SELECT 
            coin_symbol,
            article_count,
            avg_sentiment,
            latest_article
        FROM coin_sentiment_summary
        WHERE article_count >= $1
        ORDER BY article_count DESC
        LIMIT 50
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, min_articles)

        results = []
        for r in rows:
            results.append(
                {
                    "coin_symbol": r["coin_symbol"],
                    "article_count": r["article_count"],
                    "average_sentiment": round(float(r["avg_sentiment"]), 4),
                    "sentiment_label": self.analyzer.get_sentiment_label(
                        float(r["avg_sentiment"])
                    ),
                    "latest_article": r["latest_article"],
                }
            )

        return results

    async def get_system_status(self) -> dict:
        return {
            "failover": self.failover.get_status(),
            "cache_stats": await self._get_cache_stats(),
        }

    async def _get_cache_stats(self) -> dict:
        query = """
        SELECT 
            COUNT(*) as total_articles,
            COUNT(DISTINCT source) as sources,
            COUNT(DISTINCT coin_symbol) as coins,
            MAX(published_at) as latest_article,
            MIN(expires_at) as next_expiry
        FROM news_articles
        WHERE is_active = TRUE AND expires_at > NOW()
        """

        async with self.db.acquire() as conn:
            stats = await conn.fetchrow(query)

        return {
            "total_articles": stats["total_articles"],
            "active_sources": stats["sources"],
            "unique_coins": stats["coins"],
            "latest_article": stats["latest_article"],
            "next_expiry": stats["next_expiry"],
        }

    async def refresh_materialized_view(self) -> None:
        query = "REFRESH MATERIALIZED VIEW CONCURRENTLY coin_sentiment_summary"
        async with self.db.acquire() as conn:
            await conn.execute(query)
