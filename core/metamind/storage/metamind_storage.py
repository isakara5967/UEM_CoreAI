import json
"""
MetaMind v1.9 - Storage Module
==============================

DB operations for MetaMind data:
- Episodes
- Patterns
- MetaEvents
- MetaState snapshots

⚠️ Alice notu: Confidence değerleri her zaman kaydedilmeli
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..types import (
    Episode, MetaPattern, MetaEvent, MetaState,
    PatternType, EventType, Severity
)

logger = logging.getLogger("UEM.MetaMind.Storage")


class MetaMindStorage:
    """
    MetaMind verilerinin DB operasyonları.
    
    Kullanım:
        storage = MetaMindStorage(db_connection)
        await storage.save_episode(episode)
        await storage.save_pattern(pattern)
    """
    
    def __init__(self, db=None):
        """
        Args:
            db: PostgreSQL async connection (asyncpg veya mevcut DB wrapper)
        """
        self.db = db
        self._initialized = False
    
    async def initialize(self) -> bool:
        """DB bağlantısını kontrol et."""
        if self.db is None:
            logger.warning("MetaMindStorage: No database connection")
            return False
        self._initialized = True
        logger.debug("MetaMindStorage: Initialized")
        return True
    
    # ============================================================
    # EPISODE OPERATIONS
    # ============================================================
    
    async def save_episode(self, episode: Episode) -> bool:
        """
        Episode kaydet veya güncelle.
        
        Args:
            episode: Episode instance
            
        Returns:
            True if successful
        """
        if not self._initialized:
            logger.warning("MetaMindStorage not initialized")
            return False
        
        try:
            await self.db.execute("""
                INSERT INTO core.metamind_episodes (
                    episode_id, run_id, episode_seq, start_cycle_id, end_cycle_id,
                    start_time, end_time, semantic_tag, boundary_reason, 
                    cycle_count, summary
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (episode_id) DO UPDATE SET
                    end_cycle_id = EXCLUDED.end_cycle_id,
                    end_time = EXCLUDED.end_time,
                    cycle_count = EXCLUDED.cycle_count,
                    summary = EXCLUDED.summary
            """,
                episode.episode_id,
                episode.run_id,
                episode.episode_seq,
                episode.start_cycle_id,
                episode.end_cycle_id,
                episode.start_time,
                episode.end_time,
                episode.semantic_tag,
                episode.boundary_reason,
                episode.cycle_count,
                json.dumps(episode.summary or {})
            )
            logger.debug(f"Episode saved: {episode.episode_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save episode: {e}")
            return False
    
    async def get_episode(self, episode_id: str) -> Optional[Episode]:
        """Episode getir."""
        if not self._initialized:
            return None
        
        try:
            row = await self.db.fetchrow(
                "SELECT * FROM core.metamind_episodes WHERE episode_id = $1",
                episode_id
            )
            if row:
                return self._row_to_episode(row)
            return None
        except Exception as e:
            logger.error(f"Failed to get episode: {e}")
            return None
    
    async def get_active_episode(self, run_id: str) -> Optional[Episode]:
        """Aktif (açık) episode getir."""
        if not self._initialized:
            return None
        
        try:
            row = await self.db.fetchrow("""
                SELECT * FROM core.metamind_episodes 
                WHERE run_id = $1 AND end_cycle_id IS NULL
                ORDER BY episode_seq DESC LIMIT 1
            """, run_id)
            if row:
                return self._row_to_episode(row)
            return None
        except Exception as e:
            logger.error(f"Failed to get active episode: {e}")
            return None
    
    async def get_episodes_by_run(self, run_id: str) -> List[Episode]:
        """Run'a ait tüm episode'ları getir."""
        if not self._initialized:
            return []
        
        try:
            rows = await self.db.fetch(
                "SELECT * FROM core.metamind_episodes WHERE run_id = $1 ORDER BY episode_seq",
                run_id
            )
            return [self._row_to_episode(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get episodes: {e}")
            return []
    
    def _row_to_episode(self, row) -> Episode:
        """DB row'u Episode'a çevir."""
        return Episode(
            episode_id=row['episode_id'],
            run_id=row['run_id'],
            episode_seq=row['episode_seq'],
            start_cycle_id=row['start_cycle_id'],
            end_cycle_id=row['end_cycle_id'],
            start_time=row['start_time'],
            end_time=row['end_time'],
            semantic_tag=row['semantic_tag'],
            boundary_reason=row['boundary_reason'],
            cycle_count=row['cycle_count'],
            summary=row['summary'] or {}
        )
    
    # ============================================================
    # PATTERN OPERATIONS
    # ============================================================
    
    async def save_pattern(self, pattern: MetaPattern) -> bool:
        """
        Pattern kaydet veya güncelle.
        Aynı pattern varsa frequency artır, last_seen güncelle.
        """
        if not self._initialized:
            return False
        
        try:
            # Upsert: varsa güncelle, yoksa ekle
            await self.db.execute("""
                INSERT INTO core.metamind_patterns (
                    id, run_id, episode_id, pattern_type, pattern_key,
                    frequency, confidence, first_seen, last_seen, data
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (run_id, pattern_type, pattern_key) DO UPDATE SET
                    frequency = core.metamind_patterns.frequency + 1,
                    confidence = GREATEST(core.metamind_patterns.confidence, EXCLUDED.confidence),
                    last_seen = EXCLUDED.last_seen,
                    data = EXCLUDED.data
            """,
                pattern.id,
                pattern.run_id,
                pattern.episode_id,
                pattern.pattern_type,
                pattern.pattern_key,
                pattern.frequency,
                pattern.confidence,
                pattern.first_seen,
                pattern.last_seen,
                json.dumps(pattern.data or {})
            )
            logger.debug(f"Pattern saved: {pattern.pattern_type}:{pattern.pattern_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to save pattern: {e}")
            return False
    
    async def get_patterns_by_episode(
        self, 
        episode_id: str,
        pattern_type: Optional[str] = None
    ) -> List[MetaPattern]:
        """Episode'a ait pattern'leri getir."""
        if not self._initialized:
            return []
        
        try:
            if pattern_type:
                rows = await self.db.fetch("""
                    SELECT * FROM core.metamind_patterns 
                    WHERE episode_id = $1 AND pattern_type = $2
                    ORDER BY frequency DESC
                """, episode_id, pattern_type)
            else:
                rows = await self.db.fetch("""
                    SELECT * FROM core.metamind_patterns 
                    WHERE episode_id = $1
                    ORDER BY frequency DESC
                """, episode_id)
            
            return [self._row_to_pattern(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get patterns: {e}")
            return []
    
    async def get_top_patterns(
        self, 
        run_id: str,
        pattern_type: Optional[str] = None,
        limit: int = 10
    ) -> List[MetaPattern]:
        """En sık pattern'leri getir."""
        if not self._initialized:
            return []
        
        try:
            if pattern_type:
                rows = await self.db.fetch("""
                    SELECT * FROM core.metamind_patterns 
                    WHERE run_id = $1 AND pattern_type = $2
                    ORDER BY frequency DESC LIMIT $3
                """, run_id, pattern_type, limit)
            else:
                rows = await self.db.fetch("""
                    SELECT * FROM core.metamind_patterns 
                    WHERE run_id = $1
                    ORDER BY frequency DESC LIMIT $2
                """, run_id, limit)
            
            return [self._row_to_pattern(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get top patterns: {e}")
            return []
    
    def _row_to_pattern(self, row) -> MetaPattern:
        """DB row'u MetaPattern'e çevir."""
        return MetaPattern(
            id=str(row['id']),
            created_at=row['created_at'],
            pattern_type=row['pattern_type'],
            pattern_key=row['pattern_key'],
            frequency=row['frequency'],
            confidence=row['confidence'],
            first_seen=row['first_seen'],
            last_seen=row['last_seen'],
            run_id=row['run_id'],
            episode_id=row['episode_id'],
            data=row['data'] or {}
        )
    
    # ============================================================
    # META EVENT OPERATIONS
    # ============================================================
    
    async def save_meta_event(self, event: MetaEvent) -> bool:
        """MetaEvent kaydet."""
        if not self._initialized:
            return False
        
        try:
            await self.db.execute("""
                INSERT INTO core.metamind_meta_events (
                    id, run_id, cycle_id, episode_id, event_type,
                    severity, source, message, data
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                event.id,
                event.run_id,
                event.cycle_id,
                event.episode_id,
                event.event_type,
                event.severity,
                event.source,
                event.message,
                json.dumps(event.data or {})
            )
            logger.debug(f"MetaEvent saved: {event.event_type} - {event.severity}")
            return True
        except Exception as e:
            logger.error(f"Failed to save meta event: {e}")
            return False
    
    async def get_meta_events(
        self,
        run_id: str,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[MetaEvent]:
        """MetaEvent'leri getir."""
        if not self._initialized:
            return []
        
        try:
            query = "SELECT * FROM core.metamind_meta_events WHERE run_id = $1"
            params = [run_id]
            
            if severity:
                query += f" AND severity = ${len(params) + 1}"
                params.append(severity)
            
            if event_type:
                query += f" AND event_type = ${len(params) + 1}"
                params.append(event_type)
            
            query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1}"
            params.append(limit)
            
            rows = await self.db.fetch(query, *params)
            return [self._row_to_event(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get meta events: {e}")
            return []
    
    async def get_critical_events(self, run_id: str, limit: int = 20) -> List[MetaEvent]:
        """Kritik event'leri getir."""
        return await self.get_meta_events(
            run_id, 
            severity=Severity.CRITICAL.value, 
            limit=limit
        )
    
    def _row_to_event(self, row) -> MetaEvent:
        """DB row'u MetaEvent'e çevir."""
        return MetaEvent(
            id=str(row['id']),
            created_at=row['created_at'],
            event_type=row['event_type'],
            severity=row['severity'],
            source=row['source'],
            message=row['message'],
            run_id=row['run_id'],
            cycle_id=row['cycle_id'],
            episode_id=row['episode_id'],
            data=row['data'] or {}
        )
    
    # ============================================================
    # META STATE SNAPSHOT OPERATIONS
    # ============================================================
    
    async def save_meta_state_snapshot(
        self,
        run_id: str,
        cycle_id: int,
        meta_state: MetaState,
        episode_id: Optional[str] = None
    ) -> bool:
        """
        MetaState snapshot'ını metamind_cycle_summary'e kaydet.
        
        ⚠️ Alice notu: Confidence değerleri de kaydediliyor.
        """
        if not self._initialized:
            return False
        
        try:
            await self.db.execute("""
                INSERT INTO core.metamind_cycle_summary (
                    run_id, cycle_id, episode_id,
                    global_cognitive_health, global_health_confidence,
                    emotional_stability_index, emotional_stability_confidence,
                    ethical_alignment_index, ethical_alignment_confidence,
                    exploration_bias_index, exploration_bias_confidence,
                    failure_pressure_index, failure_pressure_confidence,
                    memory_health_index, memory_health_confidence,
                    calculated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, NOW())
                ON CONFLICT (run_id, cycle_id) DO UPDATE SET
                    episode_id = EXCLUDED.episode_id,
                    global_cognitive_health = EXCLUDED.global_cognitive_health,
                    global_health_confidence = EXCLUDED.global_health_confidence,
                    emotional_stability_index = EXCLUDED.emotional_stability_index,
                    emotional_stability_confidence = EXCLUDED.emotional_stability_confidence,
                    ethical_alignment_index = EXCLUDED.ethical_alignment_index,
                    ethical_alignment_confidence = EXCLUDED.ethical_alignment_confidence,
                    exploration_bias_index = EXCLUDED.exploration_bias_index,
                    exploration_bias_confidence = EXCLUDED.exploration_bias_confidence,
                    failure_pressure_index = EXCLUDED.failure_pressure_index,
                    failure_pressure_confidence = EXCLUDED.failure_pressure_confidence,
                    memory_health_index = EXCLUDED.memory_health_index,
                    memory_health_confidence = EXCLUDED.memory_health_confidence,
                    calculated_at = NOW()
            """,
                run_id,
                cycle_id,
                episode_id,
                meta_state.global_cognitive_health.value,
                meta_state.global_cognitive_health.confidence,
                meta_state.emotional_stability.value,
                meta_state.emotional_stability.confidence,
                meta_state.ethical_alignment.value,
                meta_state.ethical_alignment.confidence,
                meta_state.exploration_bias.value,
                meta_state.exploration_bias.confidence,
                meta_state.failure_pressure.value,
                meta_state.failure_pressure.confidence,
                meta_state.memory_health.value,
                meta_state.memory_health.confidence
            )
            
            # Log with confidence (Alice notu)
            logger.debug(f"MetaState saved: cycle {cycle_id} - {meta_state.to_log_string()}")
            return True
        except Exception as e:
            logger.error(f"Failed to save meta state snapshot: {e}")
            return False
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    async def get_episode_stats(self, run_id: str) -> Dict[str, Any]:
        """Episode istatistikleri."""
        if not self._initialized:
            return {}
        
        try:
            row = await self.db.fetchrow("""
                SELECT 
                    COUNT(*) as total_episodes,
                    COUNT(*) FILTER (WHERE end_cycle_id IS NULL) as active_episodes,
                    AVG(cycle_count) as avg_cycle_count,
                    MAX(episode_seq) as last_episode_seq
                FROM core.metamind_episodes
                WHERE run_id = $1
            """, run_id)
            
            return {
                'total_episodes': row['total_episodes'] or 0,
                'active_episodes': row['active_episodes'] or 0,
                'avg_cycle_count': float(row['avg_cycle_count'] or 0),
                'last_episode_seq': row['last_episode_seq'] or 0,
            }
        except Exception as e:
            logger.error(f"Failed to get episode stats: {e}")
            return {}
    
    async def get_pattern_stats(self, run_id: str) -> Dict[str, Any]:
        """Pattern istatistikleri."""
        if not self._initialized:
            return {}
        
        try:
            rows = await self.db.fetch("""
                SELECT 
                    pattern_type,
                    COUNT(*) as count,
                    SUM(frequency) as total_frequency,
                    AVG(confidence) as avg_confidence
                FROM core.metamind_patterns
                WHERE run_id = $1
                GROUP BY pattern_type
            """, run_id)
            
            return {
                row['pattern_type']: {
                    'count': row['count'],
                    'total_frequency': row['total_frequency'],
                    'avg_confidence': float(row['avg_confidence'] or 0),
                }
                for row in rows
            }
        except Exception as e:
            logger.error(f"Failed to get pattern stats: {e}")
            return {}
    
    # ============================================================
    # CLEANUP / RETENTION
    # ============================================================
    
    async def cleanup_old_data(
        self,
        episodes_days: int = 90,
        patterns_days: int = 180,
        events_days: int = 30
    ) -> Dict[str, int]:
        """
        Eski verileri temizle.
        
        Returns:
            Dict of deleted counts per table
        """
        if not self._initialized:
            return {}
        
        deleted = {}
        
        try:
            # Episodes
            result = await self.db.execute(f"""
                DELETE FROM core.metamind_episodes 
                WHERE end_time < NOW() - INTERVAL '{episodes_days} days'
                AND end_time IS NOT NULL
            """)
            deleted['episodes'] = int(result.split()[-1]) if result else 0
            
            # Patterns
            result = await self.db.execute(f"""
                DELETE FROM core.metamind_patterns 
                WHERE last_seen < NOW() - INTERVAL '{patterns_days} days'
            """)
            deleted['patterns'] = int(result.split()[-1]) if result else 0
            
            # Events
            result = await self.db.execute(f"""
                DELETE FROM core.metamind_meta_events 
                WHERE created_at < NOW() - INTERVAL '{events_days} days'
            """)
            deleted['events'] = int(result.split()[-1]) if result else 0
            
            logger.info(f"Cleanup completed: {deleted}")
            return deleted
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return deleted


# ============================================================
# FACTORY
# ============================================================

def create_metamind_storage(db=None) -> MetaMindStorage:
    """MetaMindStorage factory."""
    return MetaMindStorage(db=db)


__all__ = ['MetaMindStorage', 'create_metamind_storage']
