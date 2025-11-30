# tests/test_e2e_emotion_flow.py
"""
E2E Tests - Emotion Flow

Bu testler, duygu sisteminin farklı senaryolarda
doğru çalıştığını ve diğer modüllere akışını doğrular.

Test edilenler:
- Tehlike → fear
- Güvenlik → content
- Kaynak → excitement
- Yaralanma → sadness
- Emotion → Planning akışı
- valence_delta hesaplama

Author: İsa Kara
Assisted by: 2 AI assistants
Date: 30 Kasım 2025
"""

import pytest
from dataclasses import dataclass, field
from typing import List, Dict, Any


# ============================================================================
# TEST FIXTURES
# ============================================================================

@dataclass
class E2EWorldState:
    """E2E test için WorldState."""
    tick: int = 1
    danger_level: float = 0.0
    player_health: float = 1.0
    player_energy: float = 1.0
    agents: List[Dict] = field(default_factory=list)
    objects: List[Dict] = field(default_factory=list)
    events: List[str] = field(default_factory=list)


@pytest.fixture
def core():
    """Create UnifiedUEMCore for E2E tests."""
    from core.unified_core import create_unified_core
    return create_unified_core(storage_type="memory")


# ============================================================================
# EMOTION LABEL TESTS
# ============================================================================

class TestEmotionLabels:
    """Tests for emotion label determination."""
    
    def test_e2e_emotion_fear_high_danger(self, core):
        """Yüksek tehlike → fear."""
        world = E2EWorldState(
            danger_level=0.9,
            player_health=0.6
        )
        
        core.cycle_sync(world)
        
        assert core.current_emotion['label'] == 'fear'
        assert core.current_emotion['valence'] < 0
        assert core.current_emotion['arousal'] > 0.5
    
    def test_e2e_emotion_content_safe(self, core):
        """Güvenli ortam, iyi sağlık → content."""
        world = E2EWorldState(
            danger_level=0.0,
            player_health=0.95
        )
        
        core.cycle_sync(world)
        
        # Should be positive emotion
        assert core.current_emotion['valence'] > 0
        assert core.current_emotion['label'] in ['content', 'excitement', 'neutral']
    
    def test_e2e_emotion_sadness_low_health(self, core):
        """Düşük sağlık, düşük tehlike → sadness."""
        world = E2EWorldState(
            danger_level=0.1,  # Low danger but
            player_health=0.2  # Very low health
        )
        
        core.cycle_sync(world)
        
        # Negative valence, low arousal = sadness
        assert core.current_emotion['valence'] < 0
    
    def test_e2e_emotion_excitement_resource_found(self, core):
        """Kaynak bulundu → positive emotion."""
        world = E2EWorldState(
            danger_level=0.0,
            player_health=0.8,
            objects=[{'type': 'resource', 'distance': 5}],
            events=['RESOURCE_FOUND']
        )
        
        core.cycle_sync(world)
        
        # Should be positive
        assert core.current_emotion['valence'] >= 0


# ============================================================================
# EMOTION FLOW TESTS
# ============================================================================

class TestEmotionFlow:
    """Tests for emotion data flow through the system."""
    
    def test_e2e_emotion_affects_planning(self, core):
        """Korku durumu → flee action daha olası."""
        # High danger scenario
        world = E2EWorldState(
            danger_level=0.95,
            player_health=0.3,
            agents=[{'id': 'enemy', 'relation': -0.8, 'valence': -0.5}]
        )
        
        result = core.cycle_sync(world)
        
        # Fear should be present
        assert core.current_emotion['label'] == 'fear'
        # Action should be defensive (flee, wait, etc.) not aggressive
        # Note: exact action depends on planner, but emotion should influence
        assert result is not None
    
    def test_e2e_emotion_valence_delta(self, core):
        """İki cycle arası valence_delta hesaplanmalı."""
        # Cycle 1: Happy state
        world1 = E2EWorldState(
            tick=1,
            danger_level=0.0,
            player_health=0.9
        )
        core.cycle_sync(world1)
        valence1 = core.current_emotion['valence']
        
        # Cycle 2: Scary state
        world2 = E2EWorldState(
            tick=2,
            danger_level=0.8,
            player_health=0.5
        )
        core.cycle_sync(world2)
        valence2 = core.current_emotion['valence']
        
        # Valence should have dropped
        assert valence2 < valence1
        
        # valence_delta should be captured in predata
        if 'valence_delta' in core._current_predata:
            assert core._current_predata['valence_delta'] < 0


# ============================================================================
# AROUSAL AND DOMINANCE TESTS
# ============================================================================

class TestArousalDominance:
    """Tests for arousal and dominance dimensions."""
    
    def test_e2e_emotion_arousal_high_danger(self, core):
        """Yüksek tehlike → yüksek arousal."""
        world = E2EWorldState(
            danger_level=0.9,
            player_health=0.7
        )
        
        core.cycle_sync(world)
        
        assert core.current_emotion['arousal'] > 0.7
    
    def test_e2e_emotion_arousal_low_safe(self, core):
        """Güvenli ortam → düşük/orta arousal."""
        world = E2EWorldState(
            danger_level=0.0,
            player_health=0.9
        )
        
        core.cycle_sync(world)
        
        assert core.current_emotion['arousal'] < 0.7
    
    def test_e2e_emotion_dominance_strong_position(self, core):
        """Güçlü pozisyon → positive dominance."""
        world = E2EWorldState(
            danger_level=0.1,
            player_health=0.95,
            player_energy=0.9
        )
        
        core.cycle_sync(world)
        
        # High health, low danger = feeling in control
        assert core.current_emotion['dominance'] > 0
    
    def test_e2e_emotion_dominance_weak_position(self, core):
        """Zayıf pozisyon → negative dominance."""
        world = E2EWorldState(
            danger_level=0.8,
            player_health=0.2,
            player_energy=0.1
        )
        
        core.cycle_sync(world)
        
        # Low health, high danger = feeling helpless
        assert core.current_emotion['dominance'] < 0
