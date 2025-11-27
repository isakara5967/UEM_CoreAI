"""Sprint 0A-Fix: Emotion API Standardization Tests"""
import pytest


class TestEmotionAPIStandard:
    """Test emotion state structure and API alignment."""

    def test_emotion_state_structure(self):
        """Test that emotion_state has required keys: valence, arousal, label."""
        from core.unified_core import create_unified_core
        from core.integrated_uem_core import WorldState
        
        core = create_unified_core()
        
        # Create test world
        world = WorldState(
            tick=1,
            danger_level=0.2,
            player_health=0.8,
            player_energy=0.7,
            symbols=['FOUND_WATER'],
        )
        
        # Run cycle
        core.cycle_sync(world)
        
        # Check emotion structure
        emotion = core.current_emotion
        assert emotion is not None, "current_emotion should not be None"
        assert "valence" in emotion, "emotion must have 'valence'"
        assert "arousal" in emotion, "emotion must have 'arousal'"
        assert "label" in emotion, "emotion must have 'label'"
        
        # Check types
        assert isinstance(emotion["valence"], float), "valence must be float"
        assert isinstance(emotion["arousal"], float), "arousal must be float"
        assert isinstance(emotion["label"], str), "label must be string"
        
        # Check ranges
        assert -1.0 <= emotion["valence"] <= 1.0, "valence must be in [-1, 1]"
        assert 0.0 <= emotion["arousal"] <= 1.0, "arousal must be in [0, 1]"

    def test_emotion_demo_api_alignment(self):
        """Test that Demo can read emotion using standardized API."""
        from core.unified_core import create_unified_core
        from core.integrated_uem_core import WorldState
        
        core = create_unified_core()
        
        # Simulate what demo does
        world = WorldState(
            tick=1,
            danger_level=0.5,
            player_health=0.6,
            player_energy=0.5,
            symbols=['ENEMY_APPEARED'],
        )
        
        core.cycle_sync(world)
        
        # Demo reads emotion like this:
        emotion = {"valence": 0.0, "arousal": 0.5, "label": "neutral"}
        if hasattr(core, 'current_emotion') and core.current_emotion:
            emotion = core.current_emotion.copy()
        
        # Validation with fallback
        if "label" not in emotion:
            emotion["label"] = "neutral"
        
        # Should work without fallback
        assert "label" in core.current_emotion, "Core should provide 'label' directly"
        assert emotion["label"] != "neutral" or emotion["valence"] == 0.0, \
            "Non-neutral valence should produce non-neutral label"

    def test_emotion_label_variety(self):
        """Test that different scenarios produce different emotion labels."""
        from core.unified_core import create_unified_core
        from core.integrated_uem_core import WorldState
        
        core = create_unified_core()
        labels_seen = set()
        
        scenarios = [
            # (danger, health, energy, symbols)
            (0.0, 1.0, 1.0, ['SAFE']),           # Should be positive
            (0.8, 0.3, 0.5, ['ENEMY_APPEARED']), # Should be negative/fear
            (0.1, 0.9, 0.9, ['FOUND_TREASURE']), # Should be positive/joy
            (0.0, 0.5, 0.5, []),                 # Should be neutral
        ]
        
        for danger, health, energy, symbols in scenarios:
            world = WorldState(
                tick=1,
                danger_level=danger,
                player_health=health,
                player_energy=energy,
                symbols=symbols,
            )
            core.cycle_sync(world)
            labels_seen.add(core.current_emotion["label"])
        
        # Should see at least 2 different labels
        assert len(labels_seen) >= 2, f"Expected variety, got only: {labels_seen}"
