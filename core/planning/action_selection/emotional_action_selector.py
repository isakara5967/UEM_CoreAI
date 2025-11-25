"""
Emotion-Aware Action Selector for UEM

Duygusal duruma göre karar eşiklerini dinamik olarak ayarlar:
- Korku (low valence, high arousal): Daha agresif kaçış, düşük tehlike eşiği
- Heyecan (high valence, high arousal): Risk alabilme, keşif önceliği
- Sakinlik (low arousal): Dikkatli karar verme
- Öfke (low valence, high arousal, high dominance): Saldırgan davranış
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Any


@dataclass
class EmotionalState:
    """PAD modeli emotion state"""
    valence: float = 0.0      # -1 (negatif) to +1 (pozitif)
    arousal: float = 0.0      # -1 (sakin) to +1 (heyecanlı)
    dominance: float = 0.0    # -1 (boyun eğen) to +1 (baskın)
    
    @property
    def emotion_label(self) -> str:
        """PAD değerlerinden kategori çıkar"""
        if self.valence < -0.3 and self.arousal > 0.3:
            if self.dominance < -0.2:
                return "fear"
            else:
                return "anger"
        elif self.valence > 0.3 and self.arousal > 0.3:
            return "excitement"
        elif self.valence > 0.3 and self.arousal < -0.2:
            return "contentment"
        elif self.valence < -0.3 and self.arousal < -0.2:
            return "sadness"
        elif abs(self.arousal) < 0.2:
            return "calm"
        return "neutral"


@dataclass
class ActionCommand:
    """Planning katmanının ürettiği eylem komutu"""
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    emotional_influence: float = 0.0  # Duygunun karara etkisi

    def __repr__(self) -> str:
        if not self.params:
            return f"ActionCommand({self.name}, conf={self.confidence:.2f})"
        return f"ActionCommand({self.name}, {self.params}, conf={self.confidence:.2f})"


@dataclass
class WorkingMemoryState:
    """Karar verme için özet zihin durumu"""
    tick: int = 0
    danger_level: float = 0.0
    nearest_target: Optional[Any] = None
    visible_objects: int = 0
    visible_agents: int = 0
    symbols: list = field(default_factory=list)
    notes: str = ""


class EmotionalActionSelector:
    """
    Emotion-aware action selector.
    
    Duygusal durum karar eşiklerini dinamik olarak değiştirir:
    
    KORKU DURUMU (fear):
        - danger_threshold: 0.7 → 0.4 (daha erken kaç)
        - escape_urgency: normal → yüksek
        - exploration_willingness: düşük
        
    HEYECAN DURUMU (excitement):
        - danger_threshold: 0.7 → 0.8 (daha geç kaç)
        - risk_tolerance: yüksek
        - exploration_willingness: yüksek
        
    SAKİN DURUM (calm):
        - Tüm eşikler normal
        - Dikkatli analiz
        
    ÖFKE DURUMU (anger):
        - danger_threshold: 0.7 → 0.5
        - aggression_bias: yüksek
        - dominance davranışı
    """
    
    # Temel eşikler
    BASE_DANGER_THRESHOLD = 0.7
    BASE_EXPLORATION_THRESHOLD = 0.3
    
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or logging.getLogger("core.planning.EmotionalActionSelector")
        self.current_emotion: EmotionalState = EmotionalState()
        
    def update_emotional_state(self, emotion_data: Dict[str, float]) -> None:
        """Event bus'tan gelen emotion state'i güncelle"""
        self.current_emotion = EmotionalState(
            valence=emotion_data.get('valence', 0.0),
            arousal=emotion_data.get('arousal', 0.0),
            dominance=emotion_data.get('dominance', 0.0)
        )
        self.logger.debug(
            "[ActionSelector] Emotion updated: %s (v=%.2f, a=%.2f, d=%.2f)",
            self.current_emotion.emotion_label,
            self.current_emotion.valence,
            self.current_emotion.arousal,
            self.current_emotion.dominance
        )
    
    def _compute_danger_threshold(self) -> float:
        """Duygusal duruma göre tehlike eşiğini hesapla"""
        base = self.BASE_DANGER_THRESHOLD
        emotion = self.current_emotion
        
        # Korku: Eşiği düşür (erken kaç)
        if emotion.emotion_label == "fear":
            # Arousal yüksekse daha da erken kaç
            fear_modifier = -0.3 * (1 + emotion.arousal)
            return max(0.3, base + fear_modifier)
        
        # Heyecan: Eşiği yükselt (risk al)
        elif emotion.emotion_label == "excitement":
            excitement_modifier = 0.15 * emotion.valence
            return min(0.9, base + excitement_modifier)
        
        # Öfke: Orta düzeyde düşür (saldırgan ama dikkatli)
        elif emotion.emotion_label == "anger":
            anger_modifier = -0.15 * emotion.arousal
            return max(0.4, base + anger_modifier)
        
        # Sakin: Hafif yükselt (daha dikkatli)
        elif emotion.emotion_label == "calm":
            return base + 0.05
        
        return base
    
    def _compute_exploration_willingness(self) -> float:
        """Keşif istekliliğini hesapla"""
        emotion = self.current_emotion
        
        # Pozitif valence + yüksek arousal = yüksek keşif
        base_willingness = 0.5
        
        valence_effect = emotion.valence * 0.3
        arousal_effect = emotion.arousal * 0.2 if emotion.valence > 0 else -emotion.arousal * 0.2
        
        willingness = base_willingness + valence_effect + arousal_effect
        return max(0.1, min(1.0, willingness))
    
    def _compute_escape_urgency(self) -> float:
        """Kaçış aciliyetini hesapla (1.0 = çok acil)"""
        emotion = self.current_emotion
        
        if emotion.emotion_label == "fear":
            # Korku + yüksek arousal = panik kaçış
            return 0.8 + (emotion.arousal * 0.2)
        elif emotion.emotion_label == "anger":
            # Öfke = kaçmak istemez, savaş
            return 0.3
        else:
            return 0.5
    
    def _should_be_aggressive(self) -> bool:
        """Saldırgan davranış mı göstermeli?"""
        emotion = self.current_emotion
        return (
            emotion.emotion_label == "anger" and 
            emotion.dominance > 0.2 and
            emotion.arousal > 0.3
        )
    
    def select_action(self, wm: WorkingMemoryState) -> ActionCommand:
        """
        Duygusal duruma göre eylem seç.
        
        Karar sırası:
        1. Tehlike değerlendirmesi (emotion-adjusted threshold)
        2. Hedef değerlendirmesi (exploration willingness)
        3. Sosyal etkileşim
        4. Varsayılan davranış
        """
        emotion = self.current_emotion
        danger_threshold = self._compute_danger_threshold()
        exploration_willingness = self._compute_exploration_willingness()
        escape_urgency = self._compute_escape_urgency()
        
        self.logger.debug(
            "[ActionSelector] Thresholds - danger: %.2f, explore: %.2f, escape_urg: %.2f, emotion: %s",
            danger_threshold,
            exploration_willingness,
            escape_urgency,
            emotion.emotion_label
        )
        
        # ============================================
        # 1) TEHLİKE DEĞERLENDİRMESİ
        # ============================================
        if wm.danger_level >= danger_threshold:
            # Öfke durumunda ve dominant ise: Savaş (CONFRONT)
            if self._should_be_aggressive():
                action = ActionCommand(
                    name="CONFRONT_THREAT",
                    params={
                        "reason": "anger_driven_confrontation",
                        "danger_level": wm.danger_level,
                        "emotion": emotion.emotion_label,
                        "dominance": emotion.dominance,
                    },
                    confidence=0.6 + emotion.dominance * 0.3,
                    emotional_influence=0.7
                )
                self.logger.info(
                    "[ActionSelector] CONFRONT selected (anger+dominance, danger=%.2f)",
                    wm.danger_level
                )
                return action
            
            # Korku durumu: Acil kaçış
            escape_type = "PANIC_ESCAPE" if escape_urgency > 0.7 else "ESCAPE"
            action = ActionCommand(
                name=escape_type,
                params={
                    "reason": "high_danger",
                    "danger_level": wm.danger_level,
                    "threshold_used": danger_threshold,
                    "urgency": escape_urgency,
                    "emotion": emotion.emotion_label,
                },
                confidence=escape_urgency,
                emotional_influence=abs(emotion.valence)
            )
            self.logger.info(
                "[ActionSelector] %s selected (danger=%.2f, threshold=%.2f, urgency=%.2f)",
                escape_type, wm.danger_level, danger_threshold, escape_urgency
            )
            return action
        
        # ============================================
        # 2) HEDEF DEĞERLENDİRMESİ
        # ============================================
        if wm.nearest_target is not None:
            # Heyecanlı = daha agresif yaklaşım
            if emotion.emotion_label == "excitement":
                action = ActionCommand(
                    name="EAGER_APPROACH",
                    params={
                        "target_id": getattr(wm.nearest_target, 'id', 'unknown'),
                        "distance": getattr(wm.nearest_target, 'distance', 0),
                        "emotion": emotion.emotion_label,
                        "willingness": exploration_willingness,
                    },
                    confidence=0.8,
                    emotional_influence=emotion.valence
                )
                self.logger.info(
                    "[ActionSelector] EAGER_APPROACH selected (excitement, target=%s)",
                    getattr(wm.nearest_target, 'id', 'unknown')
                )
                return action
            
            # Korku varsa ama tehlike eşiğinin altında: Temkinli yaklaşım
            if emotion.emotion_label == "fear":
                action = ActionCommand(
                    name="CAUTIOUS_APPROACH",
                    params={
                        "target_id": getattr(wm.nearest_target, 'id', 'unknown'),
                        "distance": getattr(wm.nearest_target, 'distance', 0),
                        "emotion": emotion.emotion_label,
                        "caution_level": 1 - exploration_willingness,
                    },
                    confidence=0.5,
                    emotional_influence=abs(emotion.valence)
                )
                self.logger.info(
                    "[ActionSelector] CAUTIOUS_APPROACH selected (fear, target=%s)",
                    getattr(wm.nearest_target, 'id', 'unknown')
                )
                return action
            
            # Normal yaklaşım
            action = ActionCommand(
                name="APPROACH_TARGET",
                params={
                    "target_id": getattr(wm.nearest_target, 'id', 'unknown'),
                    "distance": getattr(wm.nearest_target, 'distance', 0),
                    "emotion": emotion.emotion_label,
                },
                confidence=0.7,
                emotional_influence=0.2
            )
            self.logger.debug("[ActionSelector] APPROACH_TARGET selected")
            return action
        
        # ============================================
        # 3) SOSYAL ETKİLEŞİM
        # ============================================
        if "AGENT_IN_SIGHT" in wm.symbols:
            # Sosyal davranış emotion'a göre değişir
            if emotion.valence > 0.2:
                action_name = "FRIENDLY_GREET"
            elif emotion.emotion_label == "fear":
                action_name = "AVOID_AGENT"
            elif emotion.emotion_label == "anger":
                action_name = "ASSERTIVE_STANCE"
            else:
                action_name = "NEUTRAL_GREET"
            
            action = ActionCommand(
                name=action_name,
                params={
                    "note": "agent_in_sight",
                    "emotion": emotion.emotion_label,
                    "valence": emotion.valence,
                },
                confidence=0.6,
                emotional_influence=abs(emotion.valence)
            )
            self.logger.debug("[ActionSelector] %s selected (agent in sight)", action_name)
            return action
        
        # ============================================
        # 4) VARSAYILAN DAVRANIŞ
        # ============================================
        # Keşif istekliliğine göre davranış
        if exploration_willingness > 0.6:
            action_name = "ACTIVE_EXPLORE"
        elif exploration_willingness < 0.3:
            action_name = "CAUTIOUS_OBSERVE"
        else:
            action_name = "EXPLORE"
        
        action = ActionCommand(
            name=action_name,
            params={
                "reason": "default",
                "symbols": list(wm.symbols),
                "exploration_willingness": exploration_willingness,
                "emotion": emotion.emotion_label,
            },
            confidence=exploration_willingness,
            emotional_influence=0.3
        )
        self.logger.debug(
            "[ActionSelector] %s selected (willingness=%.2f)",
            action_name, exploration_willingness
        )
        return action


# Geriye uyumluluk için alias
ActionSelector = EmotionalActionSelector
