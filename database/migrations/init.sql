-- Create tables for TOR Unveil
-- This file is automatically executed when postgres container starts

-- Enable extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Timeline Events Table
CREATE TABLE IF NOT EXISTS timeline_events (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER,
    event_type VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    node_fingerprint VARCHAR(100),
    event_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_timeline_analysis ON timeline_events(analysis_id);
CREATE INDEX idx_timeline_timestamp ON timeline_events(timestamp);
CREATE INDEX idx_timeline_event_type ON timeline_events(event_type);

-- Analysis History Table (for iterative learning)
CREATE TABLE IF NOT EXISTS analysis_history (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER NOT NULL,
    entry_node_fingerprint VARCHAR(100),
    exit_node_fingerprint VARCHAR(100) NOT NULL,
    confidence_score FLOAT NOT NULL,
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    feedback_score FLOAT,
    was_correct BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_history_entry_exit ON analysis_history(entry_node_fingerprint, exit_node_fingerprint);
CREATE INDEX idx_history_timestamp ON analysis_history(analysis_timestamp);

-- ML Training Data Table
CREATE TABLE IF NOT EXISTS ml_training_data (
    id SERIAL PRIMARY KEY,
    feature_vector JSONB NOT NULL,
    entry_node_fingerprint VARCHAR(100) NOT NULL,
    exit_node_fingerprint VARCHAR(100) NOT NULL,
    confidence_score FLOAT NOT NULL,
    was_correct BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ml_training_nodes ON ml_training_data(entry_node_fingerprint, exit_node_fingerprint);

-- Node Correlations Table (for temporal tracking)
CREATE TABLE IF NOT EXISTS node_correlations (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER NOT NULL,
    entry_fingerprint VARCHAR(100) NOT NULL,
    exit_fingerprint VARCHAR(100) NOT NULL,
    correlation_score FLOAT NOT NULL,
    time_delta_seconds INTEGER,
    traffic_pattern_similarity FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_correlations_analysis ON node_correlations(analysis_id);
CREATE INDEX idx_correlations_nodes ON node_correlations(entry_fingerprint, exit_fingerprint);
