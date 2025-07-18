-- init.sql
-- This script will be executed when the PostgreSQL container starts

-- Create the company_details table
CREATE TABLE IF NOT EXISTS company_details (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    founded_in DATE NOT NULL,
    founded_by TEXT[] NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_company_name ON company_details(company_name);
CREATE INDEX IF NOT EXISTS idx_founded_in ON company_details(founded_in);
