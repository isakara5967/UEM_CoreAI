#!/usr/bin/env python3
"""
MetaMind v1.9 Phase 3 - Analyzer Entegrasyonu
=============================================

Bu patch core.py'ye MicroCycleAnalyzer ve PatternMiner entegre eder:
1. __init__ içinde analyzer ve miner oluştur
2. initialize() içinde context set et
3. on_cycle_end() içinde veri ekle ve analiz çağır
4. _run_pattern_mining() implementasyonu
5. Anomaly event'leri DB'ye yaz

Kullanım:
    python3 phase3_core_patch.py
"""

import os
import re

CORE_PY_PATH = os.path.expanduser("~/UEM_CoreAI/core/metamind/core.py")

# ============================================================
# PATCH 1: Import'lar
# ============================================================

OLD_IMPORTS = '''from .storage import MetaMindStorage'''

NEW_IMPORTS = '''from .storage import MetaMindStorage
from .analyzers import MicroCycleAnalyzer, PatternMiner, create_cycle_analyzer, create_pattern_miner'''

# ============================================================
# PATCH 2: __init__ içinde analyzer ve miner oluştur
# ============================================================

OLD_INIT_END = '''        # Performance tracking
        self._last_cycle_time_ms: float = 0.0
        self._total_online_time_ms: float = 0.0
        
        logger.info(f"MetaMindCore v{self.config.version} created")'''

NEW_INIT_END = '''        # Performance tracking
        self._last_cycle_time_ms: float = 0.0
        self._total_online_time_ms: float = 0.0
        
        # === Phase 3: Analyzers ===
        self.cycle_analyzer = MicroCycleAnalyzer(
            on_event=self._handle_analyzer_event,
        )
        self.pattern_miner = PatternMiner(storage=storage)
        
        logger.info(f"MetaMindCore v{self.config.version} created (with analyzers)")'''

# ============================================================
# PATCH 3: initialize() içinde analyzer/miner context set
# ============================================================

OLD_INIT_END_2 = '''        self._initialized = True
        logger.info(f"MetaMindCore initialized for run: {run_id}")'''

NEW_INIT_END_2 = '''        # === Phase 3: Analyzer context ===
        self.cycle_analyzer.set_context(run_id)
        self.pattern_miner.initialize(run_id)
        
        self._initialized = True
        logger.info(f"MetaMindCore initialized for run: {run_id}")'''

# ============================================================
# PATCH 4: on_cycle_end içinde PatternMiner'a veri ekle
# ============================================================

OLD_META_STATE_UPDATE = '''    def _run_meta_state_update(self, cycle_data: Dict[str, Any], cycle_id: int) -> None:
        """MetaState hesapla ve güncelle.\""""

NEW_META_STATE_UPDATE = '''    def _run_meta_state_update(self, cycle_data: Dict[str, Any], cycle_id: int) -> None:
        """MetaState hesapla ve güncelle."""
        # === Phase 3: PatternMiner'a cycle data ekle ===
        action = cycle_data.get('action', 'unknown')
        valence = cycle_data.get('valence', 0.0)
        arousal = cycle_data.get('arousal', 0.5)
        self.pattern_miner.add_cycle_data(action, valence, arousal, cycle_data)
        '''

# ============================================================
# PATCH 5: _run_anomaly_check'i MicroCycleAnalyzer ile değiştir
# ============================================================

OLD_ANOMALY_CHECK = '''    def _run_anomaly_check(self, cycle_data: Dict[str, Any], cycle_id: int) -> None:
        """Anomali kontrolü (basit threshold check)."""
        if not self._current_meta_state:
            return
        
        # Threshold checks
        thresholds = self.config.meta_state.__dict__ if hasattr(self.config.meta_state, '__dict__') else {}
        
        # Global health critical
        if self._current_meta_state.global_cognitive_health.value < 0.3:
            self._emit_event(
                event_type=EventType.THRESHOLD_BREACH,
                severity=Severity.WARNING,
                message=f"Global health critical: {self._current_meta_state.global_cognitive_health.value:.2f}",
                cycle_id=cycle_id,
            )
        
        # Failure pressure high
        if self._current_meta_state.failure_pressure.value > 0.8:
            self._emit_event(
                event_type=EventType.THRESHOLD_BREACH,
                severity=Severity.WARNING,
                message=f"High failure pressure: {self._current_meta_state.failure_pressure.value:.2f}",
                cycle_id=cycle_id,
            )'''

NEW_ANOMALY_CHECK = '''    def _run_anomaly_check(self, cycle_data: Dict[str, Any], cycle_id: int) -> None:
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
            logger.debug(f"Cycle {cycle_id}: {len(anomalies)} anomalies detected")'''

# ============================================================
# PATCH 6: _run_pattern_mining implementasyonu
# ============================================================

OLD_PATTERN_MINING = '''    async def _run_pattern_mining(self, cycle_data: Dict[str, Any], cycle_id: int) -> None:
        """Pattern mining (Phase 3'te implement edilecek)."""
        # Placeholder - Phase 3'te PatternMiner entegre edilecek
        pass'''

NEW_PATTERN_MINING = '''    async def _run_pattern_mining(self, cycle_data: Dict[str, Any], cycle_id: int) -> None:
        """Pattern mining - PatternMiner.mine() çağırır."""
        try:
            # Episode context güncelle
            episode_id = self.episode_manager.get_current_episode_id()
            self.pattern_miner.set_episode(episode_id)
            
            # Mining yap
            patterns = self.pattern_miner.mine()
            
            if patterns:
                logger.debug(f"Cycle {cycle_id}: {len(patterns)} patterns found")
                
                # Pattern detected event'leri emit et
                for pattern in patterns[:3]:  # Top 3 pattern için event
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
            logger.error(f"Pattern mining failed: {e}")'''

# ============================================================
# PATCH 7: Analyzer event callback
# ============================================================

OLD_EMIT_EVENT_END = '''        # Log
        if severity == Severity.CRITICAL:
            logger.error(f"[MetaEvent] {message}")
        elif severity == Severity.WARNING:
            logger.warning(f"[MetaEvent] {message}")
        else:
            logger.debug(f"[MetaEvent] {message}")'''

NEW_EMIT_EVENT_END = '''        # Log
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
            import asyncio
            try:
                asyncio.create_task(self.storage.save_meta_event(event))
            except RuntimeError:
                # No running loop
                pass
        
        # Log
        if event.severity == Severity.CRITICAL.value:
            logger.error(f"[Analyzer] {event.message}")
        elif event.severity == Severity.WARNING.value:
            logger.warning(f"[Analyzer] {event.message}")'''


def apply_patches():
    """Tüm patch'leri uygula."""
    if not os.path.exists(CORE_PY_PATH):
        print(f"❌ Dosya bulunamadı: {CORE_PY_PATH}")
        return False
    
    # Backup
    backup_path = CORE_PY_PATH + ".bak_phase3"
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy(CORE_PY_PATH, backup_path)
        print(f"✓ Backup: {backup_path}")
    
    # Read
    with open(CORE_PY_PATH, 'r') as f:
        content = f.read()
    
    original = content
    patches_applied = 0
    
    # Patch 1: Imports
    if OLD_IMPORTS in content and 'from .analyzers import' not in content:
        content = content.replace(OLD_IMPORTS, NEW_IMPORTS)
        patches_applied += 1
        print("✓ Patch 1: Imports eklendi")
    else:
        print("⚠ Patch 1: Zaten var veya pattern bulunamadı")
    
    # Patch 2: __init__ analyzer/miner
    if OLD_INIT_END in content and 'self.cycle_analyzer' not in content:
        content = content.replace(OLD_INIT_END, NEW_INIT_END)
        patches_applied += 1
        print("✓ Patch 2: __init__ analyzer/miner eklendi")
    else:
        print("⚠ Patch 2: Zaten var veya pattern bulunamadı")
    
    # Patch 3: initialize context
    if OLD_INIT_END_2 in content and 'cycle_analyzer.set_context' not in content:
        content = content.replace(OLD_INIT_END_2, NEW_INIT_END_2)
        patches_applied += 1
        print("✓ Patch 3: initialize context eklendi")
    else:
        print("⚠ Patch 3: Zaten var veya pattern bulunamadı")
    
    # Patch 4: _run_meta_state_update - PatternMiner data
    if 'pattern_miner.add_cycle_data' not in content:
        if OLD_META_STATE_UPDATE in content:
            content = content.replace(OLD_META_STATE_UPDATE, NEW_META_STATE_UPDATE)
            patches_applied += 1
            print("✓ Patch 4: PatternMiner data eklendi")
        else:
            print("⚠ Patch 4: Pattern bulunamadı")
    else:
        print("⚠ Patch 4: Zaten var")
    
    # Patch 5: _run_anomaly_check
    if 'cycle_analyzer.analyze' not in content:
        if OLD_ANOMALY_CHECK in content:
            content = content.replace(OLD_ANOMALY_CHECK, NEW_ANOMALY_CHECK)
            patches_applied += 1
            print("✓ Patch 5: MicroCycleAnalyzer entegre edildi")
        else:
            print("⚠ Patch 5: Pattern bulunamadı")
    else:
        print("⚠ Patch 5: Zaten var")
    
    # Patch 6: _run_pattern_mining
    if 'pattern_miner.mine()' not in content:
        if OLD_PATTERN_MINING in content:
            content = content.replace(OLD_PATTERN_MINING, NEW_PATTERN_MINING)
            patches_applied += 1
            print("✓ Patch 6: PatternMiner.mine() entegre edildi")
        else:
            print("⚠ Patch 6: Pattern bulunamadı")
    else:
        print("⚠ Patch 6: Zaten var")
    
    # Patch 7: _handle_analyzer_event
    if '_handle_analyzer_event' not in content:
        if OLD_EMIT_EVENT_END in content:
            content = content.replace(OLD_EMIT_EVENT_END, NEW_EMIT_EVENT_END)
            patches_applied += 1
            print("✓ Patch 7: _handle_analyzer_event eklendi")
        else:
            print("⚠ Patch 7: Pattern bulunamadı")
    else:
        print("⚠ Patch 7: Zaten var")
    
    # Write
    if content != original:
        with open(CORE_PY_PATH, 'w') as f:
            f.write(content)
        print(f"\n✅ {patches_applied} patch uygulandı")
        return True
    else:
        print("\n⚠ Hiçbir patch uygulanmadı")
        return False


def verify_syntax():
    """Syntax kontrolü."""
    import subprocess
    result = subprocess.run(
        ['python3', '-m', 'py_compile', CORE_PY_PATH],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ Syntax OK")
        return True
    else:
        print(f"❌ Syntax Error: {result.stderr}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("MetaMind v1.9 Phase 3 - Analyzer Entegrasyonu")
    print("=" * 60)
    
    if apply_patches():
        verify_syntax()
    
    print("\nTest için:")
    print("  pytest tests/ -q --tb=no 2>&1 | tail -3")
