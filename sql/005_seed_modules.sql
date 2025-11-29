-- ============================================================
-- UEM_CoreAI PreData + Log System
-- Phase A - Step 5: Seed Modules Data
-- ============================================================

-- Core modules
INSERT INTO core.modules (name, description) VALUES
    ('perception', 'Girdi işleme ve yenilik tespiti'),
    ('workspace', 'Global Workspace ve bilinç'),
    ('memory', 'Hafıza erişimi'),
    ('self', 'Öz-değerlendirme'),
    ('emotion', 'Duygu durumu'),
    ('empathy', 'Sosyal biliş'),
    ('planner', 'Aksiyon planlama'),
    ('ethmor', 'Etik değerlendirme'),
    ('execution', 'Aksiyon yürütme'),
    ('learning', 'Öğrenme'),
    ('metamind', 'Üst-biliş')
ON CONFLICT (name) DO NOTHING;

-- Verify
SELECT module_id, name, description FROM core.modules ORDER BY module_id;
