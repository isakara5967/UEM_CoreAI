-- ============================================================
-- UEM_CoreAI PreData + Log System DDL
-- Version: 1.0 (v12 Final Consensus)
-- Phase A - Step 1: Schema Creation
-- ============================================================

-- Schema oluştur
CREATE SCHEMA IF NOT EXISTS core;

-- Yetki ver
GRANT ALL ON SCHEMA core TO uem;

COMMENT ON SCHEMA core IS 'UEM Core AI - PreData, Log, MetaMetrics sistemi';
