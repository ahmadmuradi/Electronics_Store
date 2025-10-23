-- Electronics Store Inventory Database Initialization
-- This script sets up the PostgreSQL database with proper extensions and initial configuration

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create database user if not exists (handled by Docker environment)
-- The main tables will be created by SQLAlchemy migrations

-- Create indexes for better performance (these will be created after tables exist)
-- Note: These are examples - actual indexes will be created by SQLAlchemy

-- Set up database configuration
ALTER DATABASE inventory_db SET timezone TO 'UTC';

-- Create a function for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Electronics Store Inventory Database initialized successfully';
END $$;
