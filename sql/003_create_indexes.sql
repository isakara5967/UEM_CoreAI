-- ============================================================
-- UEM_CoreAI PreData + Log System DDL
-- Version: 1.0 (v12 Final Consensus)
-- Phase A - Step 3: Index Creation
-- ============================================================

-- experiments indexes
CREATE INDEX IF NOT EXISTS idx_experiments_status ON core.experiments(status);
CREATE INDEX IF NOT EXISTS idx_experiments_owner ON core.experiments(owner);

-- runs indexes
CREATE INDEX IF NOT EXISTS idx_runs_status ON core.runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_experiment ON core.runs(experiment_id);
CREATE INDEX IF NOT EXISTS idx_runs_started ON core.runs(started_at);

-- cycles indexes
CREATE INDEX IF NOT EXISTS idx_cycles_run ON core.cycles(run_id);
CREATE INDEX IF NOT EXISTS idx_cycles_tick ON core.cycles(tick);
CREATE INDEX IF NOT EXISTS idx_cycles_started ON core.cycles(started_at);

-- events indexes (kritik - en büyük tablo)
CREATE INDEX IF NOT EXISTS idx_events_run_cycle ON core.events(run_id, cycle_id);
CREATE INDEX IF NOT EXISTS idx_events_module ON core.events(module_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON core.events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_type ON core.events(event_type);
-- Denormalize column indexes
CREATE INDEX IF NOT EXISTS idx_events_emotion ON core.events(emotion_valence);
CREATE INDEX IF NOT EXISTS idx_events_action ON core.events(action_name);
CREATE INDEX IF NOT EXISTS idx_events_ethmor ON core.events(ethmor_decision);
CREATE INDEX IF NOT EXISTS idx_events_time ON core.events(cycle_time_ms);
CREATE INDEX IF NOT EXISTS idx_events_module_name ON core.events(module_name);
CREATE INDEX IF NOT EXISTS idx_events_input_lang ON core.events(input_language);
-- Composite indexes
CREATE INDEX IF NOT EXISTS idx_events_composite ON core.events(run_id, cycle_id, module_id);

-- metamind_cycle_summary indexes
CREATE INDEX IF NOT EXISTS idx_metamind_run_cycle ON core.metamind_cycle_summary(run_id, cycle_id);
CREATE INDEX IF NOT EXISTS idx_metamind_coherence ON core.metamind_cycle_summary(coherence_score);
CREATE INDEX IF NOT EXISTS idx_metamind_failure ON core.metamind_cycle_summary(failure_streak);
CREATE INDEX IF NOT EXISTS idx_metamind_cluster ON core.metamind_cycle_summary(behavior_cluster_id);

-- alerts indexes
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON core.alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_category ON core.alerts(category);
CREATE INDEX IF NOT EXISTS idx_alerts_run ON core.alerts(run_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON core.alerts(created_ts);
CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON core.alerts(resolved) WHERE resolved = false;

-- metric_registry indexes
CREATE INDEX IF NOT EXISTS idx_metric_registry_group ON core.metric_registry(metric_group);
CREATE INDEX IF NOT EXISTS idx_metric_registry_module ON core.metric_registry(owner_module);
CREATE INDEX IF NOT EXISTS idx_metric_registry_version ON core.metric_registry(version);
