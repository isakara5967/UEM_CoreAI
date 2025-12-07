./
├── config/
│   ├── ethmor/
│   │   └── constraints_v0.yaml
│   ├── __init__.py
│   ├── core.yaml
│   ├── logging.yaml
│   └── metamind.yaml
├── core/
│   ├── cognition/
│   │   ├── conflict_resolution/
│   │   │   ├── __init__.py
│   │   │   └── conflict_resolution_unit.py
│   │   ├── evaluation/
│   │   │   ├── __init__.py
│   │   │   └── evaluation_unit.py
│   │   ├── inference/
│   │   │   ├── __init__.py
│   │   │   └── inference_unit.py
│   │   ├── internal_simulation/
│   │   │   ├── __init__.py
│   │   │   └── internal_simulation_unit.py
│   │   ├── intuition/
│   │   │   ├── __init__.py
│   │   │   └── intuition_unit.py
│   │   ├── meta_cognition/
│   │   │   ├── __init__.py
│   │   │   └── meta_cognition_unit.py
│   │   ├── __init__.py
│   │   └── cognition_core.py
│   ├── consciousness/
│   │   ├── __init__.py
│   │   ├── global_workspace.py
│   │   ├── global_workspace.py.bak
│   │   └── types.py
│   ├── emotion/
│   │   ├── integration/
│   │   │   ├── affective_state_integrator/
│   │   │   │   ├── __init__.py
│   │   │   │   └── affective_state_integrator.py
│   │   │   ├── emotion_pattern_classifier/
│   │   │   │   ├── __init__.py
│   │   │   │   └── emotion_pattern_classifier.py
│   │   │   ├── emotion_regulation_controller/
│   │   │   │   ├── __init__.py
│   │   │   │   └── emotion_regulation_controller.py
│   │   │   ├── ethmor_emotion_bridge/
│   │   │   │   ├── __init__.py
│   │   │   │   └── ethmor_emotion_bridge.py
│   │   │   ├── valence_arousal_model/
│   │   │   │   ├── __init__.py
│   │   │   │   └── valence_arousal_model.py
│   │   │   ├── __init__.py
│   │   │   └── integration_system.py
│   │   ├── personality/
│   │   │   ├── __init__.py
│   │   │   ├── chronic_stress_model.py
│   │   │   ├── personality_profile.py
│   │   │   └── resilience_model.py
│   │   ├── primitive/
│   │   │   ├── __init__.py
│   │   │   ├── attachment_system.py
│   │   │   ├── core_affect_system.py
│   │   │   ├── novelty_system.py
│   │   │   ├── pain_comfort_system.py
│   │   │   └── threat_safety_system.py
│   │   ├── __init__.py
│   │   ├── emotion_core.py
│   │   ├── emotion_core.py.bak
│   │   ├── predata_calculator.py
│   │   ├── somatic_event_handler.py
│   │   └── somatic_marker_system.py
│   ├── empathy/
│   │   ├── __init__.py
│   │   └── empathy_orchestrator.py
│   ├── ethmor/
│   │   ├── behavior_model/
│   │   │   ├── __init__.py
│   │   │   └── behavior_value_model.py
│   │   ├── context_engine/
│   │   │   ├── __init__.py
│   │   │   └── context_engine.py
│   │   ├── ethical_base/
│   │   │   ├── __init__.py
│   │   │   └── ethical_base.py
│   │   ├── moral_base/
│   │   │   ├── __init__.py
│   │   │   └── moral_base.py
│   │   ├── self_model/
│   │   │   ├── __init__.py
│   │   │   └── self_model_extension.py
│   │   ├── synthesis_engine/
│   │   │   ├── __init__.py
│   │   │   └── synthesis_engine.py
│   │   ├── __init__.py
│   │   ├── ethmor_system.py
│   │   ├── ethmor_system.py.bak
│   │   └── types.py
│   ├── logger/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── config_snapshots.py
│   │   ├── cycles.py
│   │   ├── db.py
│   │   ├── events.py
│   │   ├── experiments.py
│   │   ├── fallback.py
│   │   ├── logger.py
│   │   ├── runs.py
│   │   └── utils.py
│   ├── memory/
│   │   ├── consolidation/
│   │   │   ├── __init__.py
│   │   │   └── memory_consolidation.py
│   │   ├── emotional/
│   │   │   ├── __init__.py
│   │   │   └── emotional_memory.py
│   │   ├── episodic/
│   │   │   ├── __init__.py
│   │   │   └── episodic_memory.py
│   │   ├── long_term/
│   │   │   ├── __init__.py
│   │   │   └── long_term_memory.py
│   │   ├── semantic/
│   │   │   ├── __init__.py
│   │   │   └── semantic_memory.py
│   │   ├── short_term/
│   │   │   ├── __init__.py
│   │   │   └── short_term_memory.py
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── file_storage.py
│   │   │   ├── memory_storage.py
│   │   │   └── postgres_storage.py
│   │   ├── working/
│   │   │   ├── __init__.py
│   │   │   └── working_memory.py
│   │   ├── __init__.py
│   │   ├── ltm_manager.py
│   │   ├── memory_core.py
│   │   ├── memory_interface.py
│   │   ├── memory_interface.py.bak
│   │   └── types.py
│   ├── metamind/
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   └── metrics_adapter.py
│   │   ├── analyzers/
│   │   │   ├── __init__.py
│   │   │   ├── cycle_analyzer.py
│   │   │   └── pattern_miner.py
│   │   ├── evaluation/
│   │   │   ├── __init__.py
│   │   │   └── episode_evaluator.py
│   │   ├── insights/
│   │   │   ├── __init__.py
│   │   │   └── insight_generator.py
│   │   ├── metrics/
│   │   │   ├── alerts/
│   │   │   │   ├── __init__.py
│   │   │   │   └── manager.py
│   │   │   ├── clustering/
│   │   │   │   ├── __init__.py
│   │   │   │   └── behavior.py
│   │   │   ├── pattern/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── action.py
│   │   │   │   ├── failure.py
│   │   │   │   └── trend.py
│   │   │   ├── scoring/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── coherence.py
│   │   │   │   ├── efficiency.py
│   │   │   │   ├── quality.py
│   │   │   │   └── trust.py
│   │   │   └── __init__.py
│   │   ├── pipelines/
│   │   │   ├── __init__.py
│   │   │   ├── social.py
│   │   │   └── social.py.stub
│   │   ├── social/
│   │   │   ├── cognitive_empathy/
│   │   │   │   ├── __init__.py
│   │   │   │   └── unit.py
│   │   │   ├── emotional_empathy/
│   │   │   │   ├── __init__.py
│   │   │   │   └── unit.py
│   │   │   ├── ethical_filter/
│   │   │   │   ├── __init__.py
│   │   │   │   └── unit.py
│   │   │   ├── relational_mapping/
│   │   │   │   ├── __init__.py
│   │   │   │   └── unit.py
│   │   │   ├── social_context/
│   │   │   │   ├── __init__.py
│   │   │   │   └── unit.py
│   │   │   ├── social_simulation/
│   │   │   │   ├── __init__.py
│   │   │   │   └── unit.py
│   │   │   ├── state_prediction/
│   │   │   │   ├── __init__.py
│   │   │   │   └── unit.py
│   │   │   └── __init__.py
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   └── metamind_storage.py
│   │   ├── __init__.py
│   │   ├── __init__.py.bak
│   │   ├── core.py
│   │   ├── core.py.bak
│   │   ├── episodes.py
│   │   ├── episodes.py.bak
│   │   ├── meta_state.py
│   │   ├── metamind_core.py
│   │   └── types.py
│   ├── ontology/
│   │   ├── __init__.py
│   │   ├── grounding.py
│   │   ├── layer1.yaml
│   │   └── types.py
│   ├── perception/
│   │   ├── feature_extraction/
│   │   │   ├── __init__.py
│   │   │   └── feature_extractor.py
│   │   ├── noise_filter/
│   │   │   ├── __init__.py
│   │   │   └── noise_filter.py
│   │   ├── state/
│   │   │   ├── __init__.py
│   │   │   └── state_perception.py
│   │   ├── symbolic/
│   │   │   ├── __init__.py
│   │   │   └── symbolic_perception.py
│   │   ├── visual/
│   │   │   ├── __init__.py
│   │   │   └── visual_perception.py
│   │   ├── __init__.py
│   │   ├── perception_core.py
│   │   ├── predata_calculator.py
│   │   ├── types.py
│   │   └── types.py.bak
│   ├── planning/
│   │   ├── action_selection/
│   │   │   ├── __init__.py
│   │   │   ├── action_selector.py
│   │   │   ├── emotional_action_selector.py
│   │   │   └── somatic_action_selector.py
│   │   ├── goal_management/
│   │   │   ├── __init__.py
│   │   │   └── goal_manager.py
│   │   ├── rl_interface/
│   │   │   ├── __init__.py
│   │   │   └── rl_policy_interface.py
│   │   ├── strategy/
│   │   │   ├── __init__.py
│   │   │   └── strategy_engine.py
│   │   ├── task_decomposition/
│   │   │   ├── __init__.py
│   │   │   └── task_decomposer.py
│   │   ├── __init__.py
│   │   ├── emotion_aware_planning.py
│   │   ├── planner.py
│   │   ├── planner_v2.py
│   │   ├── planning_core.py
│   │   ├── planning_types.py
│   │   ├── predata_calculator.py
│   │   ├── types.py
│   │   └── types.py.bak
│   ├── predata/
│   │   ├── data_quality/
│   │   │   ├── __init__.py
│   │   │   ├── flags.py
│   │   │   ├── language.py
│   │   │   ├── modality.py
│   │   │   ├── noise.py
│   │   │   └── trust.py
│   │   ├── multi_agent/
│   │   │   ├── __init__.py
│   │   │   └── coordinator.py
│   │   ├── session/
│   │   │   ├── __init__.py
│   │   │   ├── clarity.py
│   │   │   ├── engagement.py
│   │   │   ├── experiment.py
│   │   │   ├── mode.py
│   │   │   └── stage.py
│   │   ├── tooling/
│   │   │   ├── __init__.py
│   │   │   ├── adversarial.py
│   │   │   ├── environment.py
│   │   │   ├── policy.py
│   │   │   └── tool_tracker.py
│   │   ├── __init__.py
│   │   ├── calculators.py
│   │   ├── collector.py
│   │   └── module_calculators.py
│   ├── self/
│   │   ├── continuity/
│   │   │   ├── __init__.py
│   │   │   └── unit.py
│   │   ├── drive_system/
│   │   │   ├── __init__.py
│   │   │   └── unit.py
│   │   ├── identity/
│   │   │   ├── __init__.py
│   │   │   └── unit.py
│   │   ├── integrity_monitor/
│   │   │   ├── __init__.py
│   │   │   └── unit.py
│   │   ├── reflection/
│   │   │   ├── __init__.py
│   │   │   └── unit.py
│   │   ├── schema/
│   │   │   ├── __init__.py
│   │   │   └── unit.py
│   │   ├── __init__.py
│   │   ├── self_core.py
│   │   ├── self_v2_memory_patch.py
│   │   └── types.py
│   ├── __init__.py
│   ├── event_bus.py
│   ├── integrated_uem_core.py
│   ├── logger_integration.py
│   ├── logging_utils.py
│   ├── state_vector.py
│   ├── uem_core.py
│   ├── unified_core.py
│   ├── unified_core.py.bak
│   ├── unified_types.py
│   └── unified_types.py.bak
├── data/
│   ├── fallback/
│   ├── test_storage/
│   └── __init__.py
├── demo_v0/
│   ├── scenarios/
│   │   ├── __init__.py
│   │   ├── exploration_scenario.py
│   │   ├── social_scenario.py
│   │   └── survival_scenario.py
│   ├── __init__.py
│   ├── demo_v0.py
│   ├── formatting.py
│   ├── outcome_simulator.py
│   ├── world_generator.py
│   └── world_state_builder.py
├── docker/
│   └── docker-compose.yml
├── docs/
│   └── status.md*
├── migrations/
│   ├── versions/
│   │   └── 001_initial_schema.py
│   ├── README
│   ├── env.py
│   └── script.py.mako
├── scenarios/
│   ├── combat_ambush.yaml
│   ├── combat_boss_fight.yaml
│   ├── mixed_village_day.yaml
│   ├── moral_rescue_choice.yaml
│   ├── moral_self_sacrifice.yaml
│   ├── quick_test_empathy.yaml
│   ├── scenario_runner.py
│   ├── social_betrayal.yaml
│   ├── social_trust_building.yaml
│   ├── survival_resource_scarcity.yaml
│   └── trauma_loss_grief.yaml
├── scripts/
│   └── __init__.py
├── sql/
│   ├── 001_create_schema.sql
│   ├── 002_create_tables.sql
│   ├── 003_create_indexes.sql
│   ├── 004_v5_migration_16d.sql
│   ├── 005_seed_metric_registry.sql
│   ├── 006_metamind_v1.9.sql
│   └── README.md
├── test_data/
├── tests/
│   ├── __init__.py
│   ├── run_empathy_tests.py
│   ├── run_memory_tests.py
│   ├── test_core_integration.py
│   ├── test_cycle_metrics.py
│   ├── test_e2e_conflict_scenarios.py
│   ├── test_e2e_db_persistence.py
│   ├── test_e2e_db_write.py
│   ├── test_e2e_edge_cases.py
│   ├── test_e2e_emotion_flow.py
│   ├── test_e2e_empathy_dynamics.py
│   ├── test_e2e_full_cycle.py
│   ├── test_e2e_multiagent_modes.py
│   ├── test_emotion_api.py
│   ├── test_emotion_planning_feedback.py
│   ├── test_empathy.py
│   ├── test_empathy_integration.py
│   ├── test_ethmor.py
│   ├── test_event_bus.py
│   ├── test_experiments.py
│   ├── test_logger_integration.py
│   ├── test_memory_interface.py
│   ├── test_metamind_v19_e2e.py
│   ├── test_multi_agent.py
│   ├── test_ontology_layer1.py
│   ├── test_perception_predata.py
│   ├── test_planning.py
│   ├── test_predata_calculators.py
│   ├── test_self_extended.py
│   ├── test_session.py
│   ├── test_somatic_event_handler.py
│   ├── test_somatic_marker.py
│   ├── test_state_vector_16d.py
│   ├── test_storage.py
│   ├── test_uem_analysis.py
│   ├── test_uem_logger.py
│   ├── test_uem_predata.py
│   ├── test_unified_core.py
│   └── test_workspace_integration.py
├── tests_e2e/
├── world/
│   ├── __init__.py
│   └── test_dummy_world.py
├── .env
├── .env.example
├── .gitignore
├── : Professional README with cognitive pipeline architecture"
├── LICENSE*
├── README.md
├── UEM_Project_Tree.md
├── alembic.ini
├── demo_emotion_planning.py
├── demo_global_workspace.py
├── demo_integrated_core.py
├── demo_memory_consolidation.py
├── demo_metamind_overnight.py
├── demo_ontology_layer1.py
├── demo_somatic_event_handler.py
├── demo_somatic_marker.py
├── demo_workspace_integration.py
├── e2e_tests_phase1.zip*
├── empathy_integration_patch.zip*
├── goal_overlap_v11_patch.zip*
├── h
├── main.py
├── memory_storage_16d_patch_v2.zip*
├── phase3_core_patch.py*
├── pytest.ini
├── requirements.txt
├── scenarios.zip*
├── state_vector_16d_patch.zip*
└── test_global_workspace.py

100 directories, 353 files
