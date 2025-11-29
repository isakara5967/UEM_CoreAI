-- ============================================================
-- UEM_CoreAI PreData + Log System
-- Phase A - Step 6: Seed metric_registry (51 PreData Fields)
-- ============================================================

-- ============================================================
-- KATMAN 1: CORE COGNITIVE (27 alan)
-- ============================================================

-- Planner (3 alan)
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('utility_breakdown', 'PreData.Core.Planner', 'Utility Breakdown', 'Seçilen aksiyonun fayda fonksiyonu bileşenleri', 'json', 'v1.0', 'v1.9', 'planner', 'events.payload'),
('candidate_plans', 'PreData.Core.Planner', 'Candidate Plans', 'Değerlendirilen alternatif planlar', 'json', 'v1.0', 'v1.9', 'planner', 'events.payload'),
('somatic_bias', 'PreData.Core.Planner', 'Somatic Bias', 'Somatik marker kaynaklı karar yanlılığı', 'float', 'v1.0', 'v1.9', 'planner', 'events.payload');

-- ETHMOR (4 alan)
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('triggered_rules', 'PreData.Core.ETHMOR', 'Triggered Rules', 'Tetiklenen etik kuralları listesi', 'array', 'v1.0', 'v1.9', 'ethmor', 'events.payload'),
('risk_level', 'PreData.Core.ETHMOR', 'Risk Level', 'Hesaplanan risk seviyesi', 'float', 'v1.0', 'v1.9', 'ethmor', 'events.payload'),
('intervention_type', 'PreData.Core.ETHMOR', 'Intervention Type', 'Müdahale tipi (none/modify/block)', 'enum', 'v1.0', 'v1.9', 'ethmor', 'events.payload'),
('ethical_confidence', 'PreData.Core.ETHMOR', 'Ethical Confidence', 'Etik karar güveni', 'float', 'v1.0', 'v1.9', 'ethmor', 'events.payload');

-- Emotion (5 alan)
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('engagement', 'PreData.Core.Emotion', 'Engagement', 'Duygusal bağlılık seviyesi', 'float', 'v1.0', 'v1.9', 'emotion', 'events.payload'),
('valence_delta', 'PreData.Core.Emotion', 'Valence Delta', 'Valence değişim miktarı', 'float', 'v1.0', 'v1.9', 'emotion', 'events.payload'),
('arousal_volatility', 'PreData.Core.Emotion', 'Arousal Volatility', 'Arousal dalgalanma oranı', 'float', 'v1.0', 'v1.9', 'emotion', 'events.payload'),
('emotion_label', 'PreData.Core.Emotion', 'Emotion Label', 'Sınıflandırılmış duygu etiketi', 'text', 'v1.0', 'v1.9', 'emotion', 'events.emotion_valence'),
('mood_baseline', 'PreData.Core.Emotion', 'Mood Baseline', 'Uzun vadeli mood ortalaması', 'float', 'v1.0', 'v1.9', 'emotion', 'events.payload');

-- Perception (5 alan)
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('novelty_score', 'PreData.Core.Perception', 'Novelty Score', 'Girdi yenilik skoru', 'float', 'v1.0', 'v1.9', 'perception', 'events.payload'),
('salience_map', 'PreData.Core.Perception', 'Salience Map', 'Dikkat öncelik haritası', 'json', 'v1.0', 'v1.9', 'perception', 'events.payload'),
('temporal_context', 'PreData.Core.Perception', 'Temporal Context', 'Zamansal bağlam bilgisi', 'json', 'v1.0', 'v1.9', 'perception', 'events.payload'),
('attention_focus', 'PreData.Core.Perception', 'Attention Focus', 'Mevcut dikkat odağı', 'text', 'v1.0', 'v1.9', 'perception', 'events.payload'),
('perception_confidence', 'PreData.Core.Perception', 'Perception Confidence', 'Algı güven skoru', 'float', 'v1.0', 'v1.9', 'perception', 'events.payload');

-- Workspace (4 alan)
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('coalition_strength', 'PreData.Core.Workspace', 'Coalition Strength', 'Kazanan koalisyon gücü', 'float', 'v1.0', 'v1.9', 'workspace', 'events.payload'),
('broadcast_content', 'PreData.Core.Workspace', 'Broadcast Content', 'Yayınlanan bilinç içeriği', 'json', 'v1.0', 'v1.9', 'workspace', 'events.payload'),
('competition_intensity', 'PreData.Core.Workspace', 'Competition Intensity', 'Koalisyon rekabet yoğunluğu', 'float', 'v1.0', 'v1.9', 'workspace', 'events.payload'),
('conscious_threshold', 'PreData.Core.Workspace', 'Conscious Threshold', 'Bilinç eşik değeri', 'float', 'v1.0', 'v1.9', 'workspace', 'events.payload');

-- Memory (3 alan)
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('retrieval_count', 'PreData.Core.Memory', 'Retrieval Count', 'Hafızadan çekilen kayıt sayısı', 'int', 'v1.0', 'v1.9', 'memory', 'events.payload'),
('memory_relevance', 'PreData.Core.Memory', 'Memory Relevance', 'Çekilen anıların ortalama ilgililiği', 'float', 'v1.0', 'v1.9', 'memory', 'events.payload'),
('consolidation_flag', 'PreData.Core.Memory', 'Consolidation Flag', 'Konsolidasyon tetiklendi mi', 'boolean', 'v1.0', 'v1.9', 'memory', 'events.payload');

-- Self (3 alan)
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('self_state_vector', 'PreData.Core.Self', 'Self State Vector', 'Öz-durum vektörü (energy, health, etc)', 'json', 'v1.0', 'v1.9', 'self', 'events.payload'),
('goal_progress', 'PreData.Core.Self', 'Goal Progress', 'Aktif hedeflere ilerleme', 'json', 'v1.0', 'v1.9', 'self', 'events.payload'),
('introspection_depth', 'PreData.Core.Self', 'Introspection Depth', 'Öz-değerlendirme derinliği', 'int', 'v1.0', 'v1.9', 'self', 'events.payload');

-- ============================================================
-- KATMAN 2: DATA QUALITY (6 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('input_modality_mix', 'PreData.DataQuality', 'Input Modality Mix', 'Girdi modalite dağılımı (text/image/audio)', 'json', 'v1.0', 'v1.9', 'perception', 'events.payload'),
('input_noise_level', 'PreData.DataQuality', 'Input Noise Level', 'Girdi gürültü seviyesi tahmini', 'float', 'v1.0', 'v1.9', 'perception', 'events.payload'),
('source_trust_score', 'PreData.DataQuality', 'Source Trust Score', 'Kaynak güvenilirlik skoru', 'float', 'v1.0', 'v1.9', 'perception', 'events.payload'),
('data_quality_flags', 'PreData.DataQuality', 'Data Quality Flags', 'Veri kalitesi uyarı bayrakları', 'array', 'v1.0', 'v1.9', 'perception', 'events.payload'),
('input_language', 'PreData.DataQuality', 'Input Language', 'Tespit edilen girdi dili (ISO 639-1)', 'text', 'v1.0', 'v1.9', 'perception', 'events.input_language'),
('output_language', 'PreData.DataQuality', 'Output Language', 'Çıktı dili (ISO 639-1)', 'text', 'v1.0', 'v1.9', 'execution', 'events.output_language');

-- ============================================================
-- KATMAN 3: USER/SESSION (6 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('session_stage', 'PreData.UserSession', 'Session Stage', 'Oturum aşaması (early/mid/late)', 'enum', 'v1.0', 'v1.9', 'self', 'runs.summary'),
('user_goal_clarity', 'PreData.UserSession', 'User Goal Clarity', 'Kullanıcı hedef netliği skoru', 'float', 'v1.0', 'v1.9', 'self', 'events.payload'),
('interaction_mode', 'PreData.UserSession', 'Interaction Mode', 'Etkileşim modu (chat/task/explore)', 'enum', 'v1.0', 'v1.9', 'perception', 'events.payload'),
('user_engagement_level', 'PreData.UserSession', 'User Engagement Level', 'Kullanıcı katılım seviyesi', 'enum', 'v1.0', 'v1.9', 'self', 'events.payload'),
('experiment_tag', 'PreData.UserSession', 'Experiment Tag', 'Deney etiketi', 'text', 'v1.0', 'v1.9', 'metamind', 'runs.experiment_id'),
('ab_bucket', 'PreData.UserSession', 'A/B Bucket', 'A/B test kovası', 'text', 'v1.0', 'v1.9', 'metamind', 'runs.ab_bucket');

-- ============================================================
-- KATMAN 4: TOOLING/ENVIRONMENT (5 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('tool_usage_summary', 'PreData.Tooling', 'Tool Usage Summary', 'Kullanılan araçların özeti', 'json', 'v1.0', 'v1.9', 'execution', 'events.payload'),
('environment_profile', 'PreData.Tooling', 'Environment Profile', 'Çalışma ortamı profili', 'json', 'v1.0', 'v1.9', 'metamind', 'runs.environment_profile'),
('policy_set_id', 'PreData.Tooling', 'Policy Set ID', 'Aktif politika seti', 'text', 'v1.0', 'v1.9', 'ethmor', 'config_snapshots.policy_set_id'),
('policy_conflict_score', 'PreData.Tooling', 'Policy Conflict Score', 'Politika çakışma skoru', 'float', 'v1.0', 'v1.9', 'ethmor', 'events.payload'),
('adversarial_input_score', 'PreData.Tooling', 'Adversarial Input Score', 'Düşmanca girdi tespit skoru', 'float', 'v1.0', 'v1.9', 'perception', 'events.payload');

-- ============================================================
-- KATMAN 5: MULTI-AGENT PLACEHOLDER (3 alan)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('ma_agent_count', 'PreData.MultiAgent', 'Agent Count', 'Aktif agent sayısı', 'int', 'v1.0', 'v2.0', 'metamind', 'events.payload'),
('ma_coordination_mode', 'PreData.MultiAgent', 'Coordination Mode', 'Koordinasyon modu (solo/collab/compete)', 'enum', 'v1.0', 'v2.0', 'metamind', 'events.payload'),
('ma_conflict_score', 'PreData.MultiAgent', 'Conflict Score', 'Agent arası çakışma skoru', 'float', 'v1.0', 'v2.0', 'metamind', 'events.payload');

-- ============================================================
-- EXECUTION METRICS (4 alan - ek)
-- ============================================================
INSERT INTO core.metric_registry (metric_id, metric_group, display_name, description, value_type, version, introduced_in, owner_module, log_location) VALUES
('action_name', 'PreData.Execution', 'Action Name', 'Seçilen aksiyon adı', 'text', 'v1.0', 'v1.9', 'planner', 'events.action_name'),
('action_success', 'PreData.Execution', 'Action Success', 'Aksiyon başarılı mı', 'boolean', 'v1.0', 'v1.9', 'execution', 'events.success_flag_explicit'),
('cycle_time_ms', 'PreData.Execution', 'Cycle Time', 'Cycle süresi (ms)', 'float', 'v1.0', 'v1.9', 'metamind', 'events.cycle_time_ms'),
('causal_factors', 'PreData.Execution', 'Causal Factors', 'Sonucu etkileyen faktörler', 'array', 'v1.0', 'v1.9', 'metamind', 'events.payload');

-- Verify count
SELECT COUNT(*) as total_metrics, metric_group, COUNT(*) as group_count 
FROM core.metric_registry 
GROUP BY metric_group 
ORDER BY metric_group;
