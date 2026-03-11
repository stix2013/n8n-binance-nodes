-- Migration 003: Celery task results tracking
-- Created: 2026-03-07
-- Description: Table for storing Celery task results from crypto-analysis worker

-- ============================================
-- CELERY TASK RESULTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS celery_task_results (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    task_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING', 'STARTED', 'SUCCESS', 'FAILURE', 'RETRY')),
    symbol VARCHAR(50),
    interval VARCHAR(20),
    result JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_celery_task_results_task_id ON celery_task_results(task_id);
CREATE INDEX IF NOT EXISTS idx_celery_task_results_task_name ON celery_task_results(task_name);
CREATE INDEX IF NOT EXISTS idx_celery_task_results_symbol ON celery_task_results(symbol);
CREATE INDEX IF NOT EXISTS idx_celery_task_results_status ON celery_task_results(status);
CREATE INDEX IF NOT EXISTS idx_celery_task_results_created_at ON celery_task_results(created_at DESC);

-- ============================================
-- MIGRATION METADATA
-- ============================================
INSERT INTO migration_versions (version, description)
VALUES ('003_celery_task_results', 'Add celery_task_results table for tracking crypto-analysis task results')
ON CONFLICT (version) DO UPDATE SET applied_at = NOW();
