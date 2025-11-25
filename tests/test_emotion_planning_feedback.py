"""
Tests for Emotion → Planning Feedback Loop

Test scenarios:
1. Fear state → lower danger threshold → earlier escape
2. Excitement state → higher danger threshold → risk taking
3. Anger state → confrontation behavior
4. Calm state → careful decision making
"""

import pytest
import sys
from dataclasses import dataclass
from typing import Any

# Path setup
sys.path.insert(0, '/home/claude/uem_project')

from core.planning.action_selection.emotional_action_selector import (
    EmotionalActionSelector,
    EmotionalState,
    WorkingMemoryState,
    ActionCommand,
)


@dataclass
class MockTarget:
    id: str = "target_1"
    distance: float = 5.0
    obj_type: str = "box"


class TestEmotionalActionSelector:
    """EmotionalActionSelector unit tests"""
    
    @pytest.fixture
    def selector(self):
        return EmotionalActionSelector()
    
    @pytest.fixture
    def base_wm_state(self):
        return WorkingMemoryState(
            tick=1,
            danger_level=0.0,
            nearest_target=None,
            visible_objects=1,
            visible_agents=0,
            symbols=[],
            notes=""
        )
    
    # =====================================================
    # FEAR STATE TESTS
    # =====================================================
    
    def test_fear_lowers_danger_threshold(self, selector):
        """Korku durumu tehlike eşiğini düşürmeli"""
        # Neutral state
        selector.update_emotional_state({
            'valence': 0.0,
            'arousal': 0.0,
            'dominance': 0.0
        })
        neutral_threshold = selector._compute_danger_threshold()
        
        # Fear state
        selector.update_emotional_state({
            'valence': -0.5,
            'arousal': 0.6,
            'dominance': -0.3
        })
        fear_threshold = selector._compute_danger_threshold()
        
        assert fear_threshold < neutral_threshold
        assert fear_threshold < 0.5  # Significantly lower
    
    def test_fear_triggers_early_escape(self, selector, base_wm_state):
        """Korku durumunda düşük tehlikede bile kaçmalı"""
        # Set fear state
        selector.update_emotional_state({
            'valence': -0.6,
            'arousal': 0.7,
            'dominance': -0.4
        })
        
        # Medium danger (normally wouldn't trigger escape)
        base_wm_state.danger_level = 0.5
        
        action = selector.select_action(base_wm_state)
        
        assert 'ESCAPE' in action.name
        assert action.emotional_influence > 0.3
    
    def test_fear_causes_cautious_approach(self, selector, base_wm_state):
        """Korku durumunda hedefe temkinli yaklaşmalı"""
        selector.update_emotional_state({
            'valence': -0.4,
            'arousal': 0.5,
            'dominance': -0.2
        })
        
        base_wm_state.danger_level = 0.2  # Low danger
        base_wm_state.nearest_target = MockTarget()
        
        action = selector.select_action(base_wm_state)
        
        assert action.name == "CAUTIOUS_APPROACH"
        assert action.params['emotion'] == 'fear'
    
    def test_panic_escape_high_arousal(self, selector, base_wm_state):
        """Yüksek arousal + korku = panik kaçış"""
        selector.update_emotional_state({
            'valence': -0.7,
            'arousal': 0.9,  # Very high arousal
            'dominance': -0.5
        })
        
        base_wm_state.danger_level = 0.6
        
        action = selector.select_action(base_wm_state)
        
        assert action.name == "PANIC_ESCAPE"
        assert action.params['urgency'] > 0.8
    
    # =====================================================
    # EXCITEMENT STATE TESTS
    # =====================================================
    
    def test_excitement_raises_danger_threshold(self, selector):
        """Heyecan durumu tehlike eşiğini yükseltmeli"""
        # Neutral state
        selector.update_emotional_state({
            'valence': 0.0,
            'arousal': 0.0,
            'dominance': 0.0
        })
        neutral_threshold = selector._compute_danger_threshold()
        
        # Excitement state
        selector.update_emotional_state({
            'valence': 0.6,
            'arousal': 0.7,
            'dominance': 0.3
        })
        excitement_threshold = selector._compute_danger_threshold()
        
        assert excitement_threshold > neutral_threshold
        assert excitement_threshold > 0.75  # Higher than base
    
    def test_excitement_enables_risk_taking(self, selector, base_wm_state):
        """Heyecan durumunda tehlikeye rağmen kalmalı"""
        selector.update_emotional_state({
            'valence': 0.7,
            'arousal': 0.8,
            'dominance': 0.4
        })
        
        # High danger that would normally trigger escape
        base_wm_state.danger_level = 0.75
        base_wm_state.nearest_target = MockTarget()
        
        action = selector.select_action(base_wm_state)
        
        # Shouldn't escape, should approach target
        assert 'ESCAPE' not in action.name
        assert action.name == "EAGER_APPROACH"
    
    def test_excitement_increases_exploration(self, selector, base_wm_state):
        """Heyecan durumunda aktif keşif"""
        selector.update_emotional_state({
            'valence': 0.5,
            'arousal': 0.6,
            'dominance': 0.2
        })
        
        action = selector.select_action(base_wm_state)
        
        assert action.name == "ACTIVE_EXPLORE"
        assert action.params['exploration_willingness'] > 0.6
    
    # =====================================================
    # ANGER STATE TESTS
    # =====================================================
    
    def test_anger_triggers_confrontation(self, selector, base_wm_state):
        """Öfke + baskınlık = yüzleşme"""
        selector.update_emotional_state({
            'valence': -0.5,
            'arousal': 0.7,
            'dominance': 0.5  # High dominance
        })
        
        base_wm_state.danger_level = 0.6
        
        action = selector.select_action(base_wm_state)
        
        assert action.name == "CONFRONT_THREAT"
        assert action.params['emotion'] == 'anger'
    
    def test_anger_assertive_social(self, selector, base_wm_state):
        """Öfke durumunda sosyal etkileşim assertive"""
        selector.update_emotional_state({
            'valence': -0.4,
            'arousal': 0.5,
            'dominance': 0.3
        })
        
        base_wm_state.symbols = ["AGENT_IN_SIGHT"]
        
        action = selector.select_action(base_wm_state)
        
        assert action.name == "ASSERTIVE_STANCE"
    
    # =====================================================
    # CALM STATE TESTS
    # =====================================================
    
    def test_calm_careful_decisions(self, selector, base_wm_state):
        """Sakin durumda dikkatli karar"""
        selector.update_emotional_state({
            'valence': 0.1,
            'arousal': -0.3,  # Low arousal = calm
            'dominance': 0.0
        })
        
        action = selector.select_action(base_wm_state)
        
        assert action.name in ["EXPLORE", "CAUTIOUS_OBSERVE"]
    
    def test_calm_slightly_higher_threshold(self, selector):
        """Sakin durumda biraz daha yüksek tehlike eşiği"""
        selector.update_emotional_state({
            'valence': 0.0,
            'arousal': -0.4,
            'dominance': 0.0
        })
        
        threshold = selector._compute_danger_threshold()
        
        assert threshold > 0.7  # Higher than base
    
    # =====================================================
    # SOCIAL INTERACTION TESTS
    # =====================================================
    
    def test_positive_valence_friendly_greet(self, selector, base_wm_state):
        """Pozitif valence = dostça selamlama"""
        selector.update_emotional_state({
            'valence': 0.5,
            'arousal': 0.2,
            'dominance': 0.0
        })
        
        base_wm_state.symbols = ["AGENT_IN_SIGHT"]
        
        action = selector.select_action(base_wm_state)
        
        assert action.name == "FRIENDLY_GREET"
    
    def test_fear_avoids_agent(self, selector, base_wm_state):
        """Korku durumunda ajandan kaçınma"""
        selector.update_emotional_state({
            'valence': -0.5,
            'arousal': 0.6,
            'dominance': -0.3
        })
        
        base_wm_state.symbols = ["AGENT_IN_SIGHT"]
        
        action = selector.select_action(base_wm_state)
        
        assert action.name == "AVOID_AGENT"
    
    # =====================================================
    # EMOTION INFLUENCE TRACKING
    # =====================================================
    
    def test_high_emotion_marked_in_action(self, selector, base_wm_state):
        """Yüksek duygusal etki action'da işaretlenmeli"""
        selector.update_emotional_state({
            'valence': -0.8,
            'arousal': 0.9,
            'dominance': -0.5
        })
        
        base_wm_state.danger_level = 0.5
        
        action = selector.select_action(base_wm_state)
        
        assert action.emotional_influence > 0.5
        assert action.params.get('emotion') == 'fear'
    
    def test_neutral_low_emotional_influence(self, selector, base_wm_state):
        """Nötr durumda düşük duygusal etki"""
        selector.update_emotional_state({
            'valence': 0.0,
            'arousal': 0.0,
            'dominance': 0.0
        })
        
        action = selector.select_action(base_wm_state)
        
        assert action.emotional_influence < 0.5


class TestEmotionalState:
    """EmotionalState helper tests"""
    
    def test_fear_classification(self):
        """Korku doğru sınıflandırılmalı"""
        state = EmotionalState(valence=-0.5, arousal=0.5, dominance=-0.3)
        assert state.emotion_label == "fear"
    
    def test_anger_classification(self):
        """Öfke doğru sınıflandırılmalı"""
        state = EmotionalState(valence=-0.5, arousal=0.5, dominance=0.3)
        assert state.emotion_label == "anger"
    
    def test_excitement_classification(self):
        """Heyecan doğru sınıflandırılmalı"""
        state = EmotionalState(valence=0.5, arousal=0.5, dominance=0.0)
        assert state.emotion_label == "excitement"
    
    def test_sadness_classification(self):
        """Üzüntü doğru sınıflandırılmalı"""
        state = EmotionalState(valence=-0.5, arousal=-0.5, dominance=0.0)
        assert state.emotion_label == "sadness"
    
    def test_calm_classification(self):
        """Sakinlik doğru sınıflandırılmalı"""
        state = EmotionalState(valence=0.0, arousal=-0.3, dominance=0.0)
        assert state.emotion_label == "calm"


class TestExplorationWillingness:
    """Exploration willingness calculation tests"""
    
    @pytest.fixture
    def selector(self):
        return EmotionalActionSelector()
    
    def test_positive_valence_high_arousal_max_exploration(self, selector):
        """Pozitif valence + yüksek arousal = maksimum keşif"""
        selector.update_emotional_state({
            'valence': 0.8,
            'arousal': 0.8,
            'dominance': 0.5
        })
        
        willingness = selector._compute_exploration_willingness()
        
        assert willingness > 0.7
    
    def test_negative_valence_low_exploration(self, selector):
        """Negatif valence = düşük keşif"""
        selector.update_emotional_state({
            'valence': -0.6,
            'arousal': 0.5,
            'dominance': -0.3
        })
        
        willingness = selector._compute_exploration_willingness()
        
        assert willingness < 0.4
    
    def test_neutral_moderate_exploration(self, selector):
        """Nötr durum = orta keşif"""
        selector.update_emotional_state({
            'valence': 0.0,
            'arousal': 0.0,
            'dominance': 0.0
        })
        
        willingness = selector._compute_exploration_willingness()
        
        assert 0.4 < willingness < 0.6


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
