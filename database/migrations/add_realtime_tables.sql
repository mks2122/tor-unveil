-- Migration: Add relay_cache and traffic_uploads tables
-- Run this if the tables don't exist yet

-- Relay Cache Table (for Onionoo API responses)
CREATE TABLE IF NOT EXISTS relay_cache (
    id SERIAL PRIMARY KEY,
    fingerprint VARCHAR(100),
    ip_address VARCHAR(50),
    cache_type VARCHAR(50) NOT NULL,
    cache_data JSONB NOT NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_relay_cache_fingerprint ON relay_cache(fingerprint);
CREATE INDEX IF NOT EXISTS idx_relay_cache_ip ON relay_cache(ip_address);
CREATE INDEX IF NOT EXISTS idx_relay_cache_type ON relay_cache(cache_type);
CREATE INDEX IF NOT EXISTS idx_relay_cache_expires ON relay_cache(expires_at);

-- Traffic Uploads Table (for real traffic analysis)
CREATE TABLE IF NOT EXISTS traffic_uploads (
    id SERIAL PRIMARY KEY,
    upload_id VARCHAR(100) UNIQUE NOT NULL,
    filename VARCHAR(255),
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parsed_entry_patterns JSONB,
    parsed_exit_patterns JSONB,
    entry_node_fingerprint VARCHAR(100),
    exit_node_fingerprint VARCHAR(100),
    exit_node_ip VARCHAR(50),
    metadata JSONB,
    status VARCHAR(50) DEFAULT 'uploaded',
    error_message TEXT,
    was_correct BOOLEAN
);

CREATE INDEX IF NOT EXISTS idx_traffic_uploads_id ON traffic_uploads(upload_id);
CREATE INDEX IF NOT EXISTS idx_traffic_uploads_status ON traffic_uploads(status);
CREATE INDEX IF NOT EXISTS idx_traffic_uploads_timestamp ON traffic_uploads(upload_timestamp);

-- Verify tables created
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('relay_cache', 'traffic_uploads');
