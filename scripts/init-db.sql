-- SMEFlow Database Initialization Script
-- Creates additional databases and extensions

-- Create Keycloak database
CREATE DATABASE keycloak;

-- Create extensions in main database
\c smeflow;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create extensions in Keycloak database
\c keycloak;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
