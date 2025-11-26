# core/empathy/empathy_orchestrator.py
"""
EmpathyOrchestrator v1 - Empati Hesaplama Modülü

Bu modül, UEM'in başka bir ajanın durumunu anlayıp kendi geçmiş
deneyimleriyle ilişkilendirmesini sağlar.

Tasarım Kararları:
1. Empathy Level = Weighted Average (salience ağırlıklı)
2. Resonance = Valence Similarity
3. suggested_action = YOK (Planning'e bırakılır)
4. ETHMOR bağımsız (kurallar değişmez, empati context olarak gider)
5. Tetikleme = Sadece OTHER algılandığında
6. Confidence = Hesaplamanın güvenilirlik skoru

Pipeline:
    OTHER (gözlem) → MEMORY (benzer deneyimler) → ONTOLOGY (similarity)
                              ↓
                    EMPATHY ORCHESTRATOR
                    ├─ empathy_level: float
                    ├─ resonance: float
                    ├─ confidence: float
                    └─ similar_memories: List

Author: UEM Project (Efe)
Date: 26 November 2025
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Type aliases
StateVector = Tuple[float, float, float]  # (RESOURCE, THREAT, WELLBEING)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class OtherEntity:
    """Representation of another agent (observed)."""
    entity_id: str
    state_vector: StateVector
    valence: float = 0.0  # Emotional valence (-1 to 1)
    relationship: float = 0.0  # -1 (enemy) to 1 (ally)


@dataclass
class EmpathyResult:
    """
    Result of empathy computation.
    
    Attributes:
        empathy_level: How much UEM empathizes (0-1)
        resonance: Emotional resonance with other (0-1)
        confidence: Reliability of the empathy computation (0-1)
        similar_memories: List of similar past experiences
        other_entity: The entity empathy was computed for
    """
    empathy_level: float
    resonance: float
    confidence: float
    similar_memories: List[Dict[str, Any]] = field(default_factory=list)
    other_entity: Optional[OtherEntity] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'empathy_level': self.empathy_level,
            'resonance': self.resonance,
            'confidence': self.confidence,
            'similar_memory_count': len(self.similar_memories),
            'other_entity_id': self.other_entity.entity_id if self.other_entity else None,
        }


# ============================================================================
# EMPATHY ORCHESTRATOR
# ============================================================================

class EmpathyOrchestrator:
    """
    Orchestrates empathy computation for UEM.
    
    This module is triggered ONLY when another entity (OTHER) is perceived.
    It does NOT suggest actions - that's Planning's job.
    
    Dependencies:
        - SELF: For current state and valence
        - Memory: For retrieving similar past experiences
        - Ontology: For similarity computation (optional, has fallback)
    
    Usage:
        orchestrator = EmpathyOrchestrator(self_system, memory_interface)
        
        # When OTHER is perceived:
        if perceived_other is not None:
            result = orchestrator.compute(perceived_other)
            # Pass result to Planning as context
    """
    
    # Configuration defaults
    DEFAULT_CONFIG = {
        'max_similar_experiences': 10,  # N for confidence calculation
        'similarity_tolerance': 0.3,    # How close states must be
        'min_confidence_threshold': 0.1,  # Below this, empathy is unreliable
    }
    
    def __init__(
        self,
        self_system: Any = None,
        memory_interface: Any = None,
        emotion_system: Any = None,
        logger: Optional[logging.Logger] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize EmpathyOrchestrator.
        
        Args:
            self_system: SelfCore instance
            memory_interface: MemoryInterface instance
            emotion_system: EmotionCore instance (for current valence)
            logger: Logger instance
            config: Configuration overrides
        """
        self.self_system = self_system
        self.memory_interface = memory_interface
        self.emotion_system = emotion_system
        self.logger = logger or logging.getLogger("empathy.orchestrator")
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        
        # Statistics
        self._stats = {
            'computations': 0,
            'avg_empathy': 0.0,
            'avg_confidence': 0.0,
            'zero_experience_count': 0,
        }
    
    # ========================================================================
    # MAIN COMPUTATION
    # ========================================================================
    
    def compute(self, other: OtherEntity) -> EmpathyResult:
        """
        Compute empathy for another entity.
        
        This is the main entry point. Call this when OTHER is perceived.
        
        Args:
            other: The observed entity
            
        Returns:
            EmpathyResult with empathy_level, resonance, confidence
        """
        self._stats['computations'] += 1
        
        # Get similar experiences from memory
        similar_experiences = self._get_similar_experiences(other.state_vector)
        
        # Compute empathy level (weighted average)
        empathy_level, weight_sum = self._compute_empathy_level(similar_experiences)
        
        # Compute resonance (valence similarity)
        resonance = self._compute_resonance(other.valence)
        
        # Compute confidence
        confidence = self._compute_confidence(similar_experiences, weight_sum)
        
        # Handle edge case: no experiences
        if len(similar_experiences) == 0:
            self._stats['zero_experience_count'] += 1
            self.logger.debug(
                f"[Empathy] No similar experiences for {other.entity_id}, "
                f"returning zero empathy with zero confidence"
            )
        
        # Update running averages
        self._update_stats(empathy_level, confidence)
        
        result = EmpathyResult(
            empathy_level=empathy_level,
            resonance=resonance,
            confidence=confidence,
            similar_memories=similar_experiences,
            other_entity=other,
        )
        
        self.logger.debug(
            f"[Empathy] Computed for {other.entity_id}: "
            f"level={empathy_level:.2f}, resonance={resonance:.2f}, "
            f"confidence={confidence:.2f}, memories={len(similar_experiences)}"
        )
        
        return result
    
    # ========================================================================
    # EMPATHY LEVEL COMPUTATION
    # ========================================================================
    
    def _compute_empathy_level(
        self,
        similar_experiences: List[Dict[str, Any]],
    ) -> Tuple[float, float]:
        """
        Compute empathy level using weighted average.
        
        Formula (v1):
            weight = salience
            empathy = sum(similarity * weight) / sum(weight)
        
        Args:
            similar_experiences: List of similar past experiences
            
        Returns:
            Tuple of (empathy_level, total_weight)
        """
        if not similar_experiences:
            return 0.0, 0.0
        
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for exp in similar_experiences:
            similarity = exp.get('similarity', 0.0)
            salience = exp.get('salience', 0.5)  # Default 0.5 if missing
            
            weight = salience
            weighted_sum += similarity * weight
            weight_sum += weight
        
        if weight_sum == 0:
            return 0.0, 0.0
        
        empathy_level = weighted_sum / weight_sum
        
        # Clamp to [0, 1]
        empathy_level = max(0.0, min(1.0, empathy_level))
        
        return empathy_level, weight_sum
    
    # ========================================================================
    # RESONANCE COMPUTATION
    # ========================================================================
    
    def _compute_resonance(self, other_valence: float) -> float:
        """
        Compute emotional resonance based on valence similarity.
        
        Formula:
            resonance = 1 - abs(my_valence - other_valence)
        
        Args:
            other_valence: The other entity's emotional valence (-1 to 1)
            
        Returns:
            Resonance score (0 to 1)
        """
        my_valence = self._get_current_valence()
        
        # Valence similarity
        valence_diff = abs(my_valence - other_valence)
        
        # Since valence is -1 to 1, max difference is 2
        # Normalize to 0-1 range
        resonance = 1 - (valence_diff / 2.0)
        
        return max(0.0, min(1.0, resonance))
    
    def _get_current_valence(self) -> float:
        """Get current emotional valence from emotion system."""
        if self.emotion_system is None:
            return 0.0
        
        # Try different attribute names
        valence = getattr(self.emotion_system, 'valence', None)
        if valence is not None:
            return valence
        
        # Try dict access
        if hasattr(self.emotion_system, 'get'):
            return self.emotion_system.get('valence', 0.0)
        
        # Try current_emotion dict
        current = getattr(self.emotion_system, 'current_emotion', None)
        if current and isinstance(current, dict):
            return current.get('valence', 0.0)
        
        return 0.0
    
    # ========================================================================
    # CONFIDENCE COMPUTATION
    # ========================================================================
    
    def _compute_confidence(
        self,
        similar_experiences: List[Dict[str, Any]],
        weight_sum: float,
    ) -> float:
        """
        Compute confidence score for the empathy calculation.
        
        Formula:
            confidence = sum(weights) / max_possible_weight
            where max_possible_weight = N * 1.0 (N = max expected experiences)
        
        Low confidence means:
            - Few or no similar experiences
            - Low salience experiences
        
        Args:
            similar_experiences: List of similar experiences
            weight_sum: Sum of all weights used
            
        Returns:
            Confidence score (0 to 1)
        """
        if not similar_experiences:
            return 0.0
        
        max_experiences = self.config.get('max_similar_experiences', 10)
        max_possible_weight = max_experiences * 1.0  # Max salience is 1.0
        
        confidence = weight_sum / max_possible_weight
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))
    
    # ========================================================================
    # MEMORY ACCESS
    # ========================================================================
    
    def _get_similar_experiences(
        self,
        other_state: StateVector,
    ) -> List[Dict[str, Any]]:
        """
        Get similar experiences from memory.
        
        Args:
            other_state: The other entity's state vector
            
        Returns:
            List of similar experience dicts with similarity and salience
        """
        if self.memory_interface is None:
            return []
        
        tolerance = self.config.get('similarity_tolerance', 0.3)
        max_results = self.config.get('max_similar_experiences', 10)
        
        try:
            experiences = self.memory_interface.get_similar_experiences(
                state_vector=other_state,
                tolerance=tolerance,
                limit=max_results,
            )
            return experiences
        except Exception as e:
            self.logger.warning(f"[Empathy] Failed to get similar experiences: {e}")
            return []
    
    # ========================================================================
    # UTILITY
    # ========================================================================
    
    def _update_stats(self, empathy_level: float, confidence: float) -> None:
        """Update running statistics."""
        n = self._stats['computations']
        
        # Running average for empathy
        old_avg = self._stats['avg_empathy']
        self._stats['avg_empathy'] = old_avg + (empathy_level - old_avg) / n
        
        # Running average for confidence
        old_conf = self._stats['avg_confidence']
        self._stats['avg_confidence'] = old_conf + (confidence - old_conf) / n
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            **self._stats,
            'config': self.config,
        }
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {
            'computations': 0,
            'avg_empathy': 0.0,
            'avg_confidence': 0.0,
            'zero_experience_count': 0,
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_empathy_orchestrator(
    self_system: Any = None,
    memory_interface: Any = None,
    emotion_system: Any = None,
    config: Optional[Dict[str, Any]] = None,
) -> EmpathyOrchestrator:
    """
    Factory function to create an EmpathyOrchestrator.
    
    Usage:
        orchestrator = create_empathy_orchestrator(
            self_system=self_core,
            memory_interface=memory,
            emotion_system=emotion_core,
        )
    """
    return EmpathyOrchestrator(
        self_system=self_system,
        memory_interface=memory_interface,
        emotion_system=emotion_system,
        config=config,
    )


# ============================================================================
# INTEGRATION HELPER
# ============================================================================

class EmpathyIntegrationMixin:
    """
    Mixin for integrating Empathy into the cognitive cycle.
    
    Add this to IntegratedUEMCore to enable empathy computation
    when OTHER entities are perceived.
    
    Usage:
        class IntegratedUEMCore(EmpathyIntegrationMixin, ...):
            pass
    """
    
    def _compute_empathy_if_other_present(
        self,
        world_state: Any,
    ) -> Optional[EmpathyResult]:
        """
        Compute empathy if another entity is present in world state.
        
        Args:
            world_state: Current world state
            
        Returns:
            EmpathyResult if OTHER present, None otherwise
        """
        # Check if empathy system exists
        empathy = getattr(self, 'empathy_system', None)
        if empathy is None:
            return None
        
        # Check if OTHER is present
        other = self._extract_other_entity(world_state)
        if other is None:
            return None
        
        # Compute empathy
        return empathy.compute(other)
    
    def _extract_other_entity(self, world_state: Any) -> Optional[OtherEntity]:
        """
        Extract OTHER entity from world state.
        
        Override this method based on your world state structure.
        """
        # Try different attribute names
        for attr in ['other_entity', 'observed_agent', 'npc', 'other']:
            other_data = getattr(world_state, attr, None)
            if other_data is not None:
                return self._convert_to_other_entity(other_data)
        
        # Try dict access
        if hasattr(world_state, 'get'):
            other_data = world_state.get('other_entity')
            if other_data:
                return self._convert_to_other_entity(other_data)
        
        return None
    
    def _convert_to_other_entity(self, data: Any) -> OtherEntity:
        """Convert various data formats to OtherEntity."""
        if isinstance(data, OtherEntity):
            return data
        
        if isinstance(data, dict):
            return OtherEntity(
                entity_id=data.get('id', 'unknown'),
                state_vector=data.get('state_vector', (0.5, 0.5, 0.5)),
                valence=data.get('valence', 0.0),
                relationship=data.get('relationship', 0.0),
            )
        
        # Try to extract attributes
        return OtherEntity(
            entity_id=getattr(data, 'id', getattr(data, 'entity_id', 'unknown')),
            state_vector=getattr(data, 'state_vector', (0.5, 0.5, 0.5)),
            valence=getattr(data, 'valence', 0.0),
            relationship=getattr(data, 'relationship', 0.0),
        )
