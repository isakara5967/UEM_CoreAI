"""
Somatic-Integrated Emotional Action Selector for UEM

EmotionalActionSelector + SomaticMarkerSystem entegrasyonu.
Geçmiş deneyimlerden öğrenilen duygusal izler, anlık duygusal durumla birleştirilir.

Karar formülü:
    final_score = base_score * (1 + emotion_modifier) + somatic_bias * bias_weight

Örnek:
- Base score: APPROACH_TARGET = 0.7
- Emotion modifier (excitement): +0.2 → 0.84
- Somatic bias (geçmişte target'a yaklaşınca ödül aldı): +0.3
- Final: 0.84 + 0.3 * 0.4 = 0.96
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

# Import base classes
from core.planning.action_selection.emotional_action_selector import (
    EmotionalActionSelector,
    EmotionalState,
    WorkingMemoryState,
    ActionCommand,
)
from core.emotion.somatic_marker_system import SomaticMarkerSystem, SomaticBias


class SomaticEmotionalActionSelector(EmotionalActionSelector):
    """
    EmotionalActionSelector + SomaticMarkerSystem.
    
    Üç katmanlı karar verme:
    1. Base decision (kural tabanlı)
    2. Emotional modulation (PAD state)
    3. Somatic bias (geçmiş deneyimler)
    """
    
    def __init__(
        self,
        somatic_system: Optional[SomaticMarkerSystem] = None,
        somatic_weight: float = 0.4,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(logger=logger)
        
        self.somatic = somatic_system or SomaticMarkerSystem(
            logger=self.logger.getChild("Somatic")
        )
        self.somatic_weight = somatic_weight
        
        # Track last decision for outcome recording
        self.last_world_state: Dict[str, Any] = {}
        self.last_action: Optional[ActionCommand] = None
    
    def select_action(self, wm: WorkingMemoryState) -> ActionCommand:
        """
        Somatic bias entegreli eylem seçimi.
        """
        # 1) Temel emotional decision
        base_action = super().select_action(wm)
        
        # 2) World state hazırla
        world_state = self._wm_to_world_state(wm)
        self.last_world_state = world_state
        
        # 3) Alternatif eylemler için skorlar hesapla
        candidates = self._generate_candidate_actions(wm, base_action)
        
        # 4) Her aday için somatic bias al
        action_names = [c.name for c in candidates]
        biases = self.somatic.get_action_biases(world_state, action_names)
        
        # 5) Final skorları hesapla
        scored_candidates = []
        for candidate in candidates:
            bias = biases.get(candidate.name)
            
            base_score = candidate.confidence
            somatic_contribution = 0.0
            
            if bias and bias.confidence > 0.2:
                somatic_contribution = bias.bias_value * self.somatic_weight * bias.confidence
            
            final_score = base_score + somatic_contribution
            
            scored_candidates.append((candidate, final_score, somatic_contribution))
        
        # 6) En yüksek skorlu eylemi seç
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        best_candidate, best_score, somatic_contribution = scored_candidates[0]
        
        # 7) Action'ı güncelle
        best_candidate.confidence = min(1.0, best_score)
        best_candidate.params['somatic_bias'] = round(somatic_contribution, 3)
        best_candidate.params['somatic_influenced'] = abs(somatic_contribution) > 0.1
        
        # 8) Eylemi kaydet (outcome için)
        self.somatic.record_action(
            action_name=best_candidate.name,
            action_params=best_candidate.params,
            world_state=world_state,
            emotion_state={
                'valence': self.current_emotion.valence,
                'arousal': self.current_emotion.arousal,
                'dominance': self.current_emotion.dominance,
            }
        )
        
        self.last_action = best_candidate
        
        # Log if somatic changed decision
        if best_candidate.name != base_action.name:
            self.logger.info(
                "[SomaticSelector] Decision changed by somatic: %s → %s (bias=%.2f)",
                base_action.name, best_candidate.name, somatic_contribution
            )
        elif abs(somatic_contribution) > 0.1:
            self.logger.debug(
                "[SomaticSelector] Somatic reinforced: %s (bias=%+.2f)",
                best_candidate.name, somatic_contribution
            )
        
        return best_candidate
    
    def _wm_to_world_state(self, wm: WorkingMemoryState) -> Dict[str, Any]:
        """WorkingMemoryState → world_state dict"""
        return {
            'danger_level': wm.danger_level,
            'nearest_target': wm.nearest_target,
            'objects_count': wm.visible_objects,
            'agents_count': wm.visible_agents,
            'symbols': list(wm.symbols),
            'tick': wm.tick,
        }
    
    def _generate_candidate_actions(
        self,
        wm: WorkingMemoryState,
        base_action: ActionCommand,
    ) -> List[ActionCommand]:
        """
        Base action + alternatifler üret.
        Somatic system tüm alternatifleri değerlendirecek.
        """
        candidates = [base_action]
        
        # Alternatif eylemler ekle (duruma göre)
        danger_threshold = self._compute_danger_threshold()
        
        # Eğer ESCAPE seçilmediyse ama tehlike varsa, ESCAPE'i aday olarak ekle
        if 'ESCAPE' not in base_action.name and wm.danger_level > 0.3:
            escape_candidate = ActionCommand(
                name="ESCAPE",
                params={
                    "reason": "somatic_candidate",
                    "danger_level": wm.danger_level,
                    "emotion": self.current_emotion.emotion_label,
                },
                confidence=wm.danger_level,  # Base confidence = danger level
                emotional_influence=0.3,
            )
            candidates.append(escape_candidate)
        
        # Eğer target varsa ve APPROACH seçilmediyse
        if wm.nearest_target and 'APPROACH' not in base_action.name:
            approach_candidate = ActionCommand(
                name="APPROACH_TARGET",
                params={
                    "reason": "somatic_candidate",
                    "target_id": getattr(wm.nearest_target, 'id', 'unknown'),
                    "emotion": self.current_emotion.emotion_label,
                },
                confidence=0.5,
                emotional_influence=0.2,
            )
            candidates.append(approach_candidate)
        
        # EXPLORE her zaman aday
        if 'EXPLORE' not in base_action.name:
            explore_candidate = ActionCommand(
                name="EXPLORE",
                params={
                    "reason": "somatic_candidate",
                    "emotion": self.current_emotion.emotion_label,
                },
                confidence=self._compute_exploration_willingness(),
                emotional_influence=0.2,
            )
            candidates.append(explore_candidate)
        
        return candidates
    
    def record_outcome(
        self,
        outcome_valence: float,
        description: str = "",
    ) -> None:
        """
        Son eylemin sonucunu kaydet.
        
        Args:
            outcome_valence: -1 (kötü) to +1 (iyi)
            description: "took_damage", "found_reward", etc.
        """
        if self.last_action:
            self.somatic.record_outcome(
                outcome_valence=outcome_valence,
                outcome_description=description,
                action_name=self.last_action.name,
            )
    
    def get_somatic_stats(self) -> Dict[str, Any]:
        """Somatic system istatistikleri"""
        return self.somatic.get_stats()


# Convenience function
def create_somatic_selector(
    persistence_path: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> SomaticEmotionalActionSelector:
    """Create a somatic-integrated action selector"""
    somatic = SomaticMarkerSystem(
        persistence_path=persistence_path,
        logger=logger.getChild("Somatic") if logger else None,
    )
    return SomaticEmotionalActionSelector(
        somatic_system=somatic,
        logger=logger,
    )
