"""
Somatic Marker System for UEM

Damasio'nun Somatic Marker Hypothesis'inden esinlenilmiştir.
Geçmiş deneyimlerin duygusal sonuçlarını öğrenir ve gelecek kararlara bias ekler.

Çalışma prensibi:
1. Bir eylem yapılır (action)
2. Sonuç gözlemlenir (outcome: reward/punishment)
3. Duygusal iz kaydedilir (situation + action → emotional_valence)
4. Gelecekte benzer durumda bu iz, karar vermeye bias ekler

Örnek:
- "Karanlık mağaraya girdim → saldırıya uğradım → negatif marker"
- Gelecekte karanlık mağara görünce: otomatik kaçınma bias'ı

Event integration:
- planning.action_decided → Eylemi kaydet
- world.outcome_received → Sonucu kaydet, marker güncelle
- somatic.marker_activated → Bias uygulandığında
"""

from __future__ import annotations
import logging
import time
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from pathlib import Path


@dataclass
class SomaticMarker:
    """Tek bir duygusal iz/marker"""
    situation_hash: str
    action: str
    valence: float  # -1 (çok kötü) to +1 (çok iyi)
    strength: float  # 0 to 1, zamanla decay
    creation_time: float
    last_activation: float
    activation_count: int = 0
    
    # Metadata
    context_tags: List[str] = field(default_factory=list)
    original_outcome: str = ""
    
    def decay(self, decay_rate: float = 0.01) -> None:
        """Zamanla marker gücü azalır (unutma)"""
        time_passed = time.time() - self.last_activation
        decay_factor = max(0.1, 1 - (decay_rate * time_passed / 3600))  # Saat başı decay
        self.strength *= decay_factor
    
    def reinforce(self, new_valence: float, learning_rate: float = 0.3) -> None:
        """Marker'ı yeni deneyimle güçlendir"""
        self.valence = self.valence * (1 - learning_rate) + new_valence * learning_rate
        self.strength = min(1.0, self.strength + 0.1)
        self.last_activation = time.time()
        self.activation_count += 1


@dataclass
class PendingAction:
    """Sonucu beklenen eylem kaydı"""
    action_name: str
    action_params: Dict[str, Any]
    situation_hash: str
    situation_features: Dict[str, Any]
    timestamp: float
    emotion_at_decision: Dict[str, float]


@dataclass
class SomaticBias:
    """Bir eylem için hesaplanan toplam bias"""
    action: str
    bias_value: float  # -1 to +1
    contributing_markers: List[str]  # Hangi marker'lar katkı yaptı
    confidence: float  # Ne kadar güvenilir (marker sayısına göre)


class SomaticMarkerSystem:
    """
    Somatic Marker System - Duygusal Öğrenme ve Karar Bias'ı
    
    Ana işlevler:
    1. record_action(): Yapılan eylemi kaydet
    2. record_outcome(): Sonucu kaydet, marker oluştur/güncelle
    3. get_action_biases(): Mevcut durum için eylem bias'larını al
    4. apply_bias_to_decisions(): Karar skorlarına bias ekle
    """
    
    DEFAULT_LEARNING_RATE = 0.3
    DEFAULT_DECAY_RATE = 0.01
    DEFAULT_BIAS_WEIGHT = 0.4  # Karar vermedeki bias ağırlığı
    
    def __init__(
        self,
        learning_rate: float = DEFAULT_LEARNING_RATE,
        decay_rate: float = DEFAULT_DECAY_RATE,
        bias_weight: float = DEFAULT_BIAS_WEIGHT,
        persistence_path: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        event_bus: Any = None,
    ) -> None:
        self.learning_rate = learning_rate
        self.decay_rate = decay_rate
        self.bias_weight = bias_weight
        self.persistence_path = Path(persistence_path) if persistence_path else None
        self.logger = logger or logging.getLogger("core.emotion.SomaticMarkerSystem")
        self.event_bus = event_bus
        
        # Marker storage: situation_hash → {action → SomaticMarker}
        self.markers: Dict[str, Dict[str, SomaticMarker]] = defaultdict(dict)
        
        # Pending actions waiting for outcomes
        self.pending_actions: List[PendingAction] = []
        self.max_pending = 10  # En fazla bekleyen eylem
        
        # Statistics
        self.total_markers = 0
        self.total_activations = 0
        self.bias_applications = 0
        
        # Action experience count (for confidence calculation)
        self.action_experience_count: Dict[str, int] = defaultdict(int)
        self.confidence_threshold = 30  # Full confidence after 30 experiences
        
        # Load persisted markers if available
        if self.persistence_path and self.persistence_path.exists():
            self._load_markers()
    
    # =========================================================================
    # SITUATION HASHING
    # =========================================================================
    
    def _hash_situation(self, features: Dict[str, Any]) -> str:
        """
        Durumu hashle - benzer durumlar benzer hash üretmeli.
        
        Features örnek:
        - danger_level: 0.0-1.0 (quantized to 0.2 buckets)
        - has_target: bool
        - has_agent: bool
        - location_type: str
        - symbols: list
        """
        # Quantize continuous values for generalization
        normalized = {}
        
        # Danger level: 5 bucket (0.0, 0.2, 0.4, 0.6, 0.8)
        danger = features.get('danger_level', 0)
        normalized['danger_bucket'] = round(danger * 5) / 5
        
        # Boolean features
        normalized['has_target'] = bool(features.get('has_target') or features.get('nearest_target'))
        normalized['has_agent'] = bool(features.get('has_agent') or 'AGENT_IN_SIGHT' in features.get('symbols', []))
        
        # High danger symbol
        normalized['high_danger'] = 'DANGER_HIGH' in features.get('symbols', [])
        
        # Location/context (if available)
        normalized['location'] = features.get('location_type', 'unknown')
        
        # Create deterministic hash
        hash_input = json.dumps(normalized, sort_keys=True)
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def _extract_situation_features(self, world_state: Dict[str, Any]) -> Dict[str, Any]:
        """World state'den situation features çıkar"""
        return {
            'danger_level': world_state.get('danger_level', 0),
            'has_target': world_state.get('nearest_target') is not None,
            'has_agent': world_state.get('agents_count', 0) > 0,
            'symbols': world_state.get('symbols', []),
            'location_type': world_state.get('location_type', 'unknown'),
            'objects_count': world_state.get('objects_count', 0),
        }
    
    # =========================================================================
    # ACTION RECORDING
    # =========================================================================
    
    def record_action(
        self,
        action_name: str,
        action_params: Dict[str, Any],
        world_state: Dict[str, Any],
        emotion_state: Dict[str, float],
    ) -> str:
        """
        Yapılan eylemi kaydet, sonucu bekle.
        
        Returns: situation_hash (sonuç kaydı için kullanılacak)
        """
        features = self._extract_situation_features(world_state)
        situation_hash = self._hash_situation(features)
        
        pending = PendingAction(
            action_name=action_name,
            action_params=action_params,
            situation_hash=situation_hash,
            situation_features=features,
            timestamp=time.time(),
            emotion_at_decision=emotion_state,
        )
        
        self.pending_actions.append(pending)
        
        # Limit pending queue
        if len(self.pending_actions) > self.max_pending:
            old = self.pending_actions.pop(0)
            self.logger.debug(
                "[Somatic] Dropped old pending action: %s (timeout)",
                old.action_name
            )
        
        self.logger.debug(
            "[Somatic] Recorded action: %s, situation=%s",
            action_name, situation_hash
        )
        
        return situation_hash
    
    # =========================================================================
    # OUTCOME RECORDING & MARKER UPDATE
    # =========================================================================
    
    def record_outcome(
        self,
        outcome_valence: float,
        outcome_description: str = "",
        action_name: Optional[str] = None,
    ) -> Optional[SomaticMarker]:
        """
        Sonucu kaydet ve marker oluştur/güncelle.
        
        Args:
            outcome_valence: -1 (çok kötü) to +1 (çok iyi)
            outcome_description: "took_damage", "found_reward", etc.
            action_name: Belirli bir eylem için (None = son eylem)
        
        Returns:
            Güncellenen/oluşturulan marker (veya None)
        """
        if not self.pending_actions:
            self.logger.debug("[Somatic] No pending actions for outcome")
            # Still update action experience count
            if action_name:
                self.action_experience_count[action_name] += 1
            return None
        
        # Find matching pending action
        if action_name:
            matching = [p for p in self.pending_actions if p.action_name == action_name]
            if matching:
                pending = matching[-1]
                self.pending_actions.remove(pending)
            else:
                self.logger.debug("[Somatic] No matching pending action: %s", action_name)
                return None
        else:
            pending = self.pending_actions.pop()
        
        # Get or create marker
        situation_markers = self.markers[pending.situation_hash]
        
        if pending.action_name in situation_markers:
            # Reinforce existing marker
            marker = situation_markers[pending.action_name]
            marker.reinforce(outcome_valence, self.learning_rate)
            self.logger.info(
                "[Somatic] Reinforced marker: %s→%s, valence=%.2f→%.2f",
                pending.situation_hash[:6],
                pending.action_name,
                marker.valence - outcome_valence * self.learning_rate,
                marker.valence
            )
        else:
            # Create new marker
            marker = SomaticMarker(
                situation_hash=pending.situation_hash,
                action=pending.action_name,
                valence=outcome_valence,
                strength=0.5,  # Initial strength
                creation_time=time.time(),
                last_activation=time.time(),
                activation_count=1,
                context_tags=list(pending.situation_features.get('symbols', [])),
                original_outcome=outcome_description,
            )
            situation_markers[pending.action_name] = marker
            self.total_markers += 1
            self.action_experience_count[pending.action_name] += 1
            
            self.logger.info(
                "[Somatic] Created marker: %s→%s, valence=%.2f (%s)",
                pending.situation_hash[:6],
                pending.action_name,
                outcome_valence,
                outcome_description
            )
        
        # Publish event
        if self.event_bus:
            self._publish_marker_event(marker, "updated" if marker.activation_count > 1 else "created")
        
        # Auto-save
        if self.persistence_path:
            self._save_markers()
        
        return marker
    
    # =========================================================================
    # BIAS CALCULATION
    # =========================================================================
    
    def get_action_biases(
        self,
        world_state: Dict[str, Any],
        available_actions: List[str],
    ) -> Dict[str, SomaticBias]:
        """
        Mevcut durum için eylem bias'larını hesapla.
        
        Returns:
            {action_name: SomaticBias}
        """
        features = self._extract_situation_features(world_state)
        situation_hash = self._hash_situation(features)
        
        biases = {}
        
        # Exact match markers
        exact_markers = self.markers.get(situation_hash, {})
        
        # Similar situation markers (fuzzy matching)
        similar_markers = self._find_similar_markers(features)
        
        for action in available_actions:
            contributing = []
            total_bias = 0.0
            total_weight = 0.0
            
            # Exact match (full weight)
            if action in exact_markers:
                marker = exact_markers[action]
                marker.decay(self.decay_rate)
                
                weight = marker.strength
                total_bias += marker.valence * weight
                total_weight += weight
                contributing.append(f"exact:{marker.situation_hash[:6]}")
                
                marker.last_activation = time.time()
                self.total_activations += 1
            
            # Similar matches (reduced weight)
            for sim_hash, sim_markers in similar_markers.items():
                if action in sim_markers and sim_hash != situation_hash:
                    marker = sim_markers[action]
                    marker.decay(self.decay_rate)
                    
                    weight = marker.strength * 0.5  # Similar = half weight
                    total_bias += marker.valence * weight
                    total_weight += weight
                    contributing.append(f"similar:{marker.situation_hash[:6]}")
            
            # Normalize
            if total_weight > 0:
                bias_value = total_bias / total_weight
                confidence = min(1.0, total_weight)
            else:
                bias_value = 0.0
                confidence = 0.0
            
            biases[action] = SomaticBias(
                action=action,
                bias_value=bias_value,
                contributing_markers=contributing,
                confidence=confidence,
            )
        
        # Log if significant biases found
        significant = {k: v for k, v in biases.items() if abs(v.bias_value) > 0.1}
        if significant:
            self.logger.debug(
                "[Somatic] Biases for situation %s: %s",
                situation_hash[:6],
                {k: f"{v.bias_value:+.2f}" for k, v in significant.items()}
            )
        
        return biases
    
    def _find_similar_markers(
        self,
        features: Dict[str, Any],
        max_similar: int = 3,
    ) -> Dict[str, Dict[str, SomaticMarker]]:
        """Benzer durumların marker'larını bul"""
        similar = {}
        
        # Similarity based on key features
        target_danger = round(features.get('danger_level', 0) * 5) / 5
        target_has_agent = features.get('has_agent', False)
        
        for sit_hash, markers in self.markers.items():
            if not markers:
                continue
            
            # Get a sample marker to check context
            sample = next(iter(markers.values()))
            
            # Check similarity via context tags
            overlap = len(set(sample.context_tags) & set(features.get('symbols', [])))
            
            if overlap > 0 or target_has_agent:
                similar[sit_hash] = markers
                
                if len(similar) >= max_similar:
                    break
        
        return similar
    
    def apply_bias_to_decisions(
        self,
        action_scores: Dict[str, float],
        world_state: Dict[str, Any],
    ) -> Dict[str, float]:
        """
        Karar skorlarına somatic bias uygula.
        
        Args:
            action_scores: {action: base_score}
            world_state: Mevcut dünya durumu
        
        Returns:
            {action: biased_score}
        """
        biases = self.get_action_biases(world_state, list(action_scores.keys()))
        
        biased_scores = {}
        for action, base_score in action_scores.items():
            bias = biases.get(action)
            if bias and bias.confidence > 0.2:
                # Weighted combination
                bias_contribution = bias.bias_value * self.bias_weight * bias.confidence
                biased_scores[action] = base_score + bias_contribution
                
                if abs(bias_contribution) > 0.1:
                    self.logger.debug(
                        "[Somatic] Bias applied: %s %.2f → %.2f (bias=%.2f)",
                        action, base_score, biased_scores[action], bias_contribution
                    )
            else:
                biased_scores[action] = base_score
        
        self.bias_applications += 1
        return biased_scores
    
    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================
    
    async def on_action_decided(self, event) -> None:
        """Handle planning.action_decided events"""
        action_name = event.data.get('action_name')
        action_params = event.data.get('action_params', {})
        
        # World state from action params or event
        world_state = {
            'danger_level': action_params.get('danger_level', 0),
            'symbols': action_params.get('symbols', []),
            'nearest_target': action_params.get('target_id'),
        }
        
        emotion_state = {
            'valence': event.data.get('current_emotion_valence', 0),
            'arousal': event.data.get('current_emotion_arousal', 0),
        }
        
        self.record_action(action_name, action_params, world_state, emotion_state)
    
    async def on_outcome_received(self, event) -> None:
        """Handle world.outcome_received events"""
        valence = event.data.get('outcome_valence', 0)
        description = event.data.get('outcome_description', '')
        action = event.data.get('action_name')
        
        self.record_outcome(valence, description, action)
    
    def _publish_marker_event(self, marker: SomaticMarker, event_type: str) -> None:
        """Publish somatic marker event"""
        import asyncio
        try:
            from core.event_bus import Event, EventPriority
            
            event = Event(
                type=f'somatic.marker_{event_type}',
                source='somatic_marker_system',
                data={
                    'situation_hash': marker.situation_hash,
                    'action': marker.action,
                    'valence': marker.valence,
                    'strength': marker.strength,
                    'activation_count': marker.activation_count,
                },
                priority=EventPriority.LOW
            )
            
            loop = asyncio.get_event_loop()
            loop.create_task(self.event_bus.publish(event))
        except Exception:
            pass
    
    # =========================================================================
    # PERSISTENCE
    # =========================================================================
    
    def _save_markers(self) -> None:
        """Marker'ları diske kaydet"""
        if not self.persistence_path:
            return
        
        data = {
            'markers': {},
            'stats': {
                'total_markers': self.total_markers,
                'total_activations': self.total_activations,
                'bias_applications': self.bias_applications,
            }
        }
        
        for sit_hash, actions in self.markers.items():
            data['markers'][sit_hash] = {
                action: asdict(marker) for action, marker in actions.items()
            }
        
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.persistence_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_markers(self) -> None:
        """Marker'ları diskten yükle"""
        if not self.persistence_path or not self.persistence_path.exists():
            return
        
        try:
            with open(self.persistence_path, 'r') as f:
                data = json.load(f)
            
            for sit_hash, actions in data.get('markers', {}).items():
                for action, marker_data in actions.items():
                    self.markers[sit_hash][action] = SomaticMarker(**marker_data)
            
            stats = data.get('stats', {})
            self.total_markers = stats.get('total_markers', 0)
            self.total_activations = stats.get('total_activations', 0)
            self.bias_applications = stats.get('bias_applications', 0)
            
            self.logger.info(
                "[Somatic] Loaded %d markers from %s",
                self.total_markers, self.persistence_path
            )
        except Exception as e:
            self.logger.error("[Somatic] Failed to load markers: %s", e)
    
    # =========================================================================
    # STATISTICS & DEBUG
    # =========================================================================
    
    def get_confidence(self, action: str) -> float:
        """Get learned confidence for an action (0-1)"""
        count = self.action_experience_count.get(action, 0)
        return min(1.0, count / self.confidence_threshold)

    def get_stats(self) -> Dict[str, Any]:
        """İstatistikleri döndür"""
        return {
            'total_markers': self.total_markers,
            'total_activations': self.total_activations,
            'bias_applications': self.bias_applications,
            'unique_situations': len(self.markers),
            'pending_actions': len(self.pending_actions),
            'strongest_markers': self._get_strongest_markers(5),
        }
    
    def _get_strongest_markers(self, n: int = 5) -> List[Dict[str, Any]]:
        """En güçlü marker'ları döndür"""
        all_markers = []
        for actions in self.markers.values():
            all_markers.extend(actions.values())
        
        sorted_markers = sorted(all_markers, key=lambda m: abs(m.valence) * m.strength, reverse=True)
        
        return [
            {
                'situation': m.situation_hash[:8],
                'action': m.action,
                'valence': round(m.valence, 2),
                'strength': round(m.strength, 2),
                'activations': m.activation_count,
            }
            for m in sorted_markers[:n]
        ]
    
    def debug_print_markers(self) -> None:
        """Debug: Tüm marker'ları yazdır"""
        print("\n=== SOMATIC MARKERS ===")
        for sit_hash, actions in self.markers.items():
            print(f"\nSituation: {sit_hash}")
            for action, marker in actions.items():
                print(f"  {action}: valence={marker.valence:+.2f}, strength={marker.strength:.2f}, count={marker.activation_count}")
        print("=" * 25)
