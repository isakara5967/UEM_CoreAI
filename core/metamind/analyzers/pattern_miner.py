"""
MetaMind v1.9 - Pattern Miner
=============================

Davranış pattern'lerini tespit eder:
1. Action frequency (hangi aksiyon ne kadar sık)
2. Action sequences (N-gram, örn: flee->wait->flee)
3. Emotion trends (valence declining/rising)
4. Context-action correlations (basit)

Pattern türleri:
- ACTION_SEQUENCE: "flee->wait->flee"
- ACTION_FREQUENCY: "flee: 38%"
- EMOTION_TREND: "valence_declining"
- CORRELATION: "danger>0.7 -> flee 85%"
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque

from ..types import MetaPattern, PatternType

logger = logging.getLogger("UEM.MetaMind.PatternMiner")


@dataclass
class PatternMinerConfig:
    """Pattern miner konfigürasyonu."""
    # Sequence mining
    sequence_length: int = 3          # N-gram uzunluğu
    min_frequency: int = 3            # Minimum tekrar sayısı
    min_confidence: float = 0.5       # Minimum güven skoru
    
    # History size
    action_history_size: int = 100    # Son N aksiyon
    emotion_history_size: int = 50    # Son N emotion
    
    # Limits
    max_patterns_per_type: int = 100  # Tip başına max pattern
    
    # Trend detection
    trend_window: int = 10            # Trend hesaplama penceresi
    trend_threshold: float = 0.1      # Min değişim for trend
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'PatternMinerConfig':
        """Config dict'ten oluştur."""
        pm_config = config.get('pattern_mining', {})
        return cls(
            sequence_length=pm_config.get('action_sequence_length', 3),
            min_frequency=pm_config.get('min_frequency', 3),
            min_confidence=pm_config.get('min_confidence', 0.5),
            max_patterns_per_type=pm_config.get('max_patterns_per_type', 100),
        )


class PatternMiner:
    """
    Davranış pattern'lerini tespit eden miner.
    
    Her N cycle'da (default: 10) çalışır ve:
    1. Action frequency hesaplar
    2. Action sequences bulur
    3. Emotion trend'lerini tespit eder
    
    Kullanım:
        miner = PatternMiner(config)
        miner.initialize(run_id)
        
        # Her cycle'da veri ekle
        miner.add_cycle_data(action, valence, arousal, context)
        
        # Her 10 cycle'da mining yap
        patterns = miner.mine()
    """
    
    def __init__(
        self,
        config: Optional[PatternMinerConfig] = None,
        storage=None,
    ):
        """
        Args:
            config: PatternMinerConfig instance
            storage: MetaMindStorage for persistence
        """
        self.config = config or PatternMinerConfig()
        self.storage = storage
        
        # Run context
        self._run_id: Optional[str] = None
        self._episode_id: Optional[str] = None
        
        # History buffers
        self._action_history: deque = deque(maxlen=self.config.action_history_size)
        self._valence_history: deque = deque(maxlen=self.config.emotion_history_size)
        self._arousal_history: deque = deque(maxlen=self.config.emotion_history_size)
        self._context_history: deque = deque(maxlen=self.config.action_history_size)
        
        # Pattern storage (in-memory)
        self._action_counts: Dict[str, int] = defaultdict(int)
        self._sequence_counts: Dict[str, int] = defaultdict(int)
        self._patterns: Dict[str, MetaPattern] = {}
        
        # Stats
        self._total_cycles: int = 0
        
        logger.debug("PatternMiner initialized")
    
    def initialize(self, run_id: str, episode_id: Optional[str] = None) -> None:
        """Yeni run için initialize."""
        self._run_id = run_id
        self._episode_id = episode_id
        self._total_cycles = 0
        
        # Clear history
        self._action_history.clear()
        self._valence_history.clear()
        self._arousal_history.clear()
        self._context_history.clear()
        
        # Clear counts (optionally keep patterns across episodes)
        self._action_counts.clear()
        self._sequence_counts.clear()
        
        logger.debug(f"PatternMiner initialized for run: {run_id}")
    
    def set_episode(self, episode_id: str) -> None:
        """Episode değiştiğinde güncelle."""
        self._episode_id = episode_id
    
    def add_cycle_data(
        self,
        action: str,
        valence: float,
        arousal: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Yeni cycle verisi ekle.
        
        Args:
            action: Seçilen aksiyon (flee, attack, wait, etc.)
            valence: Emotion valence (-1 to 1)
            arousal: Emotion arousal (0 to 1)
            context: Opsiyonel context bilgisi (danger_level, etc.)
        """
        self._total_cycles += 1
        
        # Add to history
        self._action_history.append(action)
        self._valence_history.append(valence)
        self._arousal_history.append(arousal)
        self._context_history.append(context or {})
        
        # Update action counts
        self._action_counts[action] += 1
        
        # Update sequence counts (if enough history)
        if len(self._action_history) >= self.config.sequence_length:
            seq = self._get_last_sequence()
            self._sequence_counts[seq] += 1
    
    def mine(self) -> List[MetaPattern]:
        """
        Pattern mining çalıştır.
        
        Returns:
            List of discovered patterns
        """
        patterns: List[MetaPattern] = []
        
        # 1. Action frequency patterns
        patterns.extend(self._mine_action_frequency())
        
        # 2. Action sequence patterns
        patterns.extend(self._mine_action_sequences())
        
        # 3. Emotion trend patterns
        patterns.extend(self._mine_emotion_trends())
        
        # Store patterns
        for pattern in patterns:
            self._patterns[f"{pattern.pattern_type}:{pattern.pattern_key}"] = pattern
        
        # Persist to storage (async)
        if self.storage and patterns:
            self._persist_patterns(patterns)
        
        logger.debug(f"PatternMiner found {len(patterns)} patterns")
        return patterns
    
    def _mine_action_frequency(self) -> List[MetaPattern]:
        """Action frequency pattern'leri bul."""
        patterns = []
        total = sum(self._action_counts.values())
        
        if total == 0:
            return patterns
        
        for action, count in self._action_counts.items():
            frequency = count / total
            
            # Min frequency check
            if count >= self.config.min_frequency:
                pattern = MetaPattern(
                    pattern_type=PatternType.ACTION_FREQUENCY.value,
                    pattern_key=action,
                    frequency=count,
                    confidence=frequency,  # Frequency as confidence
                    run_id=self._run_id,
                    episode_id=self._episode_id,
                    data={
                        'percentage': round(frequency * 100, 1),
                        'total_actions': total,
                    },
                )
                patterns.append(pattern)
        
        # Sort by frequency, limit
        patterns.sort(key=lambda p: p.frequency, reverse=True)
        return patterns[:self.config.max_patterns_per_type]
    
    def _mine_action_sequences(self) -> List[MetaPattern]:
        """Action sequence pattern'leri bul (N-gram)."""
        patterns = []
        total_sequences = sum(self._sequence_counts.values())
        
        if total_sequences == 0:
            return patterns
        
        for seq, count in self._sequence_counts.items():
            # Min frequency check
            if count >= self.config.min_frequency:
                confidence = count / total_sequences
                
                # Min confidence check
                if confidence >= self.config.min_confidence:
                    pattern = MetaPattern(
                        pattern_type=PatternType.ACTION_SEQUENCE.value,
                        pattern_key=seq,
                        frequency=count,
                        confidence=confidence,
                        run_id=self._run_id,
                        episode_id=self._episode_id,
                        data={
                            'sequence_length': self.config.sequence_length,
                            'total_sequences': total_sequences,
                        },
                    )
                    patterns.append(pattern)
        
        # Sort by frequency, limit
        patterns.sort(key=lambda p: p.frequency, reverse=True)
        return patterns[:self.config.max_patterns_per_type]
    
    def _mine_emotion_trends(self) -> List[MetaPattern]:
        """Emotion trend pattern'leri bul."""
        patterns = []
        
        # Valence trend
        valence_trend, valence_confidence = self._calculate_trend(
            list(self._valence_history)
        )
        
        if valence_trend and valence_confidence >= self.config.min_confidence:
            pattern = MetaPattern(
                pattern_type=PatternType.EMOTION_TREND.value,
                pattern_key=f"valence_{valence_trend}",
                frequency=1,
                confidence=valence_confidence,
                run_id=self._run_id,
                episode_id=self._episode_id,
                data={
                    'trend_type': 'valence',
                    'direction': valence_trend,
                    'window_size': len(self._valence_history),
                },
            )
            patterns.append(pattern)
        
        # Arousal trend
        arousal_trend, arousal_confidence = self._calculate_trend(
            list(self._arousal_history)
        )
        
        if arousal_trend and arousal_confidence >= self.config.min_confidence:
            pattern = MetaPattern(
                pattern_type=PatternType.EMOTION_TREND.value,
                pattern_key=f"arousal_{arousal_trend}",
                frequency=1,
                confidence=arousal_confidence,
                run_id=self._run_id,
                episode_id=self._episode_id,
                data={
                    'trend_type': 'arousal',
                    'direction': arousal_trend,
                    'window_size': len(self._arousal_history),
                },
            )
            patterns.append(pattern)
        
        return patterns
    
    def _get_last_sequence(self) -> str:
        """Son N aksiyon sequence'ini string olarak döndür."""
        n = self.config.sequence_length
        actions = list(self._action_history)[-n:]
        return "->".join(actions)
    
    def _calculate_trend(self, values: List[float]) -> Tuple[Optional[str], float]:
        """
        Trend hesapla.
        
        Returns:
            (trend_direction, confidence)
            trend_direction: "rising" | "falling" | "stable" | None
            confidence: 0.0 to 1.0
        """
        if len(values) < self.config.trend_window:
            return None, 0.0
        
        # Use last N values
        window = values[-self.config.trend_window:]
        
        if len(window) < 2:
            return None, 0.0
        
        # Simple linear trend
        first_half = window[:len(window)//2]
        second_half = window[len(window)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        diff = avg_second - avg_first
        
        # Determine trend
        if diff > self.config.trend_threshold:
            trend = "rising"
            confidence = min(1.0, abs(diff) / 0.5)
        elif diff < -self.config.trend_threshold:
            trend = "falling"
            confidence = min(1.0, abs(diff) / 0.5)
        else:
            trend = "stable"
            confidence = 1.0 - abs(diff) / self.config.trend_threshold
        
        return trend, confidence
    
    def _persist_patterns(self, patterns: List[MetaPattern]) -> None:
        """Pattern'leri storage'a kaydet."""
        import asyncio
        
        async def save_all():
            for pattern in patterns:
                await self.storage.save_pattern(pattern)
        
        try:
            asyncio.create_task(save_all())
        except Exception as e:
            logger.error(f"Failed to persist patterns: {e}")
    
    # ============================================================
    # PUBLIC API
    # ============================================================
    
    def get_top_patterns(
        self,
        pattern_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[MetaPattern]:
        """En sık pattern'leri getir."""
        patterns = list(self._patterns.values())
        
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        
        patterns.sort(key=lambda p: p.frequency, reverse=True)
        return patterns[:limit]
    
    def get_action_distribution(self) -> Dict[str, float]:
        """Action dağılımını döndür."""
        total = sum(self._action_counts.values())
        if total == 0:
            return {}
        
        return {
            action: count / total
            for action, count in self._action_counts.items()
        }
    
    def get_dominant_action(self) -> Optional[str]:
        """En sık kullanılan aksiyonu döndür."""
        if not self._action_counts:
            return None
        return max(self._action_counts.items(), key=lambda x: x[1])[0]
    
    def get_stats(self) -> Dict[str, Any]:
        """Mining istatistikleri."""
        return {
            'total_cycles': self._total_cycles,
            'unique_actions': len(self._action_counts),
            'unique_sequences': len(self._sequence_counts),
            'patterns_found': len(self._patterns),
            'action_history_size': len(self._action_history),
            'emotion_history_size': len(self._valence_history),
        }
    
    def reset(self) -> None:
        """Miner state sıfırla."""
        self._action_history.clear()
        self._valence_history.clear()
        self._arousal_history.clear()
        self._context_history.clear()
        self._action_counts.clear()
        self._sequence_counts.clear()
        self._patterns.clear()
        self._total_cycles = 0
        logger.debug("PatternMiner reset")


# ============================================================
# FACTORY
# ============================================================

def create_pattern_miner(
    config: Optional[Dict[str, Any]] = None,
    storage=None,
) -> PatternMiner:
    """Factory function."""
    pm_config = PatternMinerConfig.from_dict(config or {})
    return PatternMiner(config=pm_config, storage=storage)


__all__ = ['PatternMiner', 'PatternMinerConfig', 'create_pattern_miner']
