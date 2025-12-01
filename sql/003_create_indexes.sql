-- ============================================================
-- UEM_CoreAI PreData + Log System DDL
-- Version: 2.0 (v5 - 16D StateVector Update - 1 Aralık 2025)
-- Phase A - Step 3: Index Creation
-- ============================================================

-- ############################################################
-- PUBLIC SCHEMA INDEXES (Memory Storage)
-- ############################################################

-- public.events indexes
CREATE INDEX IF NOT EXISTS idx_public_events_agent_tick 
    ON public.events (agent_id, tick DESC);

CREATE INDEX IF NOT EXISTS idx_public_events_category 
    ON public.events (category);

CREATE INDEX IF NOT EXISTS idx_public_events_timestamp 
    ON public.events (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_public_events_source 
    ON public.events (source);

-- JSONB index for metadata
CREATE INDEX IF NOT EXISTS idx_public_events_metadata 
    ON public.events USING gin (metadata);

-- public.snapshots indexes
CREATE INDEX IF NOT EXISTS idx_public_snapshots_agent_tick 
    ON public.snapshots (agent_id, tick DESC);

CREATE INDEX IF NOT EXISTS idx_public_snapshots_timestamp 
    ON public.snapshots (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_public_snapshots_consolidation 
    ON public.snapshots (consolidation_level);

CREATE INDEX IF NOT EXISTS idx_public_snapshots_strength 
    ON public.snapshots (strength DESC);

-- JSONB index for metadata
CREATE INDEX IF NOT EXISTS idx_public_snapshots_metadata 
    ON public.snapshots USING gin (metadata);

-- Vector index (ivfflat) for similarity search - 16D
-- NOT: Bu index büyük tablolarda oluşturulmalı (100+ kayıt)
CREATE INDEX IF NOT EXISTS idx_public_snapshots_vector 
    ON public.snapshots USING ivfflat (state_vector vector_l2_ops) 
    WITH (lists = 100);

-- ############################################################
-- CORE SCHEMA INDEXES (Logger/Analytics)
-- ############################################################

-- core.experiments indexes
CREATE INDEX IF NOT EXISTS idx_experiments_status 
    ON core.experiments(status);

CREATE INDEX IF NOT EXISTS idx_experiments_owner 
    ON core.experiments(owner);

CREATE INDEX IF NOT EXISTS idx_experiments_dates 
    ON core.experiments(start_ts, end_ts);

-- core.runs indexes
CREATE INDEX IF NOT EXISTS idx_runs_status 
    ON core.runs(status);

CREATE INDEX IF NOT EXISTS idx_runs_experiment 
    ON core.runs(experiment_id);

CREATE INDEX IF NOT EXISTS idx_runs_started 
    ON core.runs(started_at DESC);

CREATE INDEX IF NOT EXISTS idx_runs_config 
    ON core.runs(config_id);

-- core.cycles indexes
CREATE INDEX IF NOT EXISTS idx_cycles_run 
    ON core.cycles(run_id);

CREATE INDEX IF NOT EXISTS idx_cycles_tick 
    ON core.cycles(tick);

CREATE INDEX IF NOT EXISTS idx_cycles_started 
    ON core.cycles(started_at DESC);

CREATE INDEX IF NOT EXISTS idx_cycles_status 
    ON core.cycles(status);

-- core.events indexes (kritik - en büyük tablo)
CREATE INDEX IF NOT EXISTS idx_core_events_run_cycle 
    ON core.events(run_id, cycle_id);

CREATE INDEX IF NOT EXISTS idx_core_events_module 
    ON core.events(module_id);

CREATE INDEX IF NOT EXISTS idx_core_events_timestamp 
    ON core.events(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_core_events_type 
    ON core.events(event_type);

-- Denormalized column indexes (hızlı filtering için)
CREATE INDEX IF NOT EXISTS idx_core_events_emotion 
    ON core.events(emotion_valence);

CREATE INDEX IF NOT EXISTS idx_core_events_action 
    ON core.events(action_name);

CREATE INDEX IF NOT EXISTS idx_core_events_ethmor 
    ON core.events(ethmor_decision);

CREATE INDEX IF NOT EXISTS idx_core_events_time 
    ON core.events(cycle_time_ms);

CREATE INDEX IF NOT EXISTS idx_core_events_module_name 
    ON core.events(module_name);

CREATE INDEX IF NOT EXISTS idx_core_events_input_lang 
    ON core.events(input_language);

-- Composite indexes
CREATE INDEX IF NOT EXISTS idx_core_events_composite 
    ON core.events(run_id, cycle_id, module_id);

-- JSONB index for payload
CREATE INDEX IF NOT EXISTS idx_core_events_payload 
    ON core.events USING gin (payload);

-- core.metamind_cycle_summary indexes
CREATE INDEX IF NOT EXISTS idx_metamind_run_cycle 
    ON core.metamind_cycle_summary(run_id, cycle_id);

CREATE INDEX IF NOT EXISTS idx_metamind_coherence 
    ON core.metamind_cycle_summary(coherence_score);

CREATE INDEX IF NOT EXISTS idx_metamind_failure 
    ON core.metamind_cycle_summary(failure_streak);

CREATE INDEX IF NOT EXISTS idx_metamind_cluster 
    ON core.metamind_cycle_summary(behavior_cluster_id);

CREATE INDEX IF NOT EXISTS idx_metamind_emotion 
    ON core.metamind_cycle_summary(dominant_emotion);

-- core.alerts indexes
CREATE INDEX IF NOT EXISTS idx_alerts_severity 
    ON core.alerts(severity);

CREATE INDEX IF NOT EXISTS idx_alerts_category 
    ON core.alerts(category);

CREATE INDEX IF NOT EXISTS idx_alerts_run 
    ON core.alerts(run_id);

CREATE INDEX IF NOT EXISTS idx_alerts_created 
    ON core.alerts(created_ts DESC);

-- Partial index for unresolved alerts
CREATE INDEX IF NOT EXISTS idx_alerts_unresolved 
    ON core.alerts(resolved) 
    WHERE resolved = false;

-- core.metric_registry indexes
CREATE INDEX IF NOT EXISTS idx_metric_registry_group 
    ON core.metric_registry(metric_group);

CREATE INDEX IF NOT EXISTS idx_metric_registry_module 
    ON core.metric_registry(owner_module);

CREATE INDEX IF NOT EXISTS idx_metric_registry_version 
    ON core.metric_registry(version);
