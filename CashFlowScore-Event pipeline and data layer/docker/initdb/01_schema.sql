-- CashFlowScore TimescaleDB schema
-- Matches PipelineStore (store.py) table names exactly.

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Businesses
CREATE TABLE IF NOT EXISTS businesses (
    business_id TEXT PRIMARY KEY,
    profile_json TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Events — NOTE: TimescaleDB hypertables cannot have a PRIMARY KEY that
-- doesn't include the partitioning column (timestamp).  We use a UNIQUE
-- constraint on (event_id, timestamp) so dedup still works, and add a
-- plain index on event_id alone for fast point-lookups.
CREATE TABLE IF NOT EXISTS events (
    event_id      TEXT        NOT NULL,
    business_id   TEXT        NOT NULL,
    topic         TEXT        NOT NULL,
    event_type    TEXT        NOT NULL,
    amount        DOUBLE PRECISION NOT NULL,
    direction     TEXT        NOT NULL,
    balance_after DOUBLE PRECISION NOT NULL,
    timestamp     TIMESTAMPTZ NOT NULL,
    metadata_json TEXT        NOT NULL DEFAULT '{}',
    UNIQUE (event_id, timestamp)
);

SELECT create_hypertable('events', 'timestamp', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_events_event_id     ON events (event_id);
CREATE INDEX IF NOT EXISTS idx_events_business_time ON events (business_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_topic_time    ON events (topic, timestamp DESC);

-- Stress flags
CREATE TABLE IF NOT EXISTS stress_flags (
    id          SERIAL PRIMARY KEY,
    event_id    TEXT NOT NULL UNIQUE,
    business_id TEXT NOT NULL,
    reason      TEXT NOT NULL,
    amount      DOUBLE PRECISION NOT NULL,
    timestamp   TIMESTAMPTZ NOT NULL
);

-- Pipeline stats KV
CREATE TABLE IF NOT EXISTS pipeline_stats (
    stat_key   TEXT PRIMARY KEY,
    stat_value TEXT NOT NULL
);

-- Activity log
CREATE TABLE IF NOT EXISTS activity_events (
    id          SERIAL PRIMARY KEY,
    category    TEXT NOT NULL,
    message     TEXT NOT NULL,
    business_id TEXT,
    event_id    TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO pipeline_stats (stat_key, stat_value)
VALUES ('schema_version', '"1.0"')
ON CONFLICT (stat_key) DO NOTHING;
