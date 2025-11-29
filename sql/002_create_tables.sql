-- ============================================================
-- UEM_CoreAI PreData + Log System DDL
-- Version: 1.0 (v12 Final Consensus)
-- Phase A - Step 2: Table Creation (10 Tables)
-- ============================================================

-- ============================================================
-- TABLO 1: core.experiments
-- ============================================================
CREATE TABLE IF NOT EXISTS core.experiments (
    experiment_id   TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT,
    hypothesis      TEXT,
    start_ts        TIMESTAMPTZ,
    end_ts          TIMESTAMPTZ,
    status          TEXT DEFAULT 'planned' 
                    CHECK (status IN ('planned', 'running', 'paused', 'completed', 'cancelled')),
    owner           TEXT,
    config          JSONB,
    tags            TEXT[],
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE core.experiments IS 'Deney tanımları ve A/B test yönetimi';

-- ============================================================
-- TABLO 2: core.config_snapshots
-- ============================================================
CREATE TABLE IF NOT EXISTS core.config_snapshots (
    config_id       TEXT PRIMARY KEY,
    created_ts      TIMESTAMPTZ DEFAULT NOW(),
    core_version    TEXT NOT NULL,
    model_version   TEXT,
    policy_set_id   TEXT,
    ethmor_rules_version TEXT,
    config_blob     JSONB NOT NULL,
    checksum        TEXT,
    description     TEXT
);

COMMENT ON TABLE core.config_snapshots IS 'Konfigürasyon geçmişi - reproducibility için';

-- ============================================================
-- TABLO 3: core.modules (Referans)
-- ============================================================
CREATE TABLE IF NOT EXISTS core.modules (
    module_id       SERIAL PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,
    description     TEXT,
    is_active       BOOLEAN DEFAULT true
);

COMMENT ON TABLE core.modules IS 'UEM modül tanımları';

-- ============================================================
-- TABLO 4: core.submodules (Referans)
-- ============================================================
CREATE TABLE IF NOT EXISTS core.submodules (
    submodule_id    SERIAL PRIMARY KEY,
    module_id       INT REFERENCES core.modules(module_id),
    name            TEXT NOT NULL,
    description     TEXT,
    UNIQUE(module_id, name)
);

COMMENT ON TABLE core.submodules IS 'Alt modül tanımları';

-- ============================================================
-- TABLO 5: core.runs
-- ============================================================
CREATE TABLE IF NOT EXISTS core.runs (
    run_id          TEXT PRIMARY KEY,
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    status          TEXT DEFAULT 'running'
                    CHECK (status IN ('running', 'completed', 'failed', 'paused')),
    config          JSONB,
    summary         JSONB,
    experiment_id   TEXT REFERENCES core.experiments(experiment_id),
    config_id       TEXT REFERENCES core.config_snapshots(config_id),
    environment_profile JSONB,
    ab_bucket       TEXT,
    primary_language TEXT
);

COMMENT ON TABLE core.runs IS 'Her UEM çalıştırma oturumu';

-- ============================================================
-- TABLO 6: core.cycles
-- ============================================================
CREATE TABLE IF NOT EXISTS core.cycles (
    id              BIGSERIAL,
    run_id          TEXT NOT NULL REFERENCES core.runs(run_id) ON DELETE CASCADE,
    cycle_id        INT NOT NULL,
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    tick            INT,
    status          TEXT DEFAULT 'running'
                    CHECK (status IN ('running', 'completed', 'failed')),
    summary         JSONB,
    PRIMARY KEY (run_id, cycle_id)
);

COMMENT ON TABLE core.cycles IS 'Her cognitive cycle kaydı';

-- ============================================================
-- TABLO 7: core.events (EN BÜYÜK TABLO)
-- ============================================================
CREATE TABLE IF NOT EXISTS core.events (
    id              BIGSERIAL PRIMARY KEY,
    run_id          TEXT NOT NULL,
    cycle_id        INT NOT NULL,
    module_id       INT REFERENCES core.modules(module_id),
    submodule_id    INT REFERENCES core.submodules(submodule_id),
    event_type      TEXT NOT NULL,
    timestamp       TIMESTAMPTZ DEFAULT NOW(),
    payload         JSONB,
    -- Denormalize kolonlar (9)
    emotion_valence         FLOAT,
    action_name             TEXT,
    ethmor_decision         TEXT,
    success_flag_explicit   BOOLEAN,
    cycle_time_ms           FLOAT,
    module_name             TEXT,
    input_quality_score     FLOAT,
    input_language          TEXT,
    output_language         TEXT,
    FOREIGN KEY (run_id, cycle_id) REFERENCES core.cycles(run_id, cycle_id) ON DELETE CASCADE
);

COMMENT ON TABLE core.events IS 'Tüm modül eventleri - en yüksek hacimli tablo';

-- ============================================================
-- TABLO 8: core.metamind_cycle_summary
-- ============================================================
CREATE TABLE IF NOT EXISTS core.metamind_cycle_summary (
    id              BIGSERIAL PRIMARY KEY,
    run_id          TEXT NOT NULL,
    cycle_id        INT NOT NULL,
    calculated_at   TIMESTAMPTZ DEFAULT NOW(),
    -- 19 MetaMind Kolonu
    coherence_score         FLOAT,
    efficiency_score        FLOAT,
    outcome_quality_score   FLOAT,
    decision_confidence_avg FLOAT,
    ethmor_block_rate       FLOAT,
    dominant_emotion        TEXT,
    emotion_stability       FLOAT,
    valence_trend           TEXT CHECK (valence_trend IN ('rising', 'falling', 'stable', 'volatile')),
    arousal_trend           TEXT CHECK (arousal_trend IN ('rising', 'falling', 'stable', 'volatile')),
    failure_streak          INT DEFAULT 0,
    recovery_attempts       INT DEFAULT 0,
    action_diversity_score  FLOAT,
    repeated_action_flag    BOOLEAN DEFAULT false,
    cross_module_latency_ms FLOAT,
    trust_score_avg         FLOAT,
    quality_score_avg       FLOAT,
    anomaly_flags           TEXT[],
    behavior_cluster_id     TEXT,
    meta_notes              JSONB,
    FOREIGN KEY (run_id, cycle_id) REFERENCES core.cycles(run_id, cycle_id) ON DELETE CASCADE
);

COMMENT ON TABLE core.metamind_cycle_summary IS 'MetaMind tarafından hesaplanan cycle özet metrikleri';

-- ============================================================
-- TABLO 9: core.alerts
-- ============================================================
CREATE TABLE IF NOT EXISTS core.alerts (
    alert_id        TEXT PRIMARY KEY,
    run_id          TEXT REFERENCES core.runs(run_id),
    cycle_id        INT,
    created_ts      TIMESTAMPTZ DEFAULT NOW(),
    alert_type      TEXT NOT NULL,
    severity        TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    category        TEXT,
    message         TEXT NOT NULL,
    context         JSONB,
    threshold_value FLOAT,
    actual_value    FLOAT,
    acknowledged    BOOLEAN DEFAULT false,
    acknowledged_by TEXT,
    acknowledged_at TIMESTAMPTZ,
    resolved        BOOLEAN DEFAULT false,
    resolved_at     TIMESTAMPTZ
);

COMMENT ON TABLE core.alerts IS 'MetaMind tarafından üretilen uyarılar';

-- ============================================================
-- TABLO 10: core.metric_registry
-- ============================================================
CREATE TABLE IF NOT EXISTS core.metric_registry (
    metric_id           TEXT PRIMARY KEY,
    metric_group        TEXT NOT NULL,
    display_name        TEXT NOT NULL,
    description         TEXT NOT NULL,
    value_type          TEXT NOT NULL CHECK (value_type IN ('float', 'int', 'text', 'enum', 'json', 'array', 'boolean')),
    valid_range         JSONB,
    unit                TEXT,
    version             TEXT NOT NULL,
    introduced_in       TEXT,
    deprecated_in       TEXT,
    owner_module        TEXT,
    log_location        TEXT,
    calculation_formula TEXT,
    dependencies        TEXT[],
    tags                TEXT[],
    extra_metadata      JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE core.metric_registry IS 'Tüm metriklerin merkezi tanım kaydı';
