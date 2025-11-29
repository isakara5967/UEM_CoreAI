-- ============================================================
-- UEM_CoreAI PreData + Log System
-- Phase A - Step 4: Views
-- ============================================================

-- Full cycle snapshot view
CREATE OR REPLACE VIEW core.v_full_cycle_snapshot AS
SELECT 
    c.run_id,
    c.cycle_id,
    c.tick,
    c.started_at,
    c.ended_at,
    c.summary AS cycle_summary,
    m.coherence_score,
    m.efficiency_score,
    m.failure_streak,
    m.ethmor_block_rate,
    m.outcome_quality_score,
    m.behavior_cluster_id,
    r.experiment_id,
    r.ab_bucket,
    r.primary_language
FROM core.cycles c
LEFT JOIN core.metamind_cycle_summary m ON c.run_id = m.run_id AND c.cycle_id = m.cycle_id
LEFT JOIN core.runs r ON c.run_id = r.run_id;

COMMENT ON VIEW core.v_full_cycle_snapshot IS 'Cycle + MetaMind + Run bilgilerini birleştiren view';

-- Recent events view (son 1000 event)
CREATE OR REPLACE VIEW core.v_recent_events AS
SELECT 
    e.id,
    e.run_id,
    e.cycle_id,
    e.event_type,
    e.timestamp,
    e.module_name,
    e.action_name,
    e.emotion_valence,
    e.ethmor_decision,
    e.payload
FROM core.events e
ORDER BY e.timestamp DESC
LIMIT 1000;

COMMENT ON VIEW core.v_recent_events IS 'Son 1000 event için hızlı erişim';

-- Active alerts view
CREATE OR REPLACE VIEW core.v_active_alerts AS
SELECT 
    alert_id,
    run_id,
    cycle_id,
    alert_type,
    severity,
    category,
    message,
    created_ts,
    context
FROM core.alerts
WHERE resolved = false
ORDER BY 
    CASE severity 
        WHEN 'critical' THEN 1 
        WHEN 'warning' THEN 2 
        ELSE 3 
    END,
    created_ts DESC;

COMMENT ON VIEW core.v_active_alerts IS 'Çözülmemiş alertler - öncelik sıralı';

-- Run summary view
CREATE OR REPLACE VIEW core.v_run_summary AS
SELECT 
    r.run_id,
    r.started_at,
    r.ended_at,
    r.status,
    r.experiment_id,
    r.ab_bucket,
    COUNT(DISTINCT c.cycle_id) as total_cycles,
    COUNT(e.id) as total_events,
    AVG(m.coherence_score) as avg_coherence,
    AVG(m.efficiency_score) as avg_efficiency,
    MAX(m.failure_streak) as max_failure_streak
FROM core.runs r
LEFT JOIN core.cycles c ON r.run_id = c.run_id
LEFT JOIN core.events e ON r.run_id = e.run_id
LEFT JOIN core.metamind_cycle_summary m ON r.run_id = m.run_id
GROUP BY r.run_id, r.started_at, r.ended_at, r.status, r.experiment_id, r.ab_bucket;

COMMENT ON VIEW core.v_run_summary IS 'Run bazlı özet istatistikler';
