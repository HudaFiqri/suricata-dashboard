-- Migration: Add permissions column to users table
-- This adds support for custom permissions for each user

-- Add permissions column (JSONB for flexible permission storage)
ALTER TABLE users
ADD COLUMN IF NOT EXISTS permissions JSONB DEFAULT '{}';

-- Create index on permissions for faster queries
CREATE INDEX IF NOT EXISTS idx_users_permissions ON users USING GIN (permissions);

-- Update existing users to have empty permissions object
UPDATE users
SET permissions = '{}'
WHERE permissions IS NULL;

-- Add comment
COMMENT ON COLUMN users.permissions IS 'Custom permissions for the user (overrides role permissions)';
