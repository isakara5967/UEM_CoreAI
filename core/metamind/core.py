"""
MetaMind v1.9 - Core Module (Phase 3 Entegre)
==============================================

MetaMind'ın ana orchestrator'ı ve scheduler'ı.

Phase 3 Entegrasyonu:
- MicroCycleAnalyzer: Her cycle'da anomaly detection
- PatternMiner: Her 10 cycle'da pattern mining

Scheduler modları:
- online: Cycle path içinde (max 2ms)
- online_async: Cycle sonrası async
- offline_batch: Run sonu (v2.0)

🔧 FIX v3: Tüm episode işlemleri ASYNC yapıldı (FK hatası düzeltmesi)
"""

import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
import yaml
import os

from .types import (
    MetaState, MetaEvent, MetaInsight, Episode,
    MetricsSnapshot, Job, JobMode, EventType, Severity
)
from .meta_state import MetaStateCalculator, MetaStateConfig
from .episodes import EpisodeManager, EpisodeConfig
from .adapters import MetricsAdapter
from .storage import MetaMindStorage
from .analyzers import MicroCycleAnalyzer, PatternMiner, create_cycle_analyzer, create_pattern_miner
from .insights import InsightGenerator, create_insight_generator
from .pipelines import SocialHealthPipeline, create_social_pipeline
from .evaluation import EpisodeEvaluator, create_episode_evaluator

logger = logging.getLogger("UEM.MetaMind.Core")


@dataclass
class MetaMindConfig:
    """MetaMind ana konfigürasyonu."""
    version: str = "1.9.0"
    
    # Episode config
    episode: EpisodeConfig = field(default_factory=EpisodeConfig)
    
    # MetaState config
    meta_state: MetaStateConfig = field(default_factory=MetaStateConfig)
    
    # Scheduler config
    online_budget_ms: float = 2.0
    jobs: Dict[str, Dict] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'MetaMindConfig':
        """Config dict'ten oluştur."""
        metamind = config.get('metamind', config)
        scheduler = metamind.get('scheduler', {})
        
        return cls(
            version=metamind.get('version', '1.9.0'),
            episode=EpisodeConfig.from_dict(metamind),
            meta_state=MetaStateConfig.from_dict(metamind),
            online_budget_ms=scheduler.get('online_budget_ms', 2.0),
            jobs=scheduler.get('jobs', {}),
        )
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'MetaMindConfig':
        """YAML dosyasından yükle."""
        try:
            with open(yaml_path, 'r') as f:
                config = yaml.safe_load(f)
            return cls.from_dict(config)
        except Exception as e:
            logger.warning(f"Failed to load config from {yaml_path}: {e}")
            return cls()


class MetaMindCore:
    """
    MetaMind v1.9 Ana Koordinatör (Phase 3 Entegre).
    
    Sorumluluklar:
    1. Episode lifecycle yönetimi
    2. MetaState hesaplama ve tracking
    3. Job scheduling (online/async/batch)
    4. Storage koordinasyonu
    5. Event emission
    6. Anomaly detection (Phase 3)
    7. Pattern mining (Phase 3)
    
    Kullanım:
        metamind = MetaMindCore(config_path="config/metamind.yaml")
        await metamind.initialize(run_id)  # 🔧 ASYNC
        
        # Her cycle sonunda
        await metamind.on_cycle_end(cycle_id, cycle_data, action_result)  # 🔧 ASYNC
        
        # Run sonunda
        await metamind.on_run_end()
    """
    
    def __init__(
        self,
        config: Optional[MetaMindConfig] = None,
        config_path: Optional[str] = None,
        storage: Optional[MetaMindStorage] = None,
        metrics_adapter: Optional[MetricsAdapter] = None,
    ):
        """
        Args:
            config: MetaMindConfig instance
            config_path: Path to metamind.yaml
            storage: MetaMindStorage instance (optional)
            metrics_adapter: MetricsAdapter instance (optional)
        """
        # Config yükle
        if config:
            self.config = config
        elif config_path and os.path.exists(config_path):
            self.config = MetaMindConfig.from_yaml(config_path)
        else:
            self.config = MetaMindConfig()
        
        # Components
        self.storage = storage
        self.metrics_adapter = metrics_adapter
        
        # Episode manager
        self.episode_manager = EpisodeManager(
            config=self.config.episode,
            storage=storage,
            on_episode_start=self._on_episode_start,
            on_episode_end=self._on_episode_end,
        )
        
        # MetaState calculator
        self.meta_state_calculator = MetaStateCalculator(self.config.meta_state)
        
        # === Phase 3: Analyzers ===
        self.cycle_analyzer = MicroCycleAnalyzer(
            on_event=self._handle_analyzer_event,
        )
        self.pattern_miner = PatternMiner(storage=storage)
        self.insight_generator = InsightGenerator(storage=storage)
        self.episode_evaluator = EpisodeEvaluator()
        self.social_pipeline = SocialHealthPipeline()
        
        # Current state
        self._run_id: Optional[str] = None
        self._current_cycle: int = 0
        self._current_meta_state: Optional[MetaState] = None
        self._initialized: bool = False
        
        # Scheduler
        self._jobs: Dict[str, Job] = {}
        self._setup_jobs()
        
        # Performance tracking
        self._last_cycle_time_ms: float = 0.0
        self._total_online_time_ms: float = 0.0
        
        logger.info(f"MetaMindCore v{self.config.version} created (with Phase 3 analyzers)")
    
    def _setup_jobs(self) -> None:
        """Scheduler job'larını kur."""
        job_configs = self.config.jobs
        
        # Default jobs (config'te yoksa)
        default_jobs = {
            'meta_state_update': {'period_cycles': 1, 'mode': 'online', 'target_ms': 0.5},
            'anomaly_check': {'period_cycles': 1, 'mode': 'online', 'target_ms': 0.5},
            'pattern_miner': {'period_cycles': 10, 'mode': 'online_async', 'target_ms': 50},
            'episode_check': {'period_cycles': 100, 'mode': 'online_async', 'target_ms': 20},
            'insight_generator': {'period_cycles': 50, 'mode': 'online_async', 'target_ms': 100},
        }
        
        # Merge with config
        all_jobs = {**default_jobs, **job_configs}
        
        for name, cfg in all_jobs.items():
            if isinstance(cfg, dict):
                self._jobs[name] = Job(
                    name=name,
                    period_cycles=cfg.get('period_cycles', 1),
                    mode=cfg.get('mode', JobMode.ONLINE.value),
                    target_ms=cfg.get('target_ms', 1.0),
                    enabled=cfg.get('enabled', True),
                )
        
        logger.debug(f"Scheduler setup: {len(self._jobs)} jobs")
    
    async def initialize(self, run_id: str) -> None:
        """
        Yeni run için initialize et.
        
        🔧 FIX v3: ASYNC - Episode'u await ile başlatır (FK hatası düzeltmesi)
        
        Args:
            run_id: Current run ID
        """
        self._run_id = run_id
        self._current_cycle = 0
        self._current_meta_state = None
        
        # Episode manager initialize
        self.episode_manager.initialize(run_id)
        
        # 🔧 FIX v3: İlk episode'u ASYNC başlat
        await self.episode_manager.start_episode(
            start_cycle_id=1,
            semantic_tag="run_start",
            boundary_reason="run_start",
        )
        
        # MetaState calculator reset
        self.meta_state_calculator.reset()
        
        # === Phase 3: Analyzer context ===
        self.cycle_analyzer.set_context(run_id)
        self.pattern_miner.initialize(run_id)
        self.insight_generator.set_context(run_id)
        self.episode_evaluator.reset()
        self.social_pipeline.initialize(run_id)
        
        # Reset job counters
        for job in self._jobs.values():
            job.last_run_cycle = 0
            job.last_duration_ms = 0.0
        
        self._initialized = True
        logger.info(f"MetaMindCore initialized for run: {run_id}")
    
    async def on_cycle_end(
        self,
        cycle_id: int,
        cycle_data: Dict[str, Any],
        action_result: Any = None,
        empathy_results: List[Any] = None,
    ) -> Optional[MetaState]:
        """
        Her cycle sonunda çağrılır.
        
        🔧 FIX v3: ASYNC - Episode boundary'de await kullanır
        
        Args:
            cycle_id: Current cycle number
            cycle_data: Cycle'dan gelen veriler
            action_result: ActionResult (optional)
            
        Returns:
            Current MetaState or None
        """
        if not self._initialized:
            logger.warning("MetaMindCore not initialized")
            return None
        
        start_time = time.perf_counter()
        
        # === SOCIAL HEALTH - Process empathy results ===
        if empathy_results:
            try:
                self.social_pipeline.process_empathy_results(empathy_results)
            except Exception as e:
                logger.warning(f"Social pipeline error: {e}")
        self._current_cycle = cycle_id
        
        # === ONLINE JOBS ===
        online_jobs = [j for j in self._jobs.values() 
                       if j.mode == JobMode.ONLINE.value and j.should_run(cycle_id)]
        
        for job in online_jobs:
            job_start = time.perf_counter()
            
            try:
                if job.name == 'meta_state_update':
                    await self._run_meta_state_update(cycle_data, cycle_id)
                elif job.name == 'anomaly_check':
                    self._run_anomaly_check(cycle_data, cycle_id)
            except Exception as e:
                logger.error(f"Job {job.name} failed: {e}")
            
            job_duration = (time.perf_counter() - job_start) * 1000
            job.record_run(cycle_id, job_duration)
            
            # Performance warning
            if job.is_over_budget():
                logger.warning(
                    f"Job {job.name} over budget: {job_duration:.2f}ms > {job.target_ms}ms"
                )
        
        # === EPISODE BOUNDARY CHECK ===
        # 🔧 FIX v3: ASYNC boundary handling
        if self.episode_manager.check_boundary(cycle_id):
            await self._handle_episode_boundary(cycle_id)
        
        # === ONLINE ASYNC JOBS (fire and forget) ===
        async_jobs = [j for j in self._jobs.values()
                      if j.mode == JobMode.ONLINE_ASYNC.value and j.should_run(cycle_id)]
        
        if async_jobs:
            try:
                asyncio.create_task(self._run_async_jobs(async_jobs, cycle_data, cycle_id))
            except RuntimeError:
                # No running event loop
                pass
        
        # Performance tracking
        self._last_cycle_time_ms = (time.perf_counter() - start_time) * 1000
        self._total_online_time_ms += self._last_cycle_time_ms
        
        # Budget check
        if self._last_cycle_time_ms > self.config.online_budget_ms:
            logger.warning(
                f"MetaMind cycle over budget: {self._last_cycle_time_ms:.2f}ms > "
                f"{self.config.online_budget_ms}ms"
            )
        
        return self._current_meta_state
    
    async def _run_meta_state_update(self, cycle_data: Dict[str, Any], cycle_id: int) -> None:
        """MetaState hesapla ve güncelle."""
        # === Phase 3: PatternMiner'a cycle data ekle ===
        action = cycle_data.get('action', 'unknown')
        valence = cycle_data.get('valence', 0.0)
        arousal = cycle_data.get('arousal', 0.5)
        self.pattern_miner.add_cycle_data(action, valence, arousal, cycle_data)
        
        # MetricsSnapshot al
        if self.metrics_adapter:
            snapshot = self.metrics_adapter.get_snapshot(cycle_data, cycle_id)
        else:
            # Fallback: cycle_data'dan basit snapshot
            snapshot = MetricsSnapshot(
                cycle_id=cycle_id,
                coherence_score=cycle_data.get('coherence', 0.5),
                efficiency_score=cycle_data.get('efficiency', 0.5),
                quality_score=cycle_data.get('quality', 0.5),
                trust_score=cycle_data.get('trust', 0.5),
                failure_streak=cycle_data.get('failure_streak', 0),
                action_diversity=cycle_data.get('action_diversity', 0.5),
                valence_trend=cycle_data.get('valence', 0.0),
                arousal_trend=cycle_data.get('arousal', 0.0),
            )
        
        # MetaState hesapla
        self._current_meta_state = self.meta_state_calculator.compute_full_state(
            snapshot=snapshot,
            run_id=self._run_id,
            cycle_id=cycle_id,
            episode_id=self.episode_manager.get_current_episode_id(),
        )
        
        # === DB'ye kaydet ===
        if self.storage and self._current_meta_state:
            try:
                await self.storage.save_meta_state_snapshot(
                    run_id=self._run_id,
                    cycle_id=cycle_id,
                    meta_state=self._current_meta_state,
                    episode_id=self.episode_manager.get_current_episode_id(),
                )
            except Exception as e:
                logger.warning(f"Failed to save meta state snapshot: {e}")
    
    def _run_anomaly_check(self, cycle_data: Dict[str, Any], cycle_id: int) -> None:
        """Anomali kontrolü - MicroCycleAnalyzer kullanır."""
        # Update episode context
        episode_id = self.episode_manager.get_current_episode_id()
        self.cycle_analyzer.set_context(self._run_id, episode_id)
        
        # MetricsSnapshot al
        snapshot = None
        if self.metrics_adapter:
            snapshot = self.metrics_adapter.get_snapshot(cycle_data, cycle_id)
        
        # Analyze - bu otomatik olarak event emit eder
        anomalies = self.cycle_analyzer.analyze(
            cycle_data=cycle_data,
            snapshot=snapshot,
            meta_state=self._current_meta_state,
            cycle_id=cycle_id,
        )
        
        if anomalies:
            logger.debug(f"Cycle {cycle_id}: {len(anomalies)} anomalies detected")
    
    async def _handle_episode_boundary(self, cycle_id: int) -> None:
        """
        Episode boundary işle.
        
        🔧 FIX v3: ASYNC - await ile episode kaydet (FK hatası düzeltmesi)
        """
        # Mevcut episode'u kapat
        if self.episode_manager.has_active_episode:
            await self.episode_manager.end_current_episode(
                end_cycle_id=cycle_id,
                summary={'meta_state': self._current_meta_state.to_summary_dict() if self._current_meta_state else {}},
            )
        
        # Yeni episode başlat
        await self.episode_manager.start_episode(start_cycle_id=cycle_id + 1)
        
        # Episode boundary event
        self._emit_event(
            event_type=EventType.EPISODE_BOUNDARY,
            severity=Severity.INFO,
            message=f"New episode started at cycle {cycle_id + 1}",
            cycle_id=cycle_id,
        )
    
    async def _run_async_jobs(
        self,
        jobs: List[Job],
        cycle_data: Dict[str, Any],
        cycle_id: int,
    ) -> None:
        """Async job'ları çalıştır."""
        for job in jobs:
            job_start = time.perf_counter()
            
            try:
                if job.name == 'pattern_miner':
                    await self._run_pattern_mining(cycle_data, cycle_id)
                elif job.name == 'insight_generator':
                    await self._run_insight_generation(cycle_id)
                elif job.name == 'episode_check':
                    pass  # Already handled in sync
            except Exception as e:
                logger.error(f"Async job {job.name} failed: {e}")
            
            job_duration = (time.perf_counter() - job_start) * 1000
            job.record_run(cycle_id, job_duration)
    
    async def _run_pattern_mining(self, cycle_data: Dict[str, Any], cycle_id: int) -> None:
        """Pattern mining - PatternMiner.mine() çağırır."""
        try:
            # Episode context güncelle
            episode_id = self.episode_manager.get_current_episode_id()
            self.pattern_miner.set_episode(episode_id)
            
            # Mining yap
            patterns = self.pattern_miner.mine()
            
            if patterns and self.storage:
                for pattern in patterns:
                    await self.storage.save_pattern(pattern)
            if patterns:
                logger.debug(f"Cycle {cycle_id}: {len(patterns)} patterns found")
                
                # Pattern detected event'leri emit et (top 3)
                for pattern in patterns[:3]:
                    self._emit_event(
                        event_type=EventType.PATTERN_DETECTED,
                        severity=Severity.INFO,
                        message=f"Pattern: {pattern.pattern_key} (freq={pattern.frequency})",
                        cycle_id=cycle_id,
                        data={
                            'pattern_type': pattern.pattern_type,
                            'pattern_key': pattern.pattern_key,
                            'frequency': pattern.frequency,
                            'confidence': pattern.confidence,
                        },
                    )
        except Exception as e:
            logger.error(f"Pattern mining failed: {e}")
    
    async def _run_insight_generation(self, cycle_id: int) -> None:
        """Insight generation - her 50 cycle'da summary üret."""
        try:
            # Context güncelle
            episode_id = self.episode_manager.get_current_episode_id()
            self.insight_generator.set_context(self._run_id, episode_id)
            
            # Cycle summary üret
            insight = self.insight_generator.generate_cycle_summary(
                cycle_id=cycle_id,
                meta_state=self._current_meta_state,
                anomalies=None,
            )
            
            if insight:
                logger.debug(f"Cycle {cycle_id}: Insight generated")
                
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
    
    def _emit_event(
        self,
        event_type: EventType,
        severity: Severity,
        message: str,
        cycle_id: int,
        data: Optional[Dict] = None,
    ) -> None:
        """MetaEvent oluştur ve kaydet."""
        import json
        
        event = MetaEvent(
            event_type=event_type.value,
            severity=severity.value,
            source="metamind_core",
            message=message,
            run_id=self._run_id,
            cycle_id=cycle_id,
            episode_id=self.episode_manager.get_current_episode_id(),
            data=data or {},
        )
        
        # Storage'a kaydet (async)
        if self.storage:
            try:
                asyncio.create_task(self.storage.save_meta_event(event))
            except RuntimeError:
                # No running loop
                pass
        
        # Log
        if severity == Severity.CRITICAL:
            logger.error(f"[MetaEvent] {message}")
        elif severity == Severity.WARNING:
            logger.warning(f"[MetaEvent] {message}")
        else:
            logger.debug(f"[MetaEvent] {message}")
    
    def _handle_analyzer_event(self, event: MetaEvent) -> None:
        """MicroCycleAnalyzer'dan gelen event'leri işle."""
        # Storage'a kaydet
        if self.storage:
            try:
                asyncio.create_task(self.storage.save_meta_event(event))
            except RuntimeError:
                # No running loop
                pass
        
        # Log
        if event.severity == Severity.CRITICAL.value:
            logger.error(f"[Analyzer] {event.message}")
        elif event.severity == Severity.WARNING.value:
            logger.warning(f"[Analyzer] {event.message}")
    
    def _on_episode_start(self, episode: Episode) -> None:
        """Episode start callback."""
        logger.debug(f"Episode started callback: {episode.episode_id}")
    
    def _on_episode_end(self, episode: Episode) -> None:
        """Episode end callback."""
        logger.debug(f"Episode ended callback: {episode.episode_id} ({episode.cycle_count} cycles)")
    
    # ============================================================
    # PUBLIC API
    # ============================================================
    
    def get_meta_state(self) -> Optional[MetaState]:
        """Current MetaState döndür."""
        return self._current_meta_state
    
    def get_current_episode(self) -> Optional[Episode]:
        """Current Episode döndür."""
        return self.episode_manager.get_current_episode()
    
    def set_storage(self, storage: MetaMindStorage) -> None:
        """Storage'ı sonradan set et (DB bağlantısı kurulduktan sonra)."""
        self.storage = storage
        if self.episode_manager:
            self.episode_manager.storage = storage
        # Phase 3: PatternMiner storage
        if self.pattern_miner:
            self.pattern_miner.storage = storage
        logger.debug("MetaMindCore: Storage set")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Performance istatistikleri."""
        return {
            'last_cycle_time_ms': self._last_cycle_time_ms,
            'total_online_time_ms': self._total_online_time_ms,
            'budget_ms': self.config.online_budget_ms,
            'cycles_processed': self._current_cycle,
            'jobs': {
                name: {
                    'last_duration_ms': job.last_duration_ms,
                    'target_ms': job.target_ms,
                    'over_budget': job.is_over_budget(),
                }
                for name, job in self._jobs.items()
            },
            # Phase 3 stats
            'pattern_miner_stats': self.pattern_miner.get_stats() if self.pattern_miner else {},
        }
    
    async def on_run_end(self) -> None:
        """Run bitişinde çağrılır."""
        # Final episode'u kapat
        await self.episode_manager.on_run_end(self._current_cycle)
        
        # Stats log
        stats = self.get_performance_stats()
        logger.info(
            f"MetaMind run ended: {stats['cycles_processed']} cycles, "
            f"avg time: {stats['total_online_time_ms'] / max(1, stats['cycles_processed']):.2f}ms"
        )
        
        self._initialized = False
    
    def on_run_end_sync(self) -> None:
        """Run bitişi (sync version)."""
        if self.episode_manager.has_active_episode:
            self.episode_manager.end_current_episode_sync(self._current_cycle)
        
        stats = self.get_performance_stats()
        logger.info(f"MetaMind run ended (sync): {stats['cycles_processed']} cycles")
        self._initialized = False


# ============================================================
# FACTORY
# ============================================================

def create_metamind_core(
    config_path: str = "config/metamind.yaml",
    storage: Optional[MetaMindStorage] = None,
    metrics_adapter: Optional[MetricsAdapter] = None,
) -> MetaMindCore:
    """
    MetaMindCore factory.
    
    Args:
        config_path: Path to metamind.yaml
        storage: MetaMindStorage instance
        metrics_adapter: MetricsAdapter instance
        
    Returns:
        Configured MetaMindCore instance
    """
    return MetaMindCore(
        config_path=config_path,
        storage=storage,
        metrics_adapter=metrics_adapter,
    )


__all__ = ['MetaMindCore', 'MetaMindConfig', 'create_metamind_core']
