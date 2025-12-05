"""
MetaMind v1.9 - Episode Manager (FIXED)
=======================================

Episode lifecycle yönetimi:
- Otomatik boundary detection (her N cycle)
- Event-based override (v2.0 için hazır)
- Episode açma/kapama
- Summary hesaplama

⚠️ Alice Notları:
- window_cycles ASLA hardcode olmayacak, config'ten gelecek
- check_boundary() içinde magic number YASAK

🔧 FIX: Sync versiyonlara storage yazma eklendi
🔧 FIX v2: fire-and-forget → bekleyerek kaydetme (FK hatası düzeltmesi)
"""

import logging
import asyncio
import concurrent.futures
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

from .types import Episode, BoundaryReason, MetaState

logger = logging.getLogger("UEM.MetaMind.Episodes")


@dataclass
class EpisodeConfig:
    """Episode yönetim konfigürasyonu."""
    # ⚠️ Alice notu: Bu değer config'ten gelmeli, hardcode DEĞİL
    window_cycles: int = 100
    
    boundary_reasons: list = None
    
    def __post_init__(self):
        if self.boundary_reasons is None:
            self.boundary_reasons = ["time_window", "event_override", "run_end", "goal_complete"]
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'EpisodeConfig':
        """Config dict'ten oluştur."""
        episode_config = config.get('episode', {})
        return cls(
            window_cycles=episode_config.get('window_cycles', 100),
            boundary_reasons=episode_config.get('boundary_reasons'),
        )


class EpisodeManager:
    """
    Episode lifecycle yönetimi.
    
    Episode = Cycle grupları (default: 100 cycle = 1 episode)
    
    Boundary türleri:
    - time_window: Her N cycle'da otomatik (config'ten)
    - event_override: Manuel tetikleme (v2.0)
    - run_end: Run bitişinde
    - goal_complete: Hedef tamamlandığında (v2.0)
    
    Kullanım:
        manager = EpisodeManager(config, storage)
        
        # Her cycle'da kontrol et
        if manager.check_boundary(current_cycle):
            await manager.end_current_episode(current_cycle, summary)
            await manager.start_episode(current_cycle + 1)
    
    ⚠️ Alice notu: check_boundary() içinde 100 gibi magic number YASAK!
    """
    
    def __init__(
        self, 
        config: Optional[EpisodeConfig] = None,
        storage=None,
        on_episode_start: Optional[Callable] = None,
        on_episode_end: Optional[Callable] = None,
    ):
        """
        Args:
            config: EpisodeConfig instance
            storage: MetaMindStorage instance (optional)
            on_episode_start: Callback when episode starts
            on_episode_end: Callback when episode ends
        """
        self.config = config or EpisodeConfig()
        self.storage = storage
        self.on_episode_start = on_episode_start
        self.on_episode_end = on_episode_end
        
        # Current state
        self._current_episode: Optional[Episode] = None
        self._run_id: Optional[str] = None
        self._episode_seq: int = 0
        self._cycles_in_episode: int = 0
        
        logger.debug(f"EpisodeManager initialized with window_cycles={self.config.window_cycles}")
    
    def initialize(self, run_id: str) -> None:
        """
        Yeni run için initialize et.
        
        Args:
            run_id: Current run ID
        """
        self._run_id = run_id
        self._episode_seq = 0
        self._cycles_in_episode = 0
        self._current_episode = None
        logger.info(f"EpisodeManager initialized for run: {run_id}")
    
    def check_boundary(self, current_cycle: int) -> bool:
        """
        Episode boundary'e ulaşıldı mı kontrol et.
        
        ⚠️ Alice notu: Burada self.config.window_cycles kullanılmalı,
        100 gibi magic number YASAK!
        
        Args:
            current_cycle: Current cycle number
            
        Returns:
            True if boundary reached
        """
        # ⚠️ KRİTİK: Magic number yok, config'ten al
        window_cycles = self.config.window_cycles
        
        self._cycles_in_episode += 1
        
        # Time-based boundary check
        if self._cycles_in_episode >= window_cycles:
            logger.debug(
                f"Episode boundary reached: {self._cycles_in_episode} >= {window_cycles}"
            )
            return True
        
        return False
    
    async def start_episode(
        self, 
        start_cycle_id: int,
        semantic_tag: str = "auto_window",
        boundary_reason: str = BoundaryReason.TIME_WINDOW.value,
    ) -> Episode:
        """
        Yeni episode başlat.
        
        Args:
            start_cycle_id: Episode'un başladığı cycle
            semantic_tag: Episode etiketi
            boundary_reason: Neden başlatıldı
            
        Returns:
            New Episode instance
        """
        if not self._run_id:
            raise RuntimeError("EpisodeManager not initialized. Call initialize(run_id) first.")
        
        # Yeni episode oluştur
        self._episode_seq += 1
        self._cycles_in_episode = 0
        
        episode = Episode(
            run_id=self._run_id,
            episode_seq=self._episode_seq,
            start_cycle_id=start_cycle_id,
            semantic_tag=semantic_tag,
            boundary_reason=boundary_reason,
        )
        
        self._current_episode = episode
        
        # Storage'a kaydet
        if self.storage:
            await self.storage.save_episode(episode)
        
        # Callback
        if self.on_episode_start:
            try:
                self.on_episode_start(episode)
            except Exception as e:
                logger.error(f"on_episode_start callback failed: {e}")
        
        logger.info(
            f"Episode started: {episode.episode_id} "
            f"(cycle {start_cycle_id}, reason={boundary_reason})"
        )
        
        return episode
    
    async def end_current_episode(
        self,
        end_cycle_id: int,
        summary: Optional[Dict[str, Any]] = None,
        meta_state: Optional[MetaState] = None,
    ) -> Optional[Episode]:
        """
        Mevcut episode'u kapat.
        
        Args:
            end_cycle_id: Episode'un bittiği cycle
            summary: Episode özet verileri
            meta_state: Episode sonu MetaState
            
        Returns:
            Closed Episode or None if no active episode
        """
        if not self._current_episode:
            logger.warning("No active episode to end")
            return None
        
        episode = self._current_episode
        
        # Summary hazırla
        if summary is None:
            summary = {}
        
        # MetaState'i summary'e ekle
        if meta_state:
            summary['meta_state'] = meta_state.to_summary_dict()
            summary['low_confidence_metrics'] = meta_state.get_low_confidence_metrics()
        
        # Episode'u kapat
        episode.close(end_cycle_id, summary)
        
        # Storage'a kaydet
        if self.storage:
            await self.storage.save_episode(episode)
        
        # Callback
        if self.on_episode_end:
            try:
                self.on_episode_end(episode)
            except Exception as e:
                logger.error(f"on_episode_end callback failed: {e}")
        
        logger.info(
            f"Episode ended: {episode.episode_id} "
            f"(cycles {episode.start_cycle_id}-{end_cycle_id}, "
            f"count={episode.cycle_count})"
        )
        
        self._current_episode = None
        return episode
    
    def get_current_episode(self) -> Optional[Episode]:
        """Aktif episode'u döndür."""
        return self._current_episode
    
    def get_current_episode_id(self) -> Optional[str]:
        """Aktif episode ID'sini döndür."""
        return self._current_episode.episode_id if self._current_episode else None
    
    @property
    def has_active_episode(self) -> bool:
        """Aktif episode var mı?"""
        return self._current_episode is not None
    
    @property
    def cycles_in_current_episode(self) -> int:
        """Mevcut episode'daki cycle sayısı."""
        return self._cycles_in_episode
    
    @property
    def cycles_until_boundary(self) -> int:
        """Boundary'e kaç cycle kaldı?"""
        return max(0, self.config.window_cycles - self._cycles_in_episode)
    
    # ============================================================
    # EVENT-BASED OVERRIDE (v2.0 için hazır)
    # ============================================================
    
    async def on_event_override(
        self,
        current_cycle: int,
        reason: str = BoundaryReason.EVENT_OVERRIDE.value,
        semantic_tag: Optional[str] = None,
    ) -> Episode:
        """
        Manuel episode boundary tetikle.
        
        v2.0'da goal completion, scenario change vb. için kullanılacak.
        
        Args:
            current_cycle: Current cycle number
            reason: Boundary reason
            semantic_tag: Optional semantic tag
            
        Returns:
            New Episode after boundary
        """
        logger.info(f"Event override triggered at cycle {current_cycle}: {reason}")
        
        # Mevcut episode'u kapat
        if self._current_episode:
            await self.end_current_episode(current_cycle)
        
        # Yeni episode başlat
        tag = semantic_tag or f"event_{reason}"
        return await self.start_episode(
            start_cycle_id=current_cycle + 1,
            semantic_tag=tag,
            boundary_reason=reason,
        )
    
    async def on_run_end(self, final_cycle: int) -> Optional[Episode]:
        """
        Run bitişinde episode'u kapat.
        
        Args:
            final_cycle: Son cycle number
            
        Returns:
            Closed Episode or None
        """
        if self._current_episode:
            return await self.end_current_episode(
                end_cycle_id=final_cycle,
                summary={'reason': 'run_end'},
            )
        return None
    
    # ============================================================
    # SYNC VERSIONS (for non-async contexts)
    # 🔧 FIX v2: Bekleyerek kaydet (FK hatası düzeltmesi)
    # ============================================================
    
    def _save_episode_sync(self, episode: Episode) -> None:
        """
        Episode'u storage'a HEMEN kaydet (bekleyerek).
        
        🔧 FIX v2: fire-and-forget DEĞİL - bekleyerek kaydediyor.
        Çünkü sonraki event'ler episode_id FK'ya bağlı.
        Episode DB'de olmadan event yazılamaz!
        """
        if not self.storage:
            return
        
        if not getattr(self.storage, '_initialized', False):
            logger.debug("Storage not initialized, skipping save")
            return
        
        async def save():
            await self.storage.save_episode(episode)
        
        try:
            # Running loop var mı kontrol et
            try:
                loop = asyncio.get_running_loop()
                # Running loop var - yeni thread'de çalıştır
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, save())
                    future.result(timeout=2.0)  # Bekle - FK için kritik!
                logger.debug(f"Episode saved (thread): {episode.episode_id}")
            except RuntimeError:
                # No running loop - direkt çalıştır
                asyncio.run(save())
                logger.debug(f"Episode saved (sync): {episode.episode_id}")
        except concurrent.futures.TimeoutError:
            logger.warning(f"Episode save timeout: {episode.episode_id}")
        except Exception as e:
            logger.warning(f"Failed to save episode: {e}")
    
    def start_episode_sync(
        self,
        start_cycle_id: int,
        semantic_tag: str = "auto_window",
        boundary_reason: str = BoundaryReason.TIME_WINDOW.value,
    ) -> Episode:
        """
        Sync version of start_episode.
        
        🔧 FIX v2: Storage'a bekleyerek yazar (FK hatası düzeltmesi)
        """
        if not self._run_id:
            raise RuntimeError("EpisodeManager not initialized")
        
        self._episode_seq += 1
        self._cycles_in_episode = 0
        
        episode = Episode(
            run_id=self._run_id,
            episode_seq=self._episode_seq,
            start_cycle_id=start_cycle_id,
            semantic_tag=semantic_tag,
            boundary_reason=boundary_reason,
        )
        
        self._current_episode = episode
        
        # 🔧 FIX v2: Storage'a HEMEN kaydet (bekleyerek)
        self._save_episode_sync(episode)
        
        if self.on_episode_start:
            try:
                self.on_episode_start(episode)
            except Exception as e:
                logger.error(f"on_episode_start callback failed: {e}")
        
        logger.info(f"Episode started (sync): {episode.episode_id}")
        return episode
    
    def end_current_episode_sync(
        self,
        end_cycle_id: int,
        summary: Optional[Dict[str, Any]] = None,
    ) -> Optional[Episode]:
        """
        Sync version of end_current_episode.
        
        🔧 FIX v2: Storage'a bekleyerek yazar
        """
        if not self._current_episode:
            return None
        
        episode = self._current_episode
        episode.close(end_cycle_id, summary or {})
        
        # 🔧 FIX v2: Storage'a HEMEN kaydet (bekleyerek)
        self._save_episode_sync(episode)
        
        if self.on_episode_end:
            try:
                self.on_episode_end(episode)
            except Exception as e:
                logger.error(f"on_episode_end callback failed: {e}")
        
        logger.info(f"Episode ended (sync): {episode.episode_id}")
        self._current_episode = None
        return episode


# ============================================================
# FACTORY
# ============================================================

def create_episode_manager(
    config: Optional[Dict[str, Any]] = None,
    storage=None,
) -> EpisodeManager:
    """Factory function."""
    if config:
        episode_config = EpisodeConfig.from_dict(config)
    else:
        episode_config = EpisodeConfig()
    return EpisodeManager(episode_config, storage)


__all__ = ['EpisodeManager', 'EpisodeConfig', 'create_episode_manager']
