-- Initialize TimescaleDB Extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create tables for Digital Twin System
CREATE TABLE IF NOT EXISTS metrics (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    aggregation_type VARCHAR(50),
    sample_count INTEGER,
    total_power DOUBLE PRECISION,
    total_power_max DOUBLE PRECISION,
    total_power_min DOUBLE PRECISION,
    efficiency DOUBLE PRECISION,
    power_factor DOUBLE PRECISION,
    frequency DOUBLE PRECISION,
    total_load DOUBLE PRECISION,
    generation DOUBLE PRECISION,
    losses DOUBLE PRECISION,
    voltage_stability DOUBLE PRECISION,
    data JSONB
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('metrics', 'timestamp', if_not_exists => TRUE);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp_desc ON metrics (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_aggregation_type ON metrics (aggregation_type);

-- Asset states table
CREATE TABLE IF NOT EXISTS asset_states (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    asset_id VARCHAR(100),
    asset_type VARCHAR(100),
    status VARCHAR(50),
    health_score DOUBLE PRECISION,
    voltage DOUBLE PRECISION,
    current DOUBLE PRECISION,
    power DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    oil_level DOUBLE PRECISION,
    data JSONB
);

-- Convert to hypertable
SELECT create_hypertable('asset_states', 'timestamp', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_asset_states_timestamp_desc ON asset_states (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_asset_states_asset_id ON asset_states (asset_id, timestamp DESC);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    alert_type VARCHAR(100),
    severity VARCHAR(50),
    asset_id VARCHAR(100),
    message TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    data JSONB
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp_desc ON alerts (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts (severity, resolved);
CREATE INDEX IF NOT EXISTS idx_alerts_asset_id ON alerts (asset_id);

-- AI Analysis table
CREATE TABLE IF NOT EXISTS ai_analysis (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    analysis_type VARCHAR(100),
    asset_id VARCHAR(100),
    anomaly_score DOUBLE PRECISION,
    failure_probability DOUBLE PRECISION,
    prediction TEXT,
    recommendation TEXT,
    confidence_score DOUBLE PRECISION,
    data JSONB
);

-- Convert to hypertable
SELECT create_hypertable('ai_analysis', 'timestamp', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ai_analysis_timestamp_desc ON ai_analysis (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_type ON ai_analysis (analysis_type);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_asset_id ON ai_analysis (asset_id);

-- Create continuous aggregates for hourly metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS hour,
    AVG(total_power) as avg_power,
    MAX(total_power) as max_power,
    MIN(total_power) as min_power,
    AVG(efficiency) as avg_efficiency,
    AVG(power_factor) as avg_power_factor,
    AVG(frequency) as avg_frequency,
    COUNT(*) as sample_count
FROM metrics
GROUP BY hour
WITH NO DATA;

-- Create continuous aggregates for daily metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    AVG(total_power) as avg_power,
    MAX(total_power) as max_power,
    MIN(total_power) as min_power,
    AVG(efficiency) as avg_efficiency,
    AVG(power_factor) as avg_power_factor,
    SUM(generation) as total_generation,
    SUM(losses) as total_losses,
    COUNT(*) as sample_count
FROM metrics
GROUP BY day
WITH NO DATA;

-- Set up data retention policies
SELECT add_retention_policy('metrics', INTERVAL '30 days', if_not_exists => TRUE);
SELECT add_retention_policy('asset_states', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_retention_policy('ai_analysis', INTERVAL '14 days', if_not_exists => TRUE);

-- Create functions for data analysis
CREATE OR REPLACE FUNCTION get_asset_health_trend(
    p_asset_id VARCHAR,
    p_hours INTEGER DEFAULT 24
)
RETURNS TABLE (
    hour TIMESTAMPTZ,
    avg_health DOUBLE PRECISION,
    min_health DOUBLE PRECISION,
    max_health DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        time_bucket('1 hour', timestamp) AS hour,
        AVG(health_score) as avg_health,
        MIN(health_score) as min_health,
        MAX(health_score) as max_health
    FROM asset_states
    WHERE asset_id = p_asset_id
        AND timestamp > NOW() - INTERVAL '1 hour' * p_hours
    GROUP BY hour
    ORDER BY hour DESC;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO digitaltwin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO digitaltwin;