-- Migration: Create news sentiment tables
-- Version: 001
-- Date: 2026-02-14

-- Core articles table
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR(255) UNIQUE NOT NULL,
    source VARCHAR(100) NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    link VARCHAR(500) NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Sentiment scores table
CREATE TABLE IF NOT EXISTS article_sentiment (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR(255) REFERENCES news_articles(article_id) ON DELETE CASCADE,
    compound_score DECIMAL(5,4) NOT NULL,
    positive_score DECIMAL(5,4) NOT NULL,
    negative_score DECIMAL(5,4) NOT NULL,
    neutral_score DECIMAL(5,4) NOT NULL,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Coin mentions table
CREATE TABLE IF NOT EXISTS article_coins (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR(255) REFERENCES news_articles(article_id) ON DELETE CASCADE,
    coin_symbol VARCHAR(20) NOT NULL,
    confidence DECIMAL(3,2)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_articles_source ON news_articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_published ON news_articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_expires ON news_articles(expires_at);
CREATE INDEX IF NOT EXISTS idx_articles_active ON news_articles(is_active, expires_at);
CREATE INDEX IF NOT EXISTS idx_sentiment_article ON article_sentiment(article_id);
CREATE INDEX IF NOT EXISTS idx_coins_article ON article_coins(article_id);
CREATE INDEX IF NOT EXISTS idx_coins_symbol ON article_coins(coin_symbol);

-- Materialized view for coin sentiment summaries
CREATE MATERIALIZED VIEW IF NOT EXISTS coin_sentiment_summary AS
SELECT 
    ac.coin_symbol,
    COUNT(DISTINCT ac.article_id) AS article_count,
    AVG(ast.compound_score) AS avg_sentiment,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ast.compound_score) AS median_sentiment,
    SUM(CASE WHEN ast.compound_score > 0.05 THEN 1 ELSE 0 END) AS positive_count,
    SUM(CASE WHEN ast.compound_score < -0.05 THEN 1 ELSE 0 END) AS negative_count,
    SUM(CASE WHEN ast.compound_score BETWEEN -0.05 AND 0.05 THEN 1 ELSE 0 END) AS neutral_count,
    MAX(na.published_at) AS latest_article
FROM article_coins ac
JOIN article_sentiment ast ON ac.article_id = ast.article_id
JOIN news_articles na ON ac.article_id = na.article_id
WHERE na.is_active = TRUE AND na.expires_at > NOW()
GROUP BY ac.coin_symbol;

-- Unique index for materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_coin_sentiment_symbol ON coin_sentiment_summary(coin_symbol);

-- Enable pg_trgm extension for fuzzy matching (optional, for deduplication)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
