"""
Memory Consolidation System for UEM

STM → LTM emotion-tagged transfer with activation-based retrieval.
Based on ACT-R's memory consolidation principles and Damasio's emotional memory theory.

Key Features:
- Activation-based memory decay and retrieval
- Emotion tagging for memories (Somatic Marker integration)
- Salience-based consolidation threshold
- Episodic vs Semantic memory separation
- Sleep-like consolidation cycles
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
import math
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum


class MemoryType(Enum):
    """Memory classification"""
    EPISODIC = "episodic"      # Specific events with time/place
    SEMANTIC = "semantic"      # General knowledge/rules
    PROCEDURAL = "procedural"  # Skills, how-to
    EMOTIONAL = "emotional"    # Emotion-tagged memories


@dataclass
class EmotionTag:
    """Emotion information attached to memory"""
    valence: float = 0.0        # -1 to +1 (negative to positive)
    arousal: float = 0.0        # 0 to 1 (calm to excited)
    dominance: float = 0.0      # -1 to +1 (submissive to dominant)
    emotion_label: str = ""     # "fear", "joy", "anger", etc.
    intensity: float = 0.0      # 0 to 1


@dataclass
class ConsolidatedMemory:
    """A memory item in LTM"""
    memory_id: str
    content: Any
    memory_type: MemoryType
    
    # Temporal info
    created_at: float
    last_accessed: float
    access_count: int = 1
    
    # Activation (ACT-R style)
    base_activation: float = 0.0
    spreading_activation: float = 0.0
    
    # Emotion
    emotion_tag: Optional[EmotionTag] = None
    
    # Context
    context_hash: str = ""
    linked_memories: Set[str] = field(default_factory=set)
    
    # Metadata
    source: str = ""  # "stm_consolidation", "direct", "inference"
    salience_at_encoding: float = 0.0
    
    @property
    def total_activation(self) -> float:
        return self.base_activation + self.spreading_activation
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['memory_type'] = self.memory_type.value
        d['linked_memories'] = list(self.linked_memories)
        if self.emotion_tag:
            d['emotion_tag'] = asdict(self.emotion_tag)
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ConsolidatedMemory':
        data['memory_type'] = MemoryType(data['memory_type'])
        data['linked_memories'] = set(data.get('linked_memories', []))
        if data.get('emotion_tag'):
            data['emotion_tag'] = EmotionTag(**data['emotion_tag'])
        return cls(**data)


class ActivationCalculator:
    """
    ACT-R style activation calculation.
    
    Base-level activation: B_i = ln(sum(t_j^-d)) + beta
    Where t_j is time since jth access, d is decay rate
    """
    
    def __init__(
        self,
        decay_rate: float = 0.5,
        noise_std: float = 0.25,
        retrieval_threshold: float = -1.0,
    ):
        self.decay_rate = decay_rate  # d parameter
        self.noise_std = noise_std
        self.retrieval_threshold = retrieval_threshold
    
    def calculate_base_activation(
        self,
        access_times: List[float],
        current_time: Optional[float] = None,
    ) -> float:
        """
        Calculate base-level activation using ACT-R formula.
        
        B_i = ln(sum(t_j^-d))
        """
        if not access_times:
            return -float('inf')
        
        current_time = current_time or time.time()
        
        total = 0.0
        for t in access_times:
            time_diff = max(current_time - t, 0.001)  # Avoid division by zero
            total += math.pow(time_diff, -self.decay_rate)
        
        if total > 0:
            return math.log(total)
        return -float('inf')
    
    def calculate_spreading_activation(
        self,
        source_activations: Dict[str, float],
        association_weights: Dict[str, float],
        total_source_activation: float = 1.0,
    ) -> float:
        """
        Calculate spreading activation from associated memories.
        
        S_i = sum(W_j * S_ji)
        """
        if not source_activations or not association_weights:
            return 0.0
        
        # Normalize weights
        weight_sum = sum(association_weights.values())
        if weight_sum == 0:
            return 0.0
        
        spreading = 0.0
        for source_id, source_act in source_activations.items():
            weight = association_weights.get(source_id, 0.0)
            normalized_weight = (weight / weight_sum) * total_source_activation
            spreading += normalized_weight * source_act
        
        return spreading
    
    def is_retrievable(self, activation: float) -> bool:
        """Check if activation exceeds retrieval threshold"""
        return activation > self.retrieval_threshold


class LongTermMemory:
    """
    Long-term memory store with activation-based retrieval.
    
    Supports:
    - Episodic memories (specific events)
    - Semantic memories (general knowledge)
    - Emotional tagging
    - Spreading activation retrieval
    """
    
    def __init__(
        self,
        activation_calc: Optional[ActivationCalculator] = None,
        max_memories: int = 10000,
        persistence_path: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.activation_calc = activation_calc or ActivationCalculator()
        self.max_memories = max_memories
        self.persistence_path = persistence_path
        self.logger = logger or logging.getLogger("memory.LTM")
        
        # Storage
        self.memories: Dict[str, ConsolidatedMemory] = {}
        self.access_history: Dict[str, List[float]] = {}  # memory_id -> [access times]
        
        # Indices for fast lookup
        self.type_index: Dict[MemoryType, Set[str]] = {t: set() for t in MemoryType}
        self.context_index: Dict[str, Set[str]] = {}  # context_hash -> memory_ids
        self.emotion_index: Dict[str, Set[str]] = {}  # emotion_label -> memory_ids
        
        # Statistics
        self.total_retrievals = 0
        self.total_stores = 0
        
        # Load from persistence
        if persistence_path:
            self._load_from_disk()
    
    def store(
        self,
        content: Any,
        memory_type: MemoryType,
        emotion_tag: Optional[EmotionTag] = None,
        context_hash: str = "",
        salience: float = 0.5,
        source: str = "direct",
        linked_memories: Optional[Set[str]] = None,
    ) -> ConsolidatedMemory:
        """Store a new memory in LTM"""
        
        # Generate ID
        memory_id = self._generate_id(content, context_hash)
        
        # Check if already exists
        if memory_id in self.memories:
            # Reinforce existing memory
            return self._reinforce_memory(memory_id)
        
        # Create new memory
        now = time.time()
        memory = ConsolidatedMemory(
            memory_id=memory_id,
            content=content,
            memory_type=memory_type,
            created_at=now,
            last_accessed=now,
            access_count=1,
            base_activation=0.0,  # Will be calculated
            emotion_tag=emotion_tag,
            context_hash=context_hash,
            linked_memories=linked_memories or set(),
            source=source,
            salience_at_encoding=salience,
        )
        
        # Initialize access history
        self.access_history[memory_id] = [now]
        
        # Calculate initial activation
        memory.base_activation = self.activation_calc.calculate_base_activation(
            self.access_history[memory_id]
        )
        
        # Store
        self.memories[memory_id] = memory
        self._update_indices(memory)
        
        self.total_stores += 1
        
        # Enforce capacity
        if len(self.memories) > self.max_memories:
            self._evict_lowest_activation()
        
        self.logger.debug(
            "[LTM] Stored memory: %s (type=%s, emotion=%s)",
            memory_id[:8], memory_type.value,
            emotion_tag.emotion_label if emotion_tag else "none"
        )
        
        return memory
    
    def retrieve(
        self,
        query: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        context_hash: Optional[str] = None,
        emotion_label: Optional[str] = None,
        min_activation: Optional[float] = None,
        limit: int = 10,
        update_access: bool = True,
    ) -> List[ConsolidatedMemory]:
        """
        Retrieve memories based on criteria.
        
        Returns memories sorted by activation (highest first).
        """
        candidates = set(self.memories.keys())
        
        # Filter by type
        if memory_type:
            candidates &= self.type_index.get(memory_type, set())
        
        # Filter by context
        if context_hash:
            candidates &= self.context_index.get(context_hash, set())
        
        # Filter by emotion
        if emotion_label:
            candidates &= self.emotion_index.get(emotion_label, set())
        
        # Update activations and filter
        results = []
        now = time.time()
        
        for mem_id in candidates:
            memory = self.memories[mem_id]
            
            # Recalculate activation
            memory.base_activation = self.activation_calc.calculate_base_activation(
                self.access_history.get(mem_id, []),
                now
            )
            
            # Check threshold
            if min_activation is not None:
                if memory.total_activation < min_activation:
                    continue
            elif not self.activation_calc.is_retrievable(memory.total_activation):
                continue
            
            # Content match (simple substring for now)
            if query:
                content_str = str(memory.content).lower()
                if query.lower() not in content_str:
                    continue
            
            results.append(memory)
        
        # Sort by activation
        results.sort(key=lambda m: m.total_activation, reverse=True)
        results = results[:limit]
        
        # Update access times
        if update_access and results:
            for memory in results:
                self._record_access(memory.memory_id)
        
        self.total_retrievals += 1
        
        return results
    
    def retrieve_by_emotion(
        self,
        target_valence: float,
        tolerance: float = 0.3,
        limit: int = 10,
    ) -> List[ConsolidatedMemory]:
        """Retrieve memories with similar emotional valence"""
        results = []
        
        for memory in self.memories.values():
            if memory.emotion_tag:
                diff = abs(memory.emotion_tag.valence - target_valence)
                if diff <= tolerance:
                    results.append((memory, diff))
        
        # Sort by closeness to target valence
        results.sort(key=lambda x: x[1])
        return [m for m, _ in results[:limit]]
    
    def retrieve_emotional_memories(
        self,
        valence_threshold: float = 0.5,
        positive: bool = True,
        limit: int = 10,
    ) -> List[ConsolidatedMemory]:
        """Retrieve strongly emotional memories (positive or negative)"""
        results = []
        
        for memory in self.memories.values():
            if memory.emotion_tag:
                if positive and memory.emotion_tag.valence >= valence_threshold:
                    results.append(memory)
                elif not positive and memory.emotion_tag.valence <= -valence_threshold:
                    results.append(memory)
        
        # Sort by intensity
        results.sort(
            key=lambda m: abs(m.emotion_tag.valence) * m.emotion_tag.intensity,
            reverse=True
        )
        return results[:limit]
    
    def get_linked_memories(
        self,
        memory_id: str,
        depth: int = 1,
    ) -> List[ConsolidatedMemory]:
        """Get memories linked to a specific memory"""
        if memory_id not in self.memories:
            return []
        
        visited = {memory_id}
        to_visit = list(self.memories[memory_id].linked_memories)
        results = []
        
        for _ in range(depth):
            next_level = []
            for linked_id in to_visit:
                if linked_id in visited:
                    continue
                visited.add(linked_id)
                
                if linked_id in self.memories:
                    memory = self.memories[linked_id]
                    results.append(memory)
                    next_level.extend(memory.linked_memories)
            
            to_visit = next_level
        
        return results
    
    def _reinforce_memory(self, memory_id: str) -> ConsolidatedMemory:
        """Reinforce an existing memory (re-encoding)"""
        memory = self.memories[memory_id]
        memory.access_count += 1
        self._record_access(memory_id)
        
        # Recalculate activation
        memory.base_activation = self.activation_calc.calculate_base_activation(
            self.access_history[memory_id]
        )
        
        self.logger.debug("[LTM] Reinforced memory: %s", memory_id[:8])
        return memory
    
    def _record_access(self, memory_id: str) -> None:
        """Record memory access for activation calculation"""
        now = time.time()
        
        if memory_id not in self.access_history:
            self.access_history[memory_id] = []
        
        self.access_history[memory_id].append(now)
        
        if memory_id in self.memories:
            self.memories[memory_id].last_accessed = now
            self.memories[memory_id].access_count += 1
    
    def _update_indices(self, memory: ConsolidatedMemory) -> None:
        """Update lookup indices"""
        # Type index
        self.type_index[memory.memory_type].add(memory.memory_id)
        
        # Context index
        if memory.context_hash:
            if memory.context_hash not in self.context_index:
                self.context_index[memory.context_hash] = set()
            self.context_index[memory.context_hash].add(memory.memory_id)
        
        # Emotion index
        if memory.emotion_tag and memory.emotion_tag.emotion_label:
            label = memory.emotion_tag.emotion_label
            if label not in self.emotion_index:
                self.emotion_index[label] = set()
            self.emotion_index[label].add(memory.memory_id)
    
    def _evict_lowest_activation(self) -> None:
        """Remove memory with lowest activation"""
        if not self.memories:
            return
        
        # Find lowest activation
        lowest_id = None
        lowest_activation = float('inf')
        
        for mem_id, memory in self.memories.items():
            if memory.total_activation < lowest_activation:
                lowest_activation = memory.total_activation
                lowest_id = mem_id
        
        if lowest_id:
            self._remove_memory(lowest_id)
    
    def _remove_memory(self, memory_id: str) -> None:
        """Remove a memory from storage"""
        if memory_id not in self.memories:
            return
        
        memory = self.memories[memory_id]
        
        # Remove from indices
        self.type_index[memory.memory_type].discard(memory_id)
        
        if memory.context_hash in self.context_index:
            self.context_index[memory.context_hash].discard(memory_id)
        
        if memory.emotion_tag and memory.emotion_tag.emotion_label:
            label = memory.emotion_tag.emotion_label
            if label in self.emotion_index:
                self.emotion_index[label].discard(memory_id)
        
        # Remove memory
        del self.memories[memory_id]
        if memory_id in self.access_history:
            del self.access_history[memory_id]
        
        self.logger.debug("[LTM] Evicted memory: %s", memory_id[:8])
    
    def _generate_id(self, content: Any, context: str) -> str:
        """Generate unique memory ID"""
        content_str = json.dumps(content, sort_keys=True, default=str)
        hash_input = f"{content_str}:{context}:{time.time()}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _load_from_disk(self) -> None:
        """Load memories from persistence"""
        import os
        if not self.persistence_path or not os.path.exists(self.persistence_path):
            return
        
        try:
            with open(self.persistence_path, 'r') as f:
                data = json.load(f)
            
            for mem_dict in data.get('memories', []):
                memory = ConsolidatedMemory.from_dict(mem_dict)
                self.memories[memory.memory_id] = memory
                self._update_indices(memory)
            
            self.access_history = data.get('access_history', {})
            
            self.logger.info("[LTM] Loaded %d memories from disk", len(self.memories))
        except Exception as e:
            self.logger.error("[LTM] Failed to load from disk: %s", e)
    
    def save_to_disk(self) -> None:
        """Save memories to persistence"""
        if not self.persistence_path:
            return
        
        try:
            data = {
                'memories': [m.to_dict() for m in self.memories.values()],
                'access_history': self.access_history,
            }
            
            with open(self.persistence_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info("[LTM] Saved %d memories to disk", len(self.memories))
        except Exception as e:
            self.logger.error("[LTM] Failed to save to disk: %s", e)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get LTM statistics"""
        emotion_counts = {}
        for label, ids in self.emotion_index.items():
            emotion_counts[label] = len(ids)
        
        return {
            'total_memories': len(self.memories),
            'episodic_count': len(self.type_index[MemoryType.EPISODIC]),
            'semantic_count': len(self.type_index[MemoryType.SEMANTIC]),
            'emotional_count': len(self.type_index[MemoryType.EMOTIONAL]),
            'procedural_count': len(self.type_index[MemoryType.PROCEDURAL]),
            'emotion_distribution': emotion_counts,
            'total_retrievals': self.total_retrievals,
            'total_stores': self.total_stores,
        }


class MemoryConsolidator:
    """
    Handles STM → LTM consolidation.
    
    Consolidation criteria:
    1. High salience items (important events)
    2. Emotionally significant items
    3. Frequently accessed items
    4. Items with strong context associations
    
    Integrates with SomaticMarkerSystem for emotional memory.
    """
    
    def __init__(
        self,
        ltm: LongTermMemory,
        consolidation_threshold: float = 0.6,
        emotion_boost: float = 0.2,
        access_threshold: int = 3,
        consolidation_interval: float = 60.0,  # seconds
        logger: Optional[logging.Logger] = None,
    ):
        self.ltm = ltm
        self.consolidation_threshold = consolidation_threshold
        self.emotion_boost = emotion_boost
        self.access_threshold = access_threshold
        self.consolidation_interval = consolidation_interval
        self.logger = logger or logging.getLogger("memory.Consolidator")
        
        # Pending items from STM
        self.pending_items: List[Dict[str, Any]] = []
        
        # Current emotion context (from EmotionCore)
        self.current_emotion: Optional[EmotionTag] = None
        
        # Statistics
        self.consolidation_cycles = 0
        self.items_consolidated = 0
        self.items_rejected = 0
        
        # Running state
        self._running = False
        self._consolidation_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start consolidation background task"""
        self._running = True
        self._consolidation_task = asyncio.create_task(self._consolidation_loop())
        self.logger.info("[Consolidator] Started with interval=%.1fs", self.consolidation_interval)
    
    async def stop(self) -> None:
        """Stop consolidation task"""
        self._running = False
        if self._consolidation_task:
            self._consolidation_task.cancel()
            try:
                await self._consolidation_task
            except asyncio.CancelledError:
                pass
        self.logger.info("[Consolidator] Stopped")
    
    async def _consolidation_loop(self) -> None:
        """Background consolidation cycle"""
        while self._running:
            try:
                await asyncio.sleep(self.consolidation_interval)
                await self.consolidation_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("[Consolidator] Error in cycle: %s", e)
    
    def add_to_pending(
        self,
        content: Any,
        salience: float,
        access_count: int = 1,
        context_hash: str = "",
        emotion_state: Optional[Dict[str, float]] = None,
        memory_type: MemoryType = MemoryType.EPISODIC,
        source: str = "stm",
    ) -> None:
        """Add an item from STM to pending consolidation queue"""
        
        # Create emotion tag from current state
        emotion_tag = None
        if emotion_state:
            emotion_tag = EmotionTag(
                valence=emotion_state.get('valence', 0),
                arousal=emotion_state.get('arousal', 0),
                dominance=emotion_state.get('dominance', 0),
                emotion_label=emotion_state.get('emotion', ''),
                intensity=abs(emotion_state.get('valence', 0)) * emotion_state.get('arousal', 0.5),
            )
        elif self.current_emotion:
            emotion_tag = self.current_emotion
        
        self.pending_items.append({
            'content': content,
            'salience': salience,
            'access_count': access_count,
            'context_hash': context_hash,
            'emotion_tag': emotion_tag,
            'memory_type': memory_type,
            'source': source,
            'added_at': time.time(),
        })
        
        self.logger.debug(
            "[Consolidator] Added pending item (salience=%.2f, emotion=%s)",
            salience, emotion_tag.emotion_label if emotion_tag else "none"
        )
    
    def update_emotion_context(self, emotion_state: Dict[str, float]) -> None:
        """Update current emotion context for tagging new memories"""
        self.current_emotion = EmotionTag(
            valence=emotion_state.get('valence', 0),
            arousal=emotion_state.get('arousal', 0),
            dominance=emotion_state.get('dominance', 0),
            emotion_label=emotion_state.get('emotion', ''),
            intensity=abs(emotion_state.get('valence', 0)) * emotion_state.get('arousal', 0.5),
        )
    
    async def consolidation_cycle(self) -> Dict[str, int]:
        """
        Run one consolidation cycle.
        
        Evaluates pending items and consolidates those meeting criteria.
        """
        self.consolidation_cycles += 1
        
        consolidated = 0
        rejected = 0
        
        items_to_process = self.pending_items[:]
        self.pending_items = []
        
        for item in items_to_process:
            score = self._calculate_consolidation_score(item)
            
            if score >= self.consolidation_threshold:
                # Consolidate to LTM
                memory = self.ltm.store(
                    content=item['content'],
                    memory_type=item['memory_type'],
                    emotion_tag=item['emotion_tag'],
                    context_hash=item['context_hash'],
                    salience=item['salience'],
                    source=f"consolidation_{item['source']}",
                )
                
                consolidated += 1
                self.items_consolidated += 1
                
                self.logger.debug(
                    "[Consolidator] Consolidated: %s (score=%.2f)",
                    memory.memory_id[:8], score
                )
            else:
                rejected += 1
                self.items_rejected += 1
        
        self.logger.info(
            "[Consolidator] Cycle %d: consolidated=%d, rejected=%d",
            self.consolidation_cycles, consolidated, rejected
        )
        
        return {'consolidated': consolidated, 'rejected': rejected}
    
    def _calculate_consolidation_score(self, item: Dict[str, Any]) -> float:
        """
        Calculate consolidation score for an item.
        
        Score = base_salience + emotion_boost + access_boost
        """
        score = item['salience']
        
        # Emotion boost
        if item['emotion_tag']:
            # Strong emotions (high absolute valence * arousal) get boosted
            emotion_intensity = abs(item['emotion_tag'].valence) * max(0.5, item['emotion_tag'].arousal)
            score += self.emotion_boost * emotion_intensity
        
        # Access frequency boost
        if item['access_count'] >= self.access_threshold:
            access_boost = min(0.2, (item['access_count'] - self.access_threshold) * 0.05)
            score += access_boost
        
        # Recency penalty (older pending items slightly less likely)
        age = time.time() - item['added_at']
        if age > 300:  # More than 5 minutes old
            score -= 0.05
        
        return min(1.0, max(0.0, score))
    
    async def force_consolidate(self, content: Any, emotion_tag: Optional[EmotionTag] = None) -> ConsolidatedMemory:
        """Force immediate consolidation of important memory"""
        return self.ltm.store(
            content=content,
            memory_type=MemoryType.EPISODIC,
            emotion_tag=emotion_tag or self.current_emotion,
            salience=1.0,
            source="forced_consolidation",
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get consolidator statistics"""
        return {
            'consolidation_cycles': self.consolidation_cycles,
            'items_consolidated': self.items_consolidated,
            'items_rejected': self.items_rejected,
            'pending_count': len(self.pending_items),
            'consolidation_rate': (
                self.items_consolidated / max(1, self.items_consolidated + self.items_rejected)
            ),
            'ltm_stats': self.ltm.get_stats(),
        }


class MemoryConsolidationEventHandler:
    """
    Event bus integration for memory consolidation.
    
    Subscriptions:
    - memory.stm_item_added → Add to pending consolidation
    - emotion.state_changed → Update emotion context
    - perception.significant_event → Trigger immediate consolidation
    
    Publications:
    - memory.consolidated → When item moves to LTM
    - memory.ltm_retrieved → When memory is retrieved
    """
    
    def __init__(
        self,
        consolidator: MemoryConsolidator,
        event_bus: Any,
        logger: Optional[logging.Logger] = None,
    ):
        self.consolidator = consolidator
        self.event_bus = event_bus
        self.logger = logger or logging.getLogger("memory.ConsolidationHandler")
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Setup event subscriptions"""
        if self._initialized or self.event_bus is None:
            return
        
        await self.event_bus.subscribe('memory.stm_item_added', self._on_stm_item)
        await self.event_bus.subscribe('emotion.state_changed', self._on_emotion_changed)
        await self.event_bus.subscribe('perception.significant_event', self._on_significant_event)
        await self.event_bus.subscribe('somatic.marker_created', self._on_somatic_marker)
        
        self._initialized = True
        self.logger.info("[ConsolidationHandler] Event subscriptions initialized")
    
    async def _on_stm_item(self, event) -> None:
        """Handle new STM item"""
        self.consolidator.add_to_pending(
            content=event.data.get('content'),
            salience=event.data.get('salience', 0.5),
            access_count=event.data.get('access_count', 1),
            context_hash=event.data.get('context_hash', ''),
            emotion_state=event.data.get('emotion_state'),
            memory_type=MemoryType(event.data.get('memory_type', 'episodic')),
            source='stm_event',
        )
    
    async def _on_emotion_changed(self, event) -> None:
        """Update emotion context"""
        self.consolidator.update_emotion_context({
            'valence': event.data.get('valence', 0),
            'arousal': event.data.get('arousal', 0),
            'dominance': event.data.get('dominance', 0),
            'emotion': event.data.get('emotion', ''),
        })
    
    async def _on_significant_event(self, event) -> None:
        """Immediately consolidate significant events"""
        emotion_tag = None
        if 'emotion' in event.data:
            emotion_tag = EmotionTag(
                valence=event.data.get('valence', 0),
                arousal=event.data.get('arousal', 0),
                emotion_label=event.data.get('emotion', ''),
                intensity=1.0,
            )
        
        memory = await self.consolidator.force_consolidate(
            content=event.data,
            emotion_tag=emotion_tag,
        )
        
        self.logger.info(
            "[ConsolidationHandler] Significant event consolidated: %s",
            memory.memory_id[:8]
        )
    
    async def _on_somatic_marker(self, event) -> None:
        """
        Consolidate somatic marker as emotional memory.
        
        This links the Somatic Marker System with LTM.
        """
        emotion_tag = EmotionTag(
            valence=event.data.get('valence', 0),
            arousal=0.5,  # Default arousal for somatic markers
            emotion_label='somatic',
            intensity=event.data.get('strength', 0.5),
        )
        
        # Store as emotional memory type
        self.consolidator.add_to_pending(
            content={
                'type': 'somatic_marker',
                'action': event.data.get('action'),
                'situation_hash': event.data.get('situation_hash'),
                'original_outcome': event.data.get('original_outcome'),
            },
            salience=0.7 + (abs(event.data.get('valence', 0)) * 0.3),
            emotion_state={
                'valence': event.data.get('valence', 0),
                'arousal': 0.5,
                'emotion': 'somatic',
            },
            memory_type=MemoryType.EMOTIONAL,
            source='somatic_marker',
        )
