-- ============================================================
-- UEM_CoreAI v5 Migration Script
-- Version: 2.0 (16D StateVector Update - 1 Aralık 2025)
-- 
-- BU SCRIPT: v4'ten v5'e geçiş için kullanılır
-- DEĞİŞİKLİKLER:
--   - public.events: state_before, state_after eklendi (16D)
--   - public.events: emotion_valence, emotion_arousal kaldırıldı
--   - public.events: effect 8D → 16D
--   - public.snapshots: state_vector 8D → 16D
-- ============================================================

-- ============================================================
-- BÖLÜM 1: public.events tablosu güncellemesi
-- ============================================================

-- 1.1 Yeni kolonları ekle (16D vectors)
ALTER TABLE public.events 
    ADD COLUMN IF NOT EXISTS state_before vector(16);

ALTER TABLE public.events 
    ADD COLUMN IF NOT EXISTS state_after vector(16);

-- 1.2 Eski kolonları kaldır (artık 16D vektörlerde)
-- NOT: Mevcut veri kaybı olabilir, backup alın!
ALTER TABLE public.events 
    DROP COLUMN IF EXISTS emotion_valence;

ALTER TABLE public.events 
    DROP COLUMN IF EXISTS emotion_arousal;

-- 1.3 effect kolonunu güncelle (8D → 16D)
-- Mevcut 8D verileri 16D'ye padding ile genişlet
DO $$
DECLARE
    has_old_effect BOOLEAN;
BEGIN
    -- Eğer eski 8D effect varsa
    SELECT EXISTS (
        SELECT 1 FROM public.events 
        WHERE effect IS NOT NULL 
        AND array_length(effect::real[], 1) = 8
        LIMIT 1
    ) INTO has_old_effect;
    
    IF has_old_effect THEN
        -- Geçici kolon oluştur
        ALTER TABLE public.events ADD COLUMN IF NOT EXISTS effect_new vector(16);
        
        -- 8D → 16D padding (8 sıfır ekle)
        UPDATE public.events 
        SET effect_new = (
            SELECT array_to_string(
                array_cat(
                    string_to_array(effect::text, ',')::real[],
                    ARRAY[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]::real[]
                ), ','
            )::vector(16)
        )
        WHERE effect IS NOT NULL;
        
        -- Eski kolonu kaldır, yeniyi eski isimle değiştir
        ALTER TABLE public.events DROP COLUMN effect;
        ALTER TABLE public.events RENAME COLUMN effect_new TO effect;
        
        RAISE NOTICE 'public.events.effect: 8D → 16D migration tamamlandı';
    END IF;
END $$;

-- ============================================================
-- BÖLÜM 2: public.snapshots tablosu güncellemesi
-- ============================================================

-- 2.1 state_vector 8D → 16D
DO $$
DECLARE
    has_old_vector BOOLEAN;
BEGIN
    -- Eğer eski 8D state_vector varsa
    SELECT EXISTS (
        SELECT 1 FROM public.snapshots 
        WHERE state_vector IS NOT NULL 
        AND array_length(state_vector::real[], 1) = 8
        LIMIT 1
    ) INTO has_old_vector;
    
    IF has_old_vector THEN
        -- Geçici kolon oluştur
        ALTER TABLE public.snapshots ADD COLUMN IF NOT EXISTS state_vector_new vector(16);
        
        -- 8D → 16D padding
        UPDATE public.snapshots 
        SET state_vector_new = (
            SELECT array_to_string(
                array_cat(
                    string_to_array(state_vector::text, ',')::real[],
                    ARRAY[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]::real[]
                ), ','
            )::vector(16)
        )
        WHERE state_vector IS NOT NULL;
        
        -- Eski kolonu kaldır, yeniyi eski isimle değiştir
        ALTER TABLE public.snapshots DROP COLUMN state_vector;
        ALTER TABLE public.snapshots RENAME COLUMN state_vector_new TO state_vector;
        
        -- NOT NULL constraint ekle
        ALTER TABLE public.snapshots ALTER COLUMN state_vector SET NOT NULL;
        
        RAISE NOTICE 'public.snapshots.state_vector: 8D → 16D migration tamamlandı';
    END IF;
END $$;

-- ============================================================
-- BÖLÜM 3: Vector index'lerini yeniden oluştur
-- ============================================================

-- Eski index'i kaldır (varsa)
DROP INDEX IF EXISTS idx_snapshots_vector;
DROP INDEX IF EXISTS idx_public_snapshots_vector;

-- Yeni 16D vector index oluştur
CREATE INDEX IF NOT EXISTS idx_public_snapshots_vector 
    ON public.snapshots USING ivfflat (state_vector vector_l2_ops) 
    WITH (lists = 100);

-- ============================================================
-- BÖLÜM 4: Yeni index'ler ekle
-- ============================================================

-- state_before/state_after için index (opsiyonel, büyük tablolar için)
-- CREATE INDEX IF NOT EXISTS idx_public_events_state_before 
--     ON public.events USING ivfflat (state_before vector_l2_ops) 
--     WITH (lists = 100);

-- ============================================================
-- BÖLÜM 5: Doğrulama
-- ============================================================

DO $$
DECLARE
    events_count INT;
    snapshots_count INT;
    effect_dim INT;
    vector_dim INT;
BEGIN
    SELECT COUNT(*) INTO events_count FROM public.events;
    SELECT COUNT(*) INTO snapshots_count FROM public.snapshots;
    
    -- Dimension kontrolü
    SELECT array_length(effect::real[], 1) INTO effect_dim 
    FROM public.events WHERE effect IS NOT NULL LIMIT 1;
    
    SELECT array_length(state_vector::real[], 1) INTO vector_dim 
    FROM public.snapshots WHERE state_vector IS NOT NULL LIMIT 1;
    
    RAISE NOTICE '=== v5 Migration Özeti ===';
    RAISE NOTICE 'public.events: % kayıt', events_count;
    RAISE NOTICE 'public.snapshots: % kayıt', snapshots_count;
    RAISE NOTICE 'effect dimension: %D', COALESCE(effect_dim, 16);
    RAISE NOTICE 'state_vector dimension: %D', COALESCE(vector_dim, 16);
    RAISE NOTICE '========================';
END $$;

-- ============================================================
-- AÇIKLAMALAR
-- ============================================================

COMMENT ON TABLE public.events IS 'Episodic Memory (v5) - 16D vectors: state_before, effect, state_after';
COMMENT ON TABLE public.snapshots IS 'State Snapshots (v5) - 16D state_vector';

COMMENT ON COLUMN public.events.state_before IS 'v5: Cycle başında 16D state vector';
COMMENT ON COLUMN public.events.state_after IS 'v5: Cycle sonunda 16D state vector';
COMMENT ON COLUMN public.events.effect IS 'v5: 16D aksiyon etkisi (state_before + effect = state_after)';
