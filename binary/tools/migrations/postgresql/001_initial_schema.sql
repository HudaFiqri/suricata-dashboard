-- PostgreSQL Initial Schema
-- Migration: 001
-- Description: Create initial tables for remote agent architecture

BEGIN;

-- ============================================================================
-- AGENTS TABLE
-- ============================================================================

CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    ip_address INET,

    -- Authentication
    token_hash VARCHAR(512) NOT NULL,
    encryption_key VARCHAR(512) NOT NULL,

    -- Metadata
    tags JSONB DEFAULT '[]',
    version VARCHAR(50),

    -- Suricata Info
    suricata_version VARCHAR(50),
    suricata_pid INTEGER,

    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    last_seen TIMESTAMP WITH TIME ZONE,
    last_event_at TIMESTAMP WITH TIME ZONE,

    -- Health Metrics (cached)
    health_metrics JSONB,

    -- System Info
    system_info JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_last_seen ON agents(last_seen DESC);
CREATE INDEX idx_agents_tags ON agents USING GIN(tags);

-- ============================================================================
-- AGENT_CONFIGS TABLE
-- ============================================================================

CREATE TABLE agent_configs (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,

    -- Config Content
    config_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64),

    -- Versioning
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,

    -- Validation
    is_valid BOOLEAN DEFAULT TRUE,
    validation_errors TEXT,

    -- Status
    applied_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'draft',

    -- Metadata
    changed_by VARCHAR(255),
    change_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_agent_configs_agent_id ON agent_configs(agent_id);
CREATE INDEX idx_agent_configs_active ON agent_configs(agent_id, is_active) WHERE is_active = TRUE;
CREATE UNIQUE INDEX idx_agent_configs_unique_active ON agent_configs(agent_id, config_type, is_active) WHERE is_active = TRUE;

-- ============================================================================
-- AGENT_COMMANDS TABLE
-- ============================================================================

CREATE TABLE agent_commands (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,

    -- Command Details
    command_type VARCHAR(100) NOT NULL,
    parameters JSONB,

    -- Status
    status VARCHAR(50) DEFAULT 'pending',

    -- Result
    result JSONB,
    error_message TEXT,

    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    timeout_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_by VARCHAR(255),
    priority INTEGER DEFAULT 5
);

-- Indexes
CREATE INDEX idx_agent_commands_agent_status ON agent_commands(agent_id, status);
CREATE INDEX idx_agent_commands_pending ON agent_commands(status, created_at) WHERE status = 'pending';

-- ============================================================================
-- AGENT_STATISTICS TABLE
-- ============================================================================

CREATE TABLE agent_statistics (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,

    -- Time bucket
    bucket_time TIMESTAMP WITH TIME ZONE NOT NULL,
    bucket_interval VARCHAR(20) NOT NULL,

    -- Metrics
    metrics JSONB NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_agent_statistics_agent_time ON agent_statistics(agent_id, bucket_time DESC);
CREATE INDEX idx_agent_statistics_interval ON agent_statistics(bucket_interval, bucket_time DESC);

-- ============================================================================
-- USERS TABLE (Enhanced)
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(512) NOT NULL,

    -- Roles
    role VARCHAR(50) DEFAULT 'viewer',

    -- API Access
    api_key_hash VARCHAR(512),

    -- Permissions
    permissions JSONB DEFAULT '{}',

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- AUDIT_LOGS TABLE
-- ============================================================================

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,

    -- Who
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(255),
    agent_id INTEGER REFERENCES agents(id) ON DELETE SET NULL,

    -- What
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,

    -- Details
    details JSONB,
    ip_address INET,
    user_agent TEXT,

    -- When
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_agent ON audit_logs(agent_id, created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, created_at DESC);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_configs_updated_at BEFORE UPDATE ON agent_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;
