-- Migration: Add custom_roles table
-- This allows admins to create custom roles with specific permissions

CREATE TABLE IF NOT EXISTS custom_roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    permissions JSONB DEFAULT '[]',
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_custom_roles_name ON custom_roles(name);
CREATE INDEX IF NOT EXISTS idx_custom_roles_is_system ON custom_roles(is_system);

-- Add comment
COMMENT ON TABLE custom_roles IS 'Custom roles with configurable permissions';
COMMENT ON COLUMN custom_roles.is_system IS 'System roles (admin, operator, analyst, viewer) cannot be deleted';

-- Insert default system roles
INSERT INTO custom_roles (name, display_name, description, permissions, is_system) VALUES
('admin', 'Administrator', 'Full access to all features',
 '["agents.view","agents.manage","events.view","events.export","configs.view","configs.edit","users.view","users.manage","sessions.view","sessions.manage","stats.view","logs.view"]'::jsonb,
 true),
('operator', 'Operator', 'Manage infrastructure and configurations',
 '["agents.view","agents.manage","events.view","events.export","configs.view","configs.edit","stats.view","logs.view"]'::jsonb,
 true),
('analyst', 'Security Analyst', 'Read and analyze security data',
 '["agents.view","events.view","events.export","configs.view","stats.view","logs.view"]'::jsonb,
 true),
('viewer', 'Viewer', 'Read-only access to monitoring data',
 '["agents.view","events.view","stats.view","logs.view"]'::jsonb,
 true)
ON CONFLICT (name) DO NOTHING;
