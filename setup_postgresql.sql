
-- PostgreSQL Setup Script for POS System
-- Run this as PostgreSQL superuser (postgres)

-- Create database
CREATE DATABASE pos_network;

-- Create user
CREATE USER admin WITH PASSWORD 'admin';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE pos_network TO admin;
GRANT CREATE ON DATABASE pos_network TO admin;

-- For network access, also ensure postgresql.conf has:
-- listen_addresses = '*'
-- 
-- And pg_hba.conf has:
-- host    all             all             0.0.0.0/0               md5

\q
