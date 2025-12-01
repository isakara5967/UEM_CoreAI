-- ============================================================
-- UEM_CoreAI PreData + Log System DDL
-- Version: 2.0 (v5 - 16D StateVector Update - 1 Aralık 2025)
-- Phase A - Step 2: Table Creation
-- ============================================================

-- ############################################################
-- PUBLIC SCHEMA - MEMORY STORAGE (16D Vectors)
-- ############################################################

-- ============================================================
-- PUBLIC TABLO 1: public.events (Episodic Memory - 16D)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.events (
    id              BIGSERIAL PRIMARY KEY,
    agent_id        UUID NOT NULL,
    session_id      UUID,
    timestamp       TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    tick            BIGINT NOT NULL DEFAULT 0,
    category        VARCHAR(20) DEFAULT 'WORLD',
    source          VARCHAR(50) NOT NULL,
    target          VARCHAR(50) NOT NULL,
    -- 16D Vector kolonları (v5)
    state_before    vector(16),              -- Cycle başı state
    effect          vector(16) NOT NULL,     -- Aksiyon etkisi
    state_after     vector(16),              -- Cycle sonu state
    -- Meta
    salience        REAL DEFAULT 0.5,
    metadata        JSONB DEFAULT '{}'
);

COMMENT ON TABLE public.events IS 'Episodic Memory - Her event için state_before, effect, state_after (16D vectors)';
COMMENT ON COLUMN public.events.state_before IS '16D: [resource, threat, wellbeing, health, energy, valence, arousal, dominance, reserved×8]';
COMMENT ON COLUMN public.events.effect IS '16D: Aksiyon etkisi (delta)';
COMMENT ON COLUMN public.events.state_after IS '16D: state_before + effect = state_after';

-- ============================================================
-- PUBLIC TABLO 2: public.snapshots (State Snapshots - 16D)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.snapshots (
    id                  BIGSERIAL PRIMARY KEY,
    agent_id            UUID NOT NULL,
    session_id          UUID,
    timestamp           TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    tick                BIGINT NOT NULL DEFAULT 0,
    -- 16D State vector
    state_vector        vector(16) NOT NULL,
    -- Memory properties
    consolidation_level INTEGER DEFAULT 0,
    last_accessed       TIMESTAMPTZ DEFAULT NOW(),
    access_count        INTEGER DEFAULT 0,
    strength            REAL DEFAULT 1.0,
    salience            REAL DEFAULT 0.5,
    goals               JSONB DEFAULT '[]',
    metadata            JSONB DEFAULT '{}'
);

COMMENT ON TABLE public.snapshots IS 'State Snapshots - 16D state_vector ile similarity search';
COMMENT ON COLUMN public.snapshots.state_vector IS '16D: [resource, threat, wellbeing, health, energy, valence, arousal, dominance, reserved×8]';

-- ############################################################
-- CORE SCHEMA - LOGGER/ANALYTICS
-- ############################################################

-- ============================================================
-- CORE TABLO 1: core.experiments
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
-- CORE TABLO 2: core.config_snapshots
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
-- CORE TABLO 3: core.modules (Referans)
-- ============================================================
CREATE TABLE IF NOT EXISTS core.modules (
    module_id       SERIAL PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,
    description     TEXT,
    is_active       BOOLEAN DEFAULT true
);

COMMENT ON TABLE core.modules IS 'UEM modül tanımları';

-- Seed data
INSERT INTO core.modules (name, description) VALUES
    ('perception', 'Algı modülü'),
    ('emotion', 'Duygu modülü'),
    ('memory', 'Hafıza modülü'),
    ('self', 'Benlik modülü'),
    ('workspace', 'Çalışma alanı modülü'),
    ('planner', 'Planlama modülü'),
    ('ethmor', 'Etik karar modülü'),
    ('empathy', 'Empati modülü'),
    ('execution', 'Yürütme modülü')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- CORE TABLO 4: core.submodules (Referans)
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
-- CORE TABLO 5: core.runs
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
-- CORE TABLO 6: core.cycles
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
-- CORE TABLO 7: core.events (Logger - Analytics)
-- NOT: Bu tablo public.events'ten FARKLIDIR!
-- public.events = Memory Storage (16D vectors)
-- core.events = Logger/Analytics (PreData payload)
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
    -- Denormalized kolonlar (hızlı query için)
    emotion_valence         REAL,
    action_name             TEXT,
    ethmor_decision         TEXT,
    success_flag_explicit   BOOLEAN,
    cycle_time_ms           REAL,
    module_name             TEXT,
    input_quality_score     REAL,
    input_language          TEXT,
    output_language         TEXT,
    FOREIGN KEY (run_id, cycle_id) REFERENCES core.cycles(run_id, cycle_id) ON DELETE CASCADE
);

COMMENT ON TABLE core.events IS 'Tüm modül eventleri - PreData payload içerir (Logger/Analytics)';

-- ============================================================
-- CORE TABLO 8: core.metamind_cycle_summary
-- ============================================================
CREATE TABLE IF NOT EXISTS core.metamind_cycle_summary (
    id              BIGSERIAL PRIMARY KEY,
    run_id          TEXT NOT NULL,
    cycle_id        INT NOT NULL,
    calculated_at   TIMESTAMPTZ DEFAULT NOW(),
    -- 19 MetaMind Kolonu
    coherence_score         REAL,
    efficiency_score        REAL,
    outcome_quality_score   REAL,
    decision_confidence_avg REAL,
    ethmor_block_rate       REAL,
    dominant_emotion        TEXT,
    emotion_stability       REAL,
    valence_trend           TEXT CHECK (valence_trend IN ('rising', 'falling', 'stable', 'volatile')),
    arousal_trend           TEXT CHECK (arousal_trend IN ('rising', 'falling', 'stable', 'volatile')),
    failure_streak          INT DEFAULT 0,
    recovery_attempts       INT DEFAULT 0,
    action_diversity_score  REAL,
    repeated_action_flag    BOOLEAN DEFAULT false,
    cross_module_latency_ms REAL,
    trust_score_avg         REAL,
    quality_score_avg       REAL,
    anomaly_flags           TEXT[],
    behavior_cluster_id     TEXT,
    meta_notes              JSONB,
    FOREIGN KEY (run_id, cycle_id) REFERENCES core.cycles(run_id, cycle_id) ON DELETE CASCADE
);

COMMENT ON TABLE core.metamind_cycle_summary IS 'MetaMind üst-bilişsel analiz özeti';

-- ============================================================
-- CORE TABLO 9: core.alerts
-- ============================================================
CREATE TABLE IF NOT EXISTS core.alerts (
    alert_id        BIGSERIAL PRIMARY KEY,
    run_id          TEXT REFERENCES core.runs(run_id),
    cycle_id        INT,
    created_ts      TIMESTAMPTZ DEFAULT NOW(),
    severity        TEXT DEFAULT 'info'
                    CHECK (severity IN ('info', 'warning', 'critical', 'emergency')),
    category        TEXT NOT NULL,
    title           TEXT NOT NULL,
    message         TEXT,
    context         JSONB,
    resolved        BOOLEAN DEFAULT false,
    resolved_at     TIMESTAMPTZ,
    resolved_by     TEXT
);

COMMENT ON TABLE core.alerts IS 'Sistem uyarıları ve anomali bildirimleri';

-- ============================================================
-- CORE TABLO 10: core.metric_registry
-- ============================================================
CREATE TABLE IF NOT EXISTS core.metric_registry (
    metric_id       TEXT PRIMARY KEY,
    metric_group    TEXT NOT NULL,
    display_name    TEXT NOT NULL,
    description     TEXT,
    value_type      TEXT NOT NULL CHECK (value_type IN ('int', 'float', 'text', 'json', 'bool')),
    version         TEXT DEFAULT 'v1.0',
    introduced_in   TEXT,
    deprecated_in   TEXT,
    owner_module    TEXT,
    log_location    TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE core.metric_registry IS 'PreData metrik tanımları - 52 alan';
