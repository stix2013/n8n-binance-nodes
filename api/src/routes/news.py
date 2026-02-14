import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from models.news_models import (
    CoinSummary,
    NewsArticleResponse,
    RefreshResponse,
    SentimentResponse,
    SourceInfo,
    SystemStatusResponse,
)
from services import Database, NewsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/news", tags=["news-sentiment"])


async def get_news_service() -> NewsService:
    from main import news_service

    return news_service


@router.get("/sentiment/{coin_symbol}", response_model=SentimentResponse)
async def get_coin_sentiment(
    coin_symbol: str,
    hours: int = Query(default=24, ge=1, le=168),
    news_service: NewsService = Depends(get_news_service),
):
    """
    Get sentiment analysis for a specific cryptocurrency.
    """
    result = await news_service.get_sentiment_by_coin(coin_symbol, hours)
    if not result["articles"]:
        raise HTTPException(
            status_code=404,
            detail=f"No news found for {coin_symbol.upper()} in the last {hours} hours",
        )
    return result


@router.get("/sentiment", response_model=list[CoinSummary])
async def get_all_sentiment(
    min_articles: int = Query(default=5, ge=1),
    news_service: NewsService = Depends(get_news_service),
):
    """
    Get sentiment summary for all coins with recent news coverage.
    """
    return await news_service.get_all_coins_sentiment(min_articles)


@router.get("/articles", response_model=list[NewsArticleResponse])
async def get_recent_articles(
    coin: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    sentiment: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    hours: int = Query(default=24, ge=1, le=168),
    news_service: NewsService = Depends(get_news_service),
):
    """
    Get recent news articles with optional filtering.
    """
    return await news_service.get_articles(
        coin=coin,
        source=source,
        sentiment_type=sentiment,
        limit=limit,
        hours=hours,
    )


@router.get("/sources", response_model=list[SourceInfo])
async def list_sources(
    news_service: NewsService = Depends(get_news_service),
):
    """
    List all configured news sources with health status.
    """
    from services.rss_fetcher import RSS_SOURCES

    health = news_service.failover.get_source_health()
    sources = []

    for name, config in RSS_SOURCES.items():
        source_info = SourceInfo(
            name=name,
            url=config["url"],
            status=health.get(name, {}).get("status", "unknown"),
            type=health.get(name, {}).get("type", "unknown"),
            failures=health.get(name, {}).get("failures", 0),
        )
        sources.append(source_info)

    return sources


@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status(
    news_service: NewsService = Depends(get_news_service),
):
    """
    Get complete system status including failover state.
    """
    return await news_service.get_system_status()


@router.post("/refresh", response_model=RefreshResponse)
async def trigger_refresh(
    background_tasks: BackgroundTasks,
    news_service: NewsService = Depends(get_news_service),
):
    """
    Manually trigger a news fetch.
    """

    async def fetch_news():
        results = await news_service.fetch_active_sources()
        total_articles = sum(len(articles) for articles in results.values())
        await news_service.refresh_materialized_view()
        return results, total_articles

    results, total = await fetch_news()

    return RefreshResponse(
        message="News refresh completed",
        status="success",
        sources_processed=len(results),
        articles_fetched=total,
    )


@router.post("/refresh/async")
async def trigger_refresh_async(
    background_tasks: BackgroundTasks,
    news_service: NewsService = Depends(get_news_service),
):
    """
    Manually trigger a news fetch (async - returns immediately).
    """

    async def fetch_news():
        results = await news_service.fetch_active_sources()
        await news_service.refresh_materialized_view()

    background_tasks.add_task(fetch_news)

    return RefreshResponse(
        message="News refresh triggered",
        status="processing",
        sources_processed=0,
        articles_fetched=0,
    )
