-- ============================================================
-- MetaMind v1.9 Database Migration
-- ============================================================
-- Dosya: sql/006_metamind_v1.9.sql
-- Tarih: 2025-12-03
-- Açıklama: 3 yeni tablo + 1 mevcut tablo güncelleme
-- 
-- Yeni Tablolar:
--   1. core.metamind_episodes
--   2. core.metamind_patterns  
--   3. core.metamind_meta_events
--
-- Güncelleme:
--   4. core.metamind_cycle_summary (episode_id + 6 index + 6 confidence)
--
-- ⚠️ Önemli: 004 = 16D migration, 005 = seed data - bu dosya 006
-- ============================================================

BEGIN;

-- ============================================================
-- TABLO 1: core.metamind_episodes
-- ============================================================
-- Episode = Cycle grupları (default: 100 cycle = 1 episode)
-- Boundary: time_window | event_override | run_end | goal_complete
-- ⚠️ Alice notu: 100 değeri config'ten gelecek, hardcode DEĞİL

CREATE TABLE IF NOT EXISTS core.metamind_episodes (
    episode_id      TEXT PRIMARY KEY,  -- Format: "{run_id}:{seq}"
    run_id          TEXT NOT NULL REFERENCES core.runs(run_id) ON DELETE CASCADE,
    episode_seq     INT NOT NULL,
    start_cycle_id  INT NOT NULL,
    end_cycle_id    INT,               -- NULL if ongoing
    start_time      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time        TIMESTAMPTZ,
    semantic_tag    TEXT DEFAULT 'auto_window',
    boundary_reason TEXT DEFAULT 'time_window'
                    CHECK (boundary_reason IN ('time_window', 'event_override', 'run_end', 'goal_complete')),
    cycle_count     INT DEFAULT 0,
    summary         JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(run_id, episode_seq)
);

COMMENT ON TABLE core.metamind_episodes IS 'MetaMind episode kayıtları - cycle grupları';
COMMENT ON COLUMN core.metamind_episodes.episode_id IS 'Format: {run_id}:{episode_seq}';
COMMENT ON COLUMN core.metamind_episodes.semantic_tag IS 'auto_window | goal_X | scenario_Y';
COMMENT ON COLUMN core.metamind_episodes.boundary_reason IS 'Episode neden açıldı/kapandı';

-- Indexes for episodes
CREATE INDEX IF NOT EXISTS idx_metamind_episodes_run 
    ON core.metamind_episodes(run_id);
    
CREATE INDEX IF NOT EXISTS idx_metamind_episodes_time 
    ON core.metamind_episodes(start_time DESC);
    
CREATE INDEX IF NOT EXISTS idx_metamind_episodes_active 
    ON core.metamind_episodes(run_id) 
    WHERE end_cycle_id IS NULL;


-- ============================================================
-- TABLO 2: core.metamind_patterns
-- ============================================================
-- Pattern = Tespit edilen davranış örüntüleri
-- Types: action_sequence | action_frequency | emotion_trend | emotion_cycle | correlation

CREATE TABLE IF NOT EXISTS core.metamind_patterns (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    run_id          TEXT REFERENCES core.runs(run_id) ON DELETE CASCADE,
    episode_id      TEXT REFERENCES core.metamind_episodes(episode_id) ON DELETE SET NULL,
    pattern_type    TEXT NOT NULL
                    CHECK (pattern_type IN ('action_sequence', 'action_frequency', 
                           'emotion_trend', 'emotion_cycle', 'correlation')),
    pattern_key     TEXT NOT NULL,     -- e.g. "flee->wait->flee" or "danger>0.7->flee"
    frequency       INT NOT NULL DEFAULT 1,
    confidence      REAL NOT NULL DEFAULT 0.0
                    CHECK (confidence >= 0.0 AND confidence <= 1.0),
    first_seen      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data            JSONB DEFAULT '{}'
);

COMMENT ON TABLE core.metamind_patterns IS 'MetaMind tespit ettiği davranış pattern''leri';
COMMENT ON COLUMN core.metamind_patterns.pattern_key IS 'Pattern tanımlayıcı: flee->wait->flee';
COMMENT ON COLUMN core.metamind_patterns.confidence IS 'Pattern güvenilirlik skoru (0-1)';

-- Indexes for patterns
CREATE INDEX IF NOT EXISTS idx_metamind_patterns_type 
    ON core.metamind_patterns(pattern_type);
    
CREATE INDEX IF NOT EXISTS idx_metamind_patterns_run 
    ON core.metamind_patterns(run_id);
    
CREATE INDEX IF NOT EXISTS idx_metamind_patterns_episode 
    ON core.metamind_patterns(episode_id);
    
CREATE INDEX IF NOT EXISTS idx_metamind_patterns_key 
    ON core.metamind_patterns(pattern_key);
    
CREATE INDEX IF NOT EXISTS idx_metamind_patterns_frequency 
    ON core.metamind_patterns(frequency DESC);

-- Unique constraint: aynı pattern aynı run'da tekrar etmesin
CREATE UNIQUE INDEX IF NOT EXISTS idx_metamind_patterns_unique 
    ON core.metamind_patterns(run_id, pattern_type, pattern_key);


-- ============================================================
-- TABLO 3: core.metamind_meta_events
-- ============================================================
-- MetaEvent = Anomali, threshold ihlali, pattern tespiti olayları
-- Types: anomaly | threshold_breach | pattern_detected | episode_boundary | performance_warning

CREATE TABLE IF NOT EXISTS core.metamind_meta_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    run_id          TEXT REFERENCES core.runs(run_id) ON DELETE CASCADE,
    cycle_id        INT,
    episode_id      TEXT REFERENCES core.metamind_episodes(episode_id) ON DELETE SET NULL,
    event_type      TEXT NOT NULL
                    CHECK (event_type IN ('anomaly', 'threshold_breach', 'pattern_detected',
                           'episode_boundary', 'performance_warning')),
    severity        TEXT NOT NULL DEFAULT 'info'
                    CHECK (severity IN ('info', 'warning', 'critical')),
    source          TEXT NOT NULL,     -- "cycle_analyzer" | "pattern_miner" | "episode_manager"
    message         TEXT,
    data            JSONB DEFAULT '{}'
);

COMMENT ON TABLE core.metamind_meta_events IS 'MetaMind ürettiği meta-olaylar';
COMMENT ON COLUMN core.metamind_meta_events.source IS 'Olayı üreten modül';
COMMENT ON COLUMN core.metamind_meta_events.severity IS 'info | warning | critical';

-- Indexes for meta_events
CREATE INDEX IF NOT EXISTS idx_metamind_meta_events_type 
    ON core.metamind_meta_events(event_type);
    
CREATE INDEX IF NOT EXISTS idx_metamind_meta_events_severity 
    ON core.metamind_meta_events(severity);
    
CREATE INDEX IF NOT EXISTS idx_metamind_meta_events_run 
    ON core.metamind_meta_events(run_id);
    
CREATE INDEX IF NOT EXISTS idx_metamind_meta_events_cycle 
    ON core.metamind_meta_events(run_id, cycle_id);
    
CREATE INDEX IF NOT EXISTS idx_metamind_meta_events_time 
    ON core.metamind_meta_events(created_at DESC);

-- Partial index: sadece kritik olaylar
CREATE INDEX IF NOT EXISTS idx_metamind_meta_events_critical 
    ON core.metamind_meta_events(run_id, created_at DESC) 
    WHERE severity = 'critical';


-- ============================================================
-- TABLO 4: core.metamind_cycle_summary GÜNCELLEME
-- ============================================================
-- Mevcut tabloya MetaState kolonları ekleniyor
-- episode_id + 6 index değeri + 6 confidence değeri = 13 yeni kolon
-- ⚠️ Alice notu: Confidence kolonları kritik - erken dönemde düşük olacak

-- Episode ID bağlantısı
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'metamind_cycle_summary' 
        AND column_name = 'episode_id'
    ) THEN
        ALTER TABLE core.metamind_cycle_summary ADD COLUMN episode_id TEXT;
    END IF;
END $$;

-- 6 Meta-State Index Kolonları
DO $$ 
BEGIN
    -- global_cognitive_health
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'metamind_cycle_summary' 
        AND column_name = 'global_cognitive_health'
    ) THEN
        ALTER TABLE core.metamind_cycle_summary ADD COLUMN global_cognitive_health REAL;
    END IF;
    
    -- emotional_stability_index
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'metamind_cycle_summary' 
        AND column_name = 'emotional_stability_index'
    ) THEN
        ALTER TABLE core.metamind_cycle_summary ADD COLUMN emotional_stability_index REAL;
    END IF;
    
    -- ethical_alignment_index
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'metamind_cycle_summary' 
        AND column_name = 'ethical_alignment_index'
    ) THEN
        ALTER TABLE core.metamind_cycle_summary ADD COLUMN ethical_alignment_index REAL;
    END IF;
    
    -- exploration_bias_index
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'metamind_cycle_summary' 
        AND column_name = 'exploration_bias_index'
    ) THEN
        ALTER TABLE core.metamind_cycle_summary ADD COLUMN exploration_bias_index REAL;
    END IF;
    
    -- failure_pressure_index
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'metamind_cycle_summary' 
        AND column_name = 'failure_pressure_index'
    ) THEN
        ALTER TABLE core.metamind_cycle_summary ADD COLUMN failure_pressure_index REAL;
    END IF;
    
    -- memory_health_index
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'metamind_cycle_summary' 
        AND column_name = 'memory_health_index'
    ) THEN
        ALTER TABLE core.metamind_cycle_summary ADD COLUMN memory_health_index REAL;
    END IF;
END $$;

-- 6 Confidence Kolonları
DO $$ 
BEGIN
    -- global_health_confidence
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'metamind_cycle_summary' 
        AND column_name = 'global_health_confidence'
    ) THEN
        ALTER TABLE core.metamind_cycle_summary ADD COLUMN global_health_confidence REAL;
    END IF;
    
    -- emotional_stability_confidence
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'metamind_cycle_summary' 
        AND column_name = 'emotional_stability_confidence'
    ) THEN
        ALTER TABLE core.metamind_cycle_summary ADD COLUMN emotional_stability_confidence REAL;
    END IF;
    
    -- ethical_alignment_confidence
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'metamind_cycle_summary' 
        AND column_name = 'ethical_alignment_confidence'
    ) THEN
        ALTER TABLE core.metamind_cycle_summary ADD COLUMN ethical_alignment_confidence REAL;
    END IF;
    
    -- exploration_bias_confidence
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'metamind_cycle_summary' 
        AND column_name = 'exploration_bias_confidence'
    ) THEN
        ALTER TABLE core.metamind_cycle_summary ADD COLUMN exploration_bias_confidence REAL;
    END IF;
    
    -- failure_pressure_confidence
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'metamind_cycle_summary' 
        AND column_name = 'failure_pressure_confidence'
    ) THEN
        ALTER TABLE core.metamind_cycle_summary ADD COLUMN failure_pressure_confidence REAL;
    END IF;
    
    -- memory_health_confidence
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'metamind_cycle_summary' 
        AND column_name = 'memory_health_confidence'
    ) THEN
        ALTER TABLE core.metamind_cycle_summary ADD COLUMN memory_health_confidence REAL;
    END IF;
END $$;

-- Episode foreign key (soft - çünkü episode sonradan oluşabilir)
-- Foreign key constraint ekleme (eğer yoksa)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_metamind_summary_episode'
    ) THEN
        ALTER TABLE core.metamind_cycle_summary
        ADD CONSTRAINT fk_metamind_summary_episode
        FOREIGN KEY (episode_id) REFERENCES core.metamind_episodes(episode_id) ON DELETE SET NULL;
    END IF;
EXCEPTION
    WHEN others THEN
        -- Constraint zaten varsa veya başka hata, devam et
        NULL;
END $$;

-- Comments for new columns
COMMENT ON COLUMN core.metamind_cycle_summary.episode_id IS 'Cycle''ın ait olduğu episode';
COMMENT ON COLUMN core.metamind_cycle_summary.global_cognitive_health IS 'Genel bilişsel sağlık (0-1)';
COMMENT ON COLUMN core.metamind_cycle_summary.global_health_confidence IS 'global_cognitive_health güvenilirlik skoru';
COMMENT ON COLUMN core.metamind_cycle_summary.memory_health_index IS 'Hafıza sağlığı (⚠️ erken dönemde düşük confidence)';
COMMENT ON COLUMN core.metamind_cycle_summary.ethical_alignment_index IS 'Etik uyum (⚠️ erken dönemde düşük confidence)';


-- ============================================================
-- ADDITIONAL INDEXES FOR metamind_cycle_summary
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_metamind_summary_episode 
    ON core.metamind_cycle_summary(episode_id);
    
CREATE INDEX IF NOT EXISTS idx_metamind_summary_global_health 
    ON core.metamind_cycle_summary(global_cognitive_health);

CREATE INDEX IF NOT EXISTS idx_metamind_summary_failure_pressure 
    ON core.metamind_cycle_summary(failure_pressure_index DESC);

CREATE INDEX IF NOT EXISTS idx_metamind_summary_low_confidence
    ON core.metamind_cycle_summary(run_id, cycle_id)
    WHERE global_health_confidence < 0.5 
       OR memory_health_confidence < 0.5;


-- ============================================================
-- VERIFY MIGRATION
-- ============================================================

-- Bu query migration sonrası çalıştırılabilir
DO $$
DECLARE
    episode_count INT;
    pattern_count INT;
    event_count INT;
    new_columns INT;
BEGIN
    SELECT COUNT(*) INTO episode_count FROM core.metamind_episodes;
    SELECT COUNT(*) INTO pattern_count FROM core.metamind_patterns;
    SELECT COUNT(*) INTO event_count FROM core.metamind_meta_events;
    
    SELECT COUNT(*) INTO new_columns 
    FROM information_schema.columns 
    WHERE table_schema = 'core' 
    AND table_name = 'metamind_cycle_summary'
    AND column_name LIKE '%confidence%';
    
    RAISE NOTICE 'Migration completed:';
    RAISE NOTICE '  - metamind_episodes: % rows', episode_count;
    RAISE NOTICE '  - metamind_patterns: % rows', pattern_count;
    RAISE NOTICE '  - metamind_meta_events: % rows', event_count;
    RAISE NOTICE '  - New confidence columns: %', new_columns;
END $$;

COMMIT;

-- ============================================================
-- ROLLBACK SCRIPT (ayrı dosyada tutulabilir)
-- ============================================================
/*
BEGIN;

-- Yeni tabloları sil
DROP TABLE IF EXISTS core.metamind_meta_events CASCADE;
DROP TABLE IF EXISTS core.metamind_patterns CASCADE;
DROP TABLE IF EXISTS core.metamind_episodes CASCADE;

-- Yeni kolonları sil
ALTER TABLE core.metamind_cycle_summary DROP COLUMN IF EXISTS episode_id;
ALTER TABLE core.metamind_cycle_summary DROP COLUMN IF EXISTS global_cognitive_health;
ALTER TABLE core.metamind_cycle_summary DROP COLUMN IF EXISTS emotional_stability_index;
ALTER TABLE core.metamind_cycle_summary DROP COLUMN IF EXISTS ethical_alignment_index;
ALTER TABLE core.metamind_cycle_summary DROP COLUMN IF EXISTS exploration_bias_index;
ALTER TABLE core.metamind_cycle_summary DROP COLUMN IF EXISTS failure_pressure_index;
ALTER TABLE core.metamind_cycle_summary DROP COLUMN IF EXISTS memory_health_index;
ALTER TABLE core.metamind_cycle_summary DROP COLUMN IF EXISTS global_health_confidence;
ALTER TABLE core.metamind_cycle_summary DROP COLUMN IF EXISTS emotional_stability_confidence;
ALTER TABLE core.metamind_cycle_summary DROP COLUMN IF EXISTS ethical_alignment_confidence;
ALTER TABLE core.metamind_cycle_summary DROP COLUMN IF EXISTS exploration_bias_confidence;
ALTER TABLE core.metamind_cycle_summary DROP COLUMN IF EXISTS failure_pressure_confidence;
ALTER TABLE core.metamind_cycle_summary DROP COLUMN IF EXISTS memory_health_confidence;

COMMIT;
*/
