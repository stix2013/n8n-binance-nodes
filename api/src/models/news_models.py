from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SentimentScores(BaseModel):
    compound: float = Field(..., ge=-1, le=1)
    positive: float = Field(..., ge=0, le=1)
    negative: float = Field(..., ge=0, le=1)
    neutral: float = Field(..., ge=0, le=1)


class SentimentSummary(BaseModel):
    average_sentiment: float
    sentiment_label: str
    article_count: int
    positive_ratio: float
    negative_ratio: float
    time_range_hours: int


class ArticleSentiment(BaseModel):
    title: str
    summary: str
    link: str
    source: str
    published_at: datetime
    compound_score: float
    positive_score: float
    negative_score: float
    neutral_score: float


class SentimentResponse(BaseModel):
    coin: str
    articles: List[ArticleSentiment]
    summary: Optional[SentimentSummary]


class CoinSummary(BaseModel):
    coin_symbol: str
    article_count: int
    average_sentiment: float
    sentiment_label: str
    latest_article: datetime


class NewsArticleResponse(BaseModel):
    article_id: str
    source: str
    title: str
    summary: str
    link: str
    published_at: datetime
    compound_score: float
    positive_score: float
    negative_score: float
    neutral_score: float
    coins: List[str]


class SourceInfo(BaseModel):
    name: str
    url: str
    status: str
    type: str
    failures: int = 0


class FailoverStatus(BaseModel):
    active_count: int
    active_sources: List[str]
    primaries_active: int
    backups_active: int
    failed_primaries: List[str]
    backups_available: int
    backup_queue: List[str]
    failure_counts: dict


class CacheStats(BaseModel):
    total_articles: int
    active_sources: int
    unique_coins: int
    latest_article: Optional[datetime]
    next_expiry: Optional[datetime]


class SystemStatusResponse(BaseModel):
    failover: FailoverStatus
    cache_stats: CacheStats


class RefreshResponse(BaseModel):
    message: str
    status: str
    sources_processed: int
    articles_fetched: int
