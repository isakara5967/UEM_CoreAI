-- ============================================================
-- UEM_CoreAI PreData + Log System DDL
-- Version: 2.0 (v5 - 16D StateVector Update - 1 Aralık 2025)
-- Phase A - Step 5: Metric Registry Seed Data (52 Alan)
-- ============================================================

-- Mevcut kayıtları temizle
TRUNCATE TABLE core.metric_registry;

-- ============================================================
-- PERCEPTION (5 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('object_count', 'PreData.Core.Perception', 'Object Count', 'Algılanan nesne sayısı', 'int', 'v1.0', 'v1.9', 'perception', 'events.payload'),
('agent_count', 'PreData.Core.Perception', 'Agent Count', 'Algılanan ajan sayısı', 'int', 'v1.0', 'v1.9', 'perception', 'events.payload'),
('danger_level', 'PreData.Core.Perception', 'Danger Level', 'Tehlike seviyesi (0-1)', 'float', 'v1.0', 'v1.9', 'perception', 'events.payload'),
('symbol_list', 'PreData.Core.Perception', 'Symbol List', 'Algılanan semboller', 'json', 'v1.0', 'v1.9', 'perception', 'events.payload'),
('perception_confidence', 'PreData.Core.Perception', 'Perception Confidence', 'Algı güven skoru (0-1)', 'float', 'v1.0', 'v1.9', 'perception', 'events.payload');

-- ============================================================
-- EMOTION (4 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('valence', 'PreData.Core.Emotion', 'Valence', 'Duygu değeri (-1 to 1)', 'float', 'v1.0', 'v1.9', 'emotion', 'events.emotion_valence'),
('arousal', 'PreData.Core.Emotion', 'Arousal', 'Uyarılma seviyesi (0-1)', 'float', 'v1.0', 'v1.9', 'emotion', 'events.payload'),
('dominance', 'PreData.Core.Emotion', 'Dominance', 'Baskınlık seviyesi (-1 to 1)', 'float', 'v1.0', 'v1.9', 'emotion', 'events.payload'),
('emotion_label', 'PreData.Core.Emotion', 'Emotion Label', 'Sınıflandırılmış duygu etiketi', 'text', 'v1.0', 'v1.9', 'emotion', 'events.payload');

-- ============================================================
-- PLANNER (3 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('utility_breakdown', 'PreData.Core.Planner', 'Utility Breakdown', 'Utility bileşenleri', 'json', 'v1.0', 'v1.9', 'planner', 'events.payload'),
('candidate_plans', 'PreData.Core.Planner', 'Candidate Plans', 'Aday aksiyon listesi', 'json', 'v1.0', 'v1.9', 'planner', 'events.payload'),
('somatic_bias', 'PreData.Core.Planner', 'Somatic Bias', 'Somatik marker etkisi', 'float', 'v1.0', 'v1.9', 'planner', 'events.payload');

-- ============================================================
-- ETHMOR (5 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('ethmor_decision', 'PreData.Core.ETHMOR', 'ETHMOR Decision', 'Etik karar (ALLOW/FLAG/BLOCK)', 'text', 'v1.0', 'v1.9', 'ethmor', 'events.ethmor_decision'),
('triggered_rules', 'PreData.Core.ETHMOR', 'Triggered Rules', 'Tetiklenen etik kurallar', 'json', 'v1.0', 'v1.9', 'ethmor', 'events.payload'),
('risk_level', 'PreData.Core.ETHMOR', 'Risk Level', 'Etik risk seviyesi (0-1)', 'float', 'v1.0', 'v1.9', 'ethmor', 'events.payload'),
('intervention_type', 'PreData.Core.ETHMOR', 'Intervention Type', 'Müdahale tipi', 'text', 'v1.0', 'v1.9', 'ethmor', 'events.payload'),
('ethical_confidence', 'PreData.Core.ETHMOR', 'Ethical Confidence', 'Etik karar güveni (0-1)', 'float', 'v1.0', 'v1.9', 'ethmor', 'events.payload');

-- ============================================================
-- WORKSPACE (4 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('coalition_strength', 'PreData.Core.Workspace', 'Coalition Strength', 'Kazanan koalisyon gücü', 'float', 'v1.0', 'v1.9', 'workspace', 'events.payload'),
('broadcast_content', 'PreData.Core.Workspace', 'Broadcast Content', 'Yayınlanan bilinç içeriği', 'json', 'v1.0', 'v1.9', 'workspace', 'events.payload'),
('competition_intensity', 'PreData.Core.Workspace', 'Competition Intensity', 'Koalisyon rekabet yoğunluğu', 'float', 'v1.0', 'v1.9', 'workspace', 'events.payload'),
('conscious_threshold', 'PreData.Core.Workspace', 'Conscious Threshold', 'Bilinç eşik değeri', 'float', 'v1.0', 'v1.9', 'workspace', 'events.payload');

-- ============================================================
-- MEMORY (4 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('retrieval_count', 'PreData.Core.Memory', 'Retrieval Count', 'Getirilen anı sayısı', 'int', 'v1.0', 'v1.9', 'memory', 'events.payload'),
('memory_relevance', 'PreData.Core.Memory', 'Memory Relevance', 'Anı ilgililik skoru', 'float', 'v1.0', 'v1.9', 'memory', 'events.payload'),
('consolidation_flag', 'PreData.Core.Memory', 'Consolidation Flag', 'Konsolidasyon durumu', 'bool', 'v1.0', 'v1.9', 'memory', 'events.payload'),
('ltm_write_count', 'PreData.Core.Memory', 'LTM Write Count', 'Uzun süreli belleğe yazılan', 'int', 'v1.0', 'v1.9', 'memory', 'events.payload');

-- ============================================================
-- SELF (2 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('self_state_vector', 'PreData.Core.Self', 'Self State Vector', '16D benlik durumu vektörü', 'json', 'v1.0', 'v1.9', 'self', 'events.payload'),
('confidence_score', 'PreData.Core.Self', 'Confidence Score', 'Öz-güven skoru (0-1)', 'float', 'v1.0', 'v1.9', 'self', 'events.payload');

-- ============================================================
-- DATA QUALITY (6 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('input_modality_mix', 'PreData.Extension.DataQuality', 'Input Modality Mix', 'Girdi modalite karışımı', 'json', 'v1.0', 'v1.9', 'data_quality', 'events.payload'),
('input_noise_level', 'PreData.Extension.DataQuality', 'Input Noise Level', 'Girdi gürültü seviyesi', 'float', 'v1.0', 'v1.9', 'data_quality', 'events.payload'),
('source_trust_score', 'PreData.Extension.DataQuality', 'Source Trust Score', 'Kaynak güven skoru', 'float', 'v1.0', 'v1.9', 'data_quality', 'events.payload'),
('data_quality_flags', 'PreData.Extension.DataQuality', 'Data Quality Flags', 'Kalite uyarı bayrakları', 'json', 'v1.0', 'v1.9', 'data_quality', 'events.payload'),
('input_language', 'PreData.Extension.DataQuality', 'Input Language', 'Girdi dili', 'text', 'v1.0', 'v1.9', 'data_quality', 'events.input_language'),
('output_language', 'PreData.Extension.DataQuality', 'Output Language', 'Çıktı dili', 'text', 'v1.0', 'v1.9', 'data_quality', 'events.output_language');

-- ============================================================
-- SESSION (6 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('session_stage', 'PreData.Extension.Session', 'Session Stage', 'Oturum aşaması', 'text', 'v1.0', 'v1.9', 'session', 'events.payload'),
('user_goal_clarity', 'PreData.Extension.Session', 'User Goal Clarity', 'Kullanıcı hedef netliği', 'float', 'v1.0', 'v1.9', 'session', 'events.payload'),
('interaction_mode', 'PreData.Extension.Session', 'Interaction Mode', 'Etkileşim modu', 'text', 'v1.0', 'v1.9', 'session', 'events.payload'),
('user_engagement_level', 'PreData.Extension.Session', 'User Engagement Level', 'Kullanıcı katılım seviyesi', 'text', 'v1.0', 'v1.9', 'session', 'events.payload'),
('experiment_tag', 'PreData.Extension.Session', 'Experiment Tag', 'Deney etiketi', 'text', 'v1.0', 'v1.9', 'session', 'events.payload'),
('ab_bucket', 'PreData.Extension.Session', 'A/B Bucket', 'A/B test grubu', 'text', 'v1.0', 'v1.9', 'session', 'events.payload');

-- ============================================================
-- TOOLING (5 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('tool_usage_summary', 'PreData.Extension.Tooling', 'Tool Usage Summary', 'Araç kullanım özeti', 'json', 'v1.0', 'v1.9', 'tooling', 'events.payload'),
('environment_profile', 'PreData.Extension.Tooling', 'Environment Profile', 'Ortam profili', 'json', 'v1.0', 'v1.9', 'tooling', 'events.payload'),
('policy_set_id', 'PreData.Extension.Tooling', 'Policy Set ID', 'Politika seti kimliği', 'text', 'v1.0', 'v1.9', 'tooling', 'events.payload'),
('policy_conflict_score', 'PreData.Extension.Tooling', 'Policy Conflict Score', 'Politika çatışma skoru', 'float', 'v1.0', 'v1.9', 'tooling', 'events.payload'),
('adversarial_input_score', 'PreData.Extension.Tooling', 'Adversarial Input Score', 'Düşmanca girdi skoru', 'float', 'v1.0', 'v1.9', 'tooling', 'events.payload');

-- ============================================================
-- MULTI-AGENT (4 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('empathy_score', 'PreData.Extension.MultiAgent', 'Empathy Score', 'Empati skoru (0-1)', 'float', 'v1.0', 'v1.9', 'empathy', 'events.payload'),
('ma_agent_count', 'PreData.Extension.MultiAgent', 'MA Agent Count', 'Çoklu ajan sayısı', 'int', 'v1.0', 'v1.9', 'empathy', 'events.payload'),
('ma_coordination_mode', 'PreData.Extension.MultiAgent', 'MA Coordination Mode', 'Koordinasyon modu', 'text', 'v1.0', 'v1.9', 'empathy', 'events.payload'),
('ma_conflict_score', 'PreData.Extension.MultiAgent', 'MA Conflict Score', 'Çatışma skoru (0-1)', 'float', 'v1.0', 'v1.9', 'empathy', 'events.payload');

-- ============================================================
-- DERIVED (4 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('action_name', 'PreData.Derived', 'Action Name', 'Seçilen aksiyon', 'text', 'v1.0', 'v1.9', 'execution', 'events.action_name'),
('action_success', 'PreData.Derived', 'Action Success', 'Aksiyon başarı durumu', 'bool', 'v1.0', 'v1.9', 'execution', 'events.success_flag_explicit'),
('cycle_time_ms', 'PreData.Derived', 'Cycle Time (ms)', 'Cycle süresi', 'float', 'v1.0', 'v1.9', 'execution', 'events.cycle_time_ms'),
('causal_factors', 'PreData.Derived', 'Causal Factors', 'Nedensel faktörler', 'json', 'v1.0', 'v1.9', 'execution', 'events.payload');

-- ============================================================
-- DOĞRULAMA
-- ============================================================
DO $$
DECLARE
    total_count INT;
BEGIN
    SELECT COUNT(*) INTO total_count FROM core.metric_registry;
    RAISE NOTICE 'Toplam metrik sayısı: % (beklenen: 52)', total_count;
    
    IF total_count != 52 THEN
        RAISE WARNING 'Metrik sayısı 52 değil!';
    END IF;
END $$;
