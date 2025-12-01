-- ============================================================
-- UEM_CoreAI PreData + Log System DDL
-- Version: 2.0 (v5 - 16D StateVector Update - 1 Aralık 2025)
-- Phase A - Step 1: Schema & Extension Creation
-- ============================================================

-- ============================================================
-- EXTENSIONS
-- ============================================================

-- pgvector extension (16D vector desteği için)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- SCHEMAS
-- ============================================================

-- Core schema (Logger/Analytics tabloları)
CREATE SCHEMA IF NOT EXISTS core;

-- Yetki ver
GRANT ALL ON SCHEMA core TO uem;

-- Schema açıklamaları
COMMENT ON SCHEMA core IS 'UEM Core AI - PreData, Log, MetaMetrics sistemi (v5)';
COMMENT ON SCHEMA public IS 'UEM Core AI - Memory Storage (events, snapshots) - 16D vectors';

-- ============================================================
-- ENUM TYPES
-- ============================================================

-- Event kategorileri (public.events için)
DO $$ BEGIN
    CREATE TYPE event_category AS ENUM (
        'WORLD', 'INTERNAL', 'AGENT_ACTION', 'OBSERVATION'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Run durumları
DO $$ BEGIN
    CREATE TYPE run_status AS ENUM (
        'running', 'completed', 'failed', 'paused'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Experiment durumları
DO $$ BEGIN
    CREATE TYPE experiment_status AS ENUM (
        'planned', 'running', 'paused', 'completed', 'cancelled'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Trend tipleri (MetaMind için)
DO $$ BEGIN
    CREATE TYPE trend_type AS ENUM (
        'rising', 'falling', 'stable', 'volatile'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Alert severity
DO $$ BEGIN
    CREATE TYPE alert_severity AS ENUM (
        'info', 'warning', 'critical', 'emergency'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;
