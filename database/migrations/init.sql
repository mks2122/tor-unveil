-- Create tables for TOR Unveil
-- This file is automatically executed when postgres container starts

-- Enable extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- USER AUTHENTICATION TABLES (Clerk-based)
-- ============================================================

-- Users Table (Clerk integration)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,

    -- Clerk user ID (from Clerk authentication)
    clerk_id VARCHAR(255) UNIQUE NOT NULL,

    -- User identification
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),

    -- User role/type: 'public', 'police', 'admin'
    -- Automatically assigned based on email domain:
    --   - stjosephs.ac.in or tn.gov.in → 'police'
    --   - all others → 'public'
    user_type VARCHAR(20) NOT NULL DEFAULT 'public' CHECK (user_type IN ('public', 'police', 'admin')),

    -- Status flags
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT TRUE,  -- Clerk handles verification
    email_verified BOOLEAN NOT NULL DEFAULT TRUE,

    -- Metadata
    profile_data TEXT,  -- JSON data
    last_login TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for users table
CREATE INDEX idx_users_clerk_id ON users(clerk_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_type ON users(user_type);
CREATE INDEX idx_users_active ON users(is_active);

COMMENT ON TABLE users IS 'Core user information table - integrated with Clerk authentication';
COMMENT ON COLUMN users.clerk_id IS 'Clerk user ID from Clerk authentication service';
COMMENT ON COLUMN users.user_type IS 'User role: public (general users), police (stjosephs.ac.in or tn.gov.in), admin (system administrators)';


-- User Sessions Table (for additional session tracking)
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    clerk_session_id VARCHAR(512),

    -- Session metadata
    ip_address VARCHAR(45),  -- IPv6 support
    user_agent VARCHAR(512),
    device_info TEXT,  -- JSON data

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for user_sessions table
CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_clerk_session ON user_sessions(clerk_session_id);
CREATE INDEX idx_sessions_active ON user_sessions(is_active);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);

COMMENT ON TABLE user_sessions IS 'User sessions tracking - supplementary to Clerk session management';


-- ============================================================
-- ANALYSIS TABLES
-- ============================================================

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
