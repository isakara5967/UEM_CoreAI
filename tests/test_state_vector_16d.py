# tests/test_state_vector_16d.py
"""
StateVector 16D Tests

Bu testler, 16D state_vector implementasyonunun
doğru çalıştığını doğrular.

Tarih: 1 Aralık 2025
"""

import pytest
from typing import Tuple


class TestStateVectorModule:
    """core/state_vector.py modül testleri."""
    
    def test_import_module(self):
        """Modül import edilebilmeli."""
        from core.state_vector import (
            SV_RESOURCE, SV_THREAT, SV_WELLBEING,
            SV_HEALTH, SV_ENERGY, SV_VALENCE,
            SV_AROUSAL, SV_DOMINANCE,
            STATE_VECTOR_SIZE,
        )
        
        assert SV_RESOURCE == 0
        assert SV_THREAT == 1
        assert SV_WELLBEING == 2
        assert SV_HEALTH == 3
        assert SV_ENERGY == 4
        assert SV_VALENCE == 5
        assert SV_AROUSAL == 6
        assert SV_DOMINANCE == 7
        assert STATE_VECTOR_SIZE == 16
    
    def test_build_state_vector_16d(self):
        """build_state_vector_16d 16 elemanlı tuple döndürmeli."""
        from core.state_vector import build_state_vector_16d
        from dataclasses import dataclass
        
        @dataclass
        class MockWorld:
            player_health: float = 0.8
            player_energy: float = 0.6
            danger_level: float = 0.3
        
        @dataclass
        class MockEmotion:
            valence: float = 0.5
            arousal: float = 0.7
            dominance: float = 0.2
        
        world = MockWorld()
        emotion = MockEmotion()
        
        sv = build_state_vector_16d(world, emotion)
        
        assert len(sv) == 16
        assert sv[3] == 0.8  # health
        assert sv[4] == 0.6  # energy
        assert sv[5] == 0.5  # valence
        assert sv[6] == 0.7  # arousal
        assert sv[7] == 0.2  # dominance
    
    def test_ensure_vector_16d_padding(self):
        """ensure_vector_16d kısa vektörleri pad etmeli."""
        from core.state_vector import ensure_vector_16d
        
        # 3D → 16D
        short = (0.5, 0.3, 0.7)
        result = ensure_vector_16d(short)
        
        assert len(result) == 16
        assert result[0] == 0.5
        assert result[1] == 0.3
        assert result[2] == 0.7
        assert result[3] == 0.0  # padded
        assert result[15] == 0.0  # padded
    
    def test_ensure_vector_16d_truncation(self):
        """ensure_vector_16d uzun vektörleri kesmeli."""
        from core.state_vector import ensure_vector_16d
        
        long = tuple(range(20))
        result = ensure_vector_16d(long)
        
        assert len(result) == 16
        assert result[0] == 0
        assert result[15] == 15
    
    def test_get_health_from_vector_16d(self):
        """get_health_from_vector 16D'den health almalı."""
        from core.state_vector import get_health_from_vector, SV_HEALTH
        
        sv = (0.7, 0.3, 0.5, 0.2, 0.9, 0.1, 0.4, 0.3) + (0.0,) * 8
        
        health = get_health_from_vector(sv)
        
        assert health == 0.2  # sv[3]
    
    def test_get_health_from_vector_legacy(self):
        """get_health_from_vector 3D'den fallback yapmalı."""
        from core.state_vector import get_health_from_vector
        
        # Legacy 3D format
        sv = (0.7, 0.3, 0.5)
        
        health = get_health_from_vector(sv)
        
        assert health == 0.7  # sv[0] = resource (fallback)
    
    def test_get_health_from_vector_none(self):
        """get_health_from_vector None için default döndürmeli."""
        from core.state_vector import get_health_from_vector
        
        health = get_health_from_vector(None)
        
        assert health == 0.5


class TestOntologyBuildStateVector:
    """core/ontology/types.py build_state_vector testleri."""
    
    def test_returns_16d(self):
        """build_state_vector 16D döndürmeli."""
        from core.ontology.types import build_state_vector
        from dataclasses import dataclass
        
        @dataclass
        class World:
            player_health: float = 0.8
            player_energy: float = 0.6
            danger_level: float = 0.2
        
        @dataclass
        class Emotion:
            valence: float = 0.3
            arousal: float = 0.5
            dominance: float = 0.1
        
        sv = build_state_vector(World(), Emotion())
        
        assert len(sv) == 16
    
    def test_raw_values_correct(self):
        """Raw değerler doğru indexlerde olmalı."""
        from core.ontology.types import build_state_vector
        from dataclasses import dataclass
        
        @dataclass
        class World:
            player_health: float = 0.2  # kritik!
            player_energy: float = 1.0
            danger_level: float = 0.9
        
        @dataclass
        class Emotion:
            valence: float = -0.5
            arousal: float = 0.8
            dominance: float = -0.3
        
        sv = build_state_vector(World(), Emotion())
        
        # Derived
        assert sv[0] == pytest.approx((0.2 + 1.0) / 2)  # resource
        assert sv[1] == pytest.approx(0.9)  # threat
        
        # Raw
        assert sv[3] == 0.2   # health
        assert sv[4] == 1.0   # energy
        assert sv[5] == -0.5  # valence
        assert sv[6] == 0.8   # arousal
        assert sv[7] == -0.3  # dominance


class TestEmotionHealthFix:
    """Emotion modülünün doğru health okuduğunu test et."""
    
    def test_emotion_uses_correct_health(self):
        """Emotion, resource değil gerçek health kullanmalı."""
        from core.unified_core import create_unified_core
        from dataclasses import dataclass, field
        from typing import List, Dict
        
        @dataclass
        class TestWorld:
            tick: int = 1
            danger_level: float = 0.1
            player_health: float = 0.2  # Kritik sağlık!
            player_energy: float = 1.0   # Tam enerji
            agents: List[Dict] = field(default_factory=list)
            objects: List[Dict] = field(default_factory=list)
            events: List[str] = field(default_factory=list)
        
        core = create_unified_core(storage_type='memory')
        world = TestWorld()
        
        core.cycle_sync(world)
        
        # Eski hatalı davranış:
        # resource = (0.2 + 1.0) / 2 = 0.6
        # Emotion 0.6'yı health sanıyordu → pozitif valence
        
        # Yeni doğru davranış:
        # health = 0.2 (raw)
        # Emotion negatif valence üretmeli
        
        assert core.current_emotion['valence'] < 0, \
            f"Kritik sağlık (0.2) pozitif valence üretmemeli! Got: {core.current_emotion['valence']}"


class TestMemoryVector16:
    """Memory modülü 16D vektör testleri."""
    
    def test_ensure_vector16_exists(self):
        """_ensure_vector16 metodu mevcut olmalı."""
        from core.memory.memory_interface import MemoryInterface
        
        mem = MemoryInterface.__new__(MemoryInterface)
        
        assert hasattr(mem, '_ensure_vector16')
    
    def test_backward_compat_ensure_vector8(self):
        """_ensure_vector8 hâlâ çalışmalı (backward compat)."""
        from core.memory.memory_interface import MemoryInterface
        
        mem = MemoryInterface.__new__(MemoryInterface)
        
        # _ensure_vector8 artık _ensure_vector16'yı çağırmalı
        assert hasattr(mem, '_ensure_vector8')


class TestDerivedVsRawConsistency:
    """Derived ve raw değerlerin tutarlılığı."""
    
    def test_resource_formula(self):
        """resource = (health + energy) / 2 olmalı."""
        from core.state_vector import build_state_vector_16d
        from dataclasses import dataclass
        
        @dataclass
        class World:
            player_health: float = 0.4
            player_energy: float = 0.8
            danger_level: float = 0.0
        
        @dataclass
        class Emotion:
            valence: float = 0.0
            arousal: float = 0.0
            dominance: float = 0.0
        
        sv = build_state_vector_16d(World(), Emotion())
        
        expected_resource = (0.4 + 0.8) / 2
        
        assert sv[0] == pytest.approx(expected_resource)
        assert sv[3] == 0.4  # raw health korunmuş
        assert sv[4] == 0.8  # raw energy korunmuş
    
    def test_wellbeing_formula(self):
        """wellbeing = (valence + 1) / 2 olmalı."""
        from core.state_vector import build_state_vector_16d
        from dataclasses import dataclass
        
        @dataclass
        class World:
            player_health: float = 0.5
            player_energy: float = 0.5
            danger_level: float = 0.0
        
        @dataclass
        class Emotion:
            valence: float = -0.6  # negatif
            arousal: float = 0.0
            dominance: float = 0.0
        
        sv = build_state_vector_16d(World(), Emotion())
        
        expected_wellbeing = (-0.6 + 1.0) / 2  # 0.2
        
        assert sv[2] == pytest.approx(expected_wellbeing)
        assert sv[5] == -0.6  # raw valence korunmuş
