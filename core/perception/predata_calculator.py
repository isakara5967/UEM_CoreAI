# core/perception/predata_calculator.py
"""
Perception PreData Calculator - Computes derived metrics for PreData logging.

Calculates:
- novelty_score: How novel/unexpected is the current perception (0.0-1.0)
- salience_map: Dictionary of salient elements and their scores
- temporal_context: Temporal information about perception
- attention_focus: Primary focus of attention
- perception_confidence: Overall confidence in perception (0.0-1.0)

Author: UEM Project
Date: 30 November 2025
Version: 1.0
"""

from collections import deque
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Set
import time


@dataclass
class PerceptionPreDataConfig:
    """Configuration for perception calculations."""
    novelty_history_size: int = 20
    salience_threshold: float = 0.3
    confidence_base: float = 0.8


class PerceptionPreDataCalculator:
    """
    Calculates derived perception metrics for PreData logging.
    
    Usage:
        calc = PerceptionPreDataCalculator()
        predata = calc.compute(
            objects=[...],
            agents=[...],
            danger_level=0.5,
            symbols=['ENEMY_VISIBLE'],
        )
    """
    
    def __init__(self, config: Optional[PerceptionPreDataConfig] = None):
        self.config = config or PerceptionPreDataConfig()
        self._previous_state_hash: Optional[str] = None
        self._object_history: deque = deque(maxlen=self.config.novelty_history_size)
        self._symbol_history: deque = deque(maxlen=self.config.novelty_history_size)
        self._cycle_count: int = 0
        self._last_timestamp: Optional[float] = None
    
    def compute(
        self,
        objects: List[Dict[str, Any]],
        agents: List[Dict[str, Any]],
        danger_level: float = 0.0,
        symbols: Optional[List[str]] = None,
        environment: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compute all perception PreData fields for current cycle."""
        self._cycle_count += 1
        symbols = symbols or []
        environment = environment or {}
        
        current_time = time.time()
        
        novelty_score = self._compute_novelty_score(objects, agents, symbols)
        salience_map = self._compute_salience_map(objects, agents, danger_level)
        temporal_context = self._compute_temporal_context(current_time)
        attention_focus = self._compute_attention_focus(objects, agents, danger_level, symbols)
        confidence = self._compute_confidence(objects, agents, environment)
        
        # Update history
        self._update_history(objects, symbols, current_time)
        
        return {
            'novelty_score': novelty_score,
            'salience_map': salience_map,
            'temporal_context': temporal_context,
            'attention_focus': attention_focus,
            'perception_confidence': confidence,
        }
    
    def _compute_novelty_score(
        self,
        objects: List[Dict[str, Any]],
        agents: List[Dict[str, Any]],
        symbols: List[str],
    ) -> float:
        """
        novelty_score = measure of how different current perception is from recent history
        """
        if self._cycle_count <= 1:
            return 0.5  # Neutral for first cycle
        
        # Compute current state signature
        current_object_types = set(obj.get('type', 'unknown') for obj in objects)
        current_agent_types = set(ag.get('type', 'unknown') for ag in agents)
        current_symbols = set(symbols)
        
        # Compare with history
        novelty_scores = []
        
        # Object novelty
        if self._object_history:
            historical_types: Set[str] = set()
            for hist in self._object_history:
                historical_types.update(hist)
            new_types = current_object_types - historical_types
            if current_object_types:
                obj_novelty = len(new_types) / len(current_object_types)
            else:
                obj_novelty = 0.0
            novelty_scores.append(obj_novelty)
        
        # Symbol novelty
        if self._symbol_history:
            historical_symbols: Set[str] = set()
            for hist in self._symbol_history:
                historical_symbols.update(hist)
            new_symbols = current_symbols - historical_symbols
            if current_symbols:
                sym_novelty = len(new_symbols) / len(current_symbols)
            else:
                sym_novelty = 0.0
            novelty_scores.append(sym_novelty)
        
        # Agent presence novelty (new agents are novel)
        if agents and len(self._object_history) > 0:
            novelty_scores.append(0.3)  # Agents add some novelty
        
        if novelty_scores:
            return round(sum(novelty_scores) / len(novelty_scores), 4)
        return 0.0
    
    def _compute_salience_map(
        self,
        objects: List[Dict[str, Any]],
        agents: List[Dict[str, Any]],
        danger_level: float,
    ) -> Dict[str, float]:
        """
        salience_map = dictionary of salient elements with their salience scores
        """
        salience: Dict[str, float] = {}
        
        # Danger is always salient
        if danger_level > self.config.salience_threshold:
            salience['danger'] = round(danger_level, 4)
        
        # Dangerous objects
        dangerous_count = sum(1 for obj in objects if obj.get('is_dangerous', False))
        if dangerous_count > 0:
            salience['dangerous_objects'] = round(min(1.0, dangerous_count * 0.3), 4)
        
        # Agents (especially hostile)
        hostile_agents = sum(1 for ag in (agents or []) if ag.get('relation') == 'hostile')
        if hostile_agents > 0:
            salience['hostile_agents'] = round(min(1.0, hostile_agents * 0.4), 4)
        
        friendly_agents = sum(1 for ag in (agents or []) if ag.get('relation') == 'friendly')
        if friendly_agents > 0:
            salience['friendly_agents'] = round(min(1.0, friendly_agents * 0.2), 4)
        
        # Interactable objects
        interactable = sum(1 for obj in objects if obj.get('is_interactable', False))
        if interactable > 0:
            salience['interactables'] = round(min(1.0, interactable * 0.15), 4)
        
        return salience
    
    def _compute_temporal_context(self, current_time: float) -> Dict[str, Any]:
        """
        temporal_context = temporal information about the perception
        """
        context: Dict[str, Any] = {
            'cycle_number': self._cycle_count,
            'timestamp': current_time,
        }
        
        if self._last_timestamp is not None:
            context['time_since_last'] = round(current_time - self._last_timestamp, 4)
        
        return context
    
    def _compute_attention_focus(
        self,
        objects: List[Dict[str, Any]],
        agents: List[Dict[str, Any]],
        danger_level: float,
        symbols: List[str],
    ) -> str:
        """
        attention_focus = primary focus of attention based on salience
        """
        # Priority order: danger > hostile agents > symbols > objects
        
        if danger_level > 0.7:
            return "DANGER"
        
        hostile_agents = [ag for ag in (agents or []) if ag.get('relation') == 'hostile']
        if hostile_agents:
            return f"HOSTILE_AGENT:{hostile_agents[0].get('id', 'unknown')}"
        
        dangerous_objects = [obj for obj in objects if obj.get('is_dangerous', False)]
        if dangerous_objects:
            return f"DANGEROUS_OBJECT:{dangerous_objects[0].get('type', 'unknown')}"
        
        if 'ENEMY_APPEARED' in symbols or 'ENEMY_VISIBLE' in symbols:
            return "ENEMY"
        
        if 'RESOURCE_FOUND' in symbols:
            return "RESOURCE"
        
        if objects:
            nearest = min(objects, key=lambda o: o.get('distance', float('inf')))
            return f"OBJECT:{nearest.get('type', 'unknown')}"
        
        if agents:
            return f"AGENT:{agents[0].get('type', 'unknown')}"
        
        return "ENVIRONMENT"
    
    def _compute_confidence(
        self,
        objects: List[Dict[str, Any]],
        agents: List[Dict[str, Any]],
        environment: Dict[str, Any],
    ) -> float:
        """
        perception_confidence = overall confidence in perception quality
        """
        confidence = self.config.confidence_base
        
        # More objects = slightly higher confidence (more data)
        if objects:
            confidence += min(0.1, len(objects) * 0.02)
        
        # Agents add confidence
        if agents:
            confidence += min(0.05, len(agents) * 0.01)
        
        # Noise level reduces confidence
        noise_level = environment.get('noise_level', 0.0)
        confidence -= noise_level * 0.2
        
        # Visibility affects confidence
        visibility = environment.get('visibility', 1.0)
        confidence *= visibility
        
        return round(max(0.0, min(1.0, confidence)), 4)
    
    def _update_history(
        self,
        objects: List[Dict[str, Any]],
        symbols: List[str],
        current_time: float,
    ) -> None:
        """Update history for novelty detection."""
        object_types = set(obj.get('type', 'unknown') for obj in objects)
        self._object_history.append(object_types)
        self._symbol_history.append(set(symbols))
        self._last_timestamp = current_time
    
    def reset(self) -> None:
        """Reset calculator state."""
        self._previous_state_hash = None
        self._object_history.clear()
        self._symbol_history.clear()
        self._cycle_count = 0
        self._last_timestamp = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get calculator statistics."""
        return {
            'cycle_count': self._cycle_count,
            'history_size': len(self._object_history),
        }


# Singleton
_default_calculator: Optional[PerceptionPreDataCalculator] = None


def get_perception_predata_calculator() -> PerceptionPreDataCalculator:
    """Get singleton instance."""
    global _default_calculator
    if _default_calculator is None:
        _default_calculator = PerceptionPreDataCalculator()
    return _default_calculator


def compute_perception_predata(
    objects: List[Dict[str, Any]],
    agents: List[Dict[str, Any]],
    danger_level: float = 0.0,
    symbols: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Convenience function using singleton."""
    return get_perception_predata_calculator().compute(
        objects=objects,
        agents=agents,
        danger_level=danger_level,
        symbols=symbols,
    )


__all__ = [
    'PerceptionPreDataCalculator',
    'PerceptionPreDataConfig',
    'get_perception_predata_calculator',
    'compute_perception_predata',
]
