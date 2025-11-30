# core/predata/calculators.py
"""
PreData Placeholder Alanları Hesaplama Modülü

Bu modül, daha önce sabit değerlerle bırakılan 4 placeholder alanı
gerçek hesaplamalarla doldurmak için tasarlanmıştır.

Alanlar:
- empathy_score: Empati seviyesi (0-1)
- ma_agent_count: Algılanan ajan sayısı
- ma_coordination_mode: Koordinasyon modu
- ma_conflict_score: Çatışma skoru (0-1)

Konsensüs: Claude (Opus 4.5) + Alice (GPT-5.1 Thinking)
Tarih: 30 Kasım 2025
Versiyon: 1.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# CONFIGURATION (Config'den okunabilir yapı için hazırlık)
# ============================================================================

# Empathy score ağırlıkları
EMPATHY_WEIGHT = 0.5
RESONANCE_WEIGHT = 0.3
CONFIDENCE_WEIGHT = 0.2

# Conflict score ağırlıkları
RELATIONSHIP_CONFLICT_WEIGHT = 0.6
GOAL_CONFLICT_WEIGHT = 0.4

# Coordination mode eşikleri
COOPERATIVE_THRESHOLD = 0.3
COMPETITIVE_THRESHOLD = -0.3
RESONANCE_COOPERATIVE_THRESHOLD = 0.7
RESONANCE_COMPETITIVE_THRESHOLD = 0.3

# Coordination mode seti
COORDINATION_MODES = {
    "single",       # Tek ajan (başka kimse yok)
    "cooperative",  # İşbirliği
    "competitive",  # Rekabet
    "neutral",      # Nötr (eski: independent)
    "mixed",        # Karışık (çoklu ajanda farklı modlar)
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class EmpathyData:
    """Empati hesaplaması için gerekli veriler."""
    empathy_level: float = 0.0
    resonance: float = 0.0
    confidence: float = 0.0
    relationship: float = 0.0  # -1 to +1
    other_entity_id: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Veri geçerli mi kontrol et."""
        return self.other_entity_id is not None


@dataclass
class MultiAgentResult:
    """Çoklu ajan hesaplama sonucu."""
    empathy_score: float
    conflict_score: float
    agent_count: int
    coordination_mode: str
    individual_scores: List[Dict[str, Any]]


# ============================================================================
# EMPATHY SCORE HESAPLAMA
# ============================================================================

def calculate_empathy_score(
    empathy_level: float,
    resonance: float,
    confidence: float,
    has_other_entity: bool = True
) -> float:
    """
    Empati skorunu hesapla.
    
    Formül (Seçenek B - Ağırlıklı Lineer):
        score = 0.5 × empathy_level + 0.3 × resonance + 0.2 × confidence
    
    Args:
        empathy_level: Empati seviyesi (0-1)
        resonance: Duygusal rezonans (0-1)
        confidence: Hesaplama güvenilirliği (0-1)
        has_other_entity: Başka bir varlık var mı?
    
    Returns:
        Empati skoru (0-1), ajan yoksa 0.0
    
    Konsensüs:
        - Claude + Alice: Seçenek B onaylandı
        - Ajan yoksa 0.0 döndür
        - Clamp [0, 1] aralığına
    """
    # Başka varlık yoksa empati yok
    if not has_other_entity:
        return 0.0
    
    # Ağırlıklı lineer kombinasyon
    raw_empathy = (
        EMPATHY_WEIGHT * empathy_level +
        RESONANCE_WEIGHT * resonance +
        CONFIDENCE_WEIGHT * confidence
    )
    
    # Clamp [0, 1] - Defensive fix (Alice önerisi)
    empathy_score = max(0.0, min(1.0, raw_empathy))
    
    return round(empathy_score, 4)


def calculate_empathy_score_from_result(
    empathy_result: Optional[Any]
) -> float:
    """
    EmpathyResult objesinden empati skoru hesapla.
    
    Args:
        empathy_result: EmpathyOrchestrator'dan dönen sonuç
    
    Returns:
        Empati skoru (0-1)
    """
    if empathy_result is None:
        return 0.0
    
    return calculate_empathy_score(
        empathy_level=getattr(empathy_result, 'empathy_level', 0.0),
        resonance=getattr(empathy_result, 'resonance', 0.0),
        confidence=getattr(empathy_result, 'confidence', 0.0),
        has_other_entity=True
    )


# ============================================================================
# CONFLICT SCORE HESAPLAMA
# ============================================================================

def estimate_goal_overlap(
    my_action: Optional[str] = None,
    other_action: Optional[str] = None,
    shared_target: Optional[str] = None
) -> float:
    """
    Hedef çakışmasını tahmin et.
    
    V1.1 Heuristic (Claude + Alice Konsensüs - 30 Kasım 2025):
    - Aynı aksiyon → 0.5
    - Paylaşılan hedef → 0.7
    - İkisi birden → max(0.5, 0.7) = 0.7
    - Aksi halde → 0.0
    
    V2.0: Planner entegrasyonu ile gerçek hesaplama (Şubat 2026)
    
    Args:
        my_action: Benim aksiyonum (ör: "eat", "attack", "flee")
        other_action: Diğer ajanın aksiyonu
        shared_target: Paylaşılan hedef (ör: "food", "enemy", "exit")
    
    Returns:
        Hedef çakışma oranı (0-1)
    """
    overlap = 0.0
    
    # Aynı aksiyon → 0.5
    if my_action and other_action and my_action.lower() == other_action.lower():
        overlap = 0.5
    
    # Paylaşılan hedef → 0.7 (daha yüksek öncelik)
    if shared_target:
        overlap = max(overlap, 0.7)
    
    return overlap


def calculate_conflict_score(
    resonance: float,
    relationship: float,
    goal_overlap: float = 0.0
) -> float:
    """
    Çatışma skorunu hesapla.
    
    Formül (İki Bileşenli - Claude + Alice Konsensüs):
        relationship_conflict = (1 - resonance) × abs(min(0, relationship))
        goal_conflict = goal_overlap × (1 - 0.5 × resonance)
        conflict = 0.6 × relationship_conflict + 0.4 × goal_conflict
    
    Args:
        resonance: Duygusal rezonans (0-1)
        relationship: İlişki değeri (-1 to +1)
        goal_overlap: Hedef çakışması (0-1), şimdilik 0.0
    
    Returns:
        Çatışma skoru (0-1)
    
    Konsensüs:
        - Pozitif ilişkiler çatışmayı ARTIRMAZ (Claude haklı)
        - Goal conflict ayrı bileşen olarak hesaplanır
        - Clamp [0, 1] aralığına (Alice önerisi)
    """
    # Bileşen 1: İlişki bazlı çatışma (sadece negatif ilişkiler)
    # relationship = -0.8 → abs(min(0, -0.8)) = 0.8
    # relationship = +0.8 → abs(min(0, +0.8)) = 0.0
    relationship_conflict = (1 - resonance) * abs(min(0.0, relationship))
    
    # Bileşen 2: Hedef bazlı çatışma
    # Yüksek resonance → empati → çatışma azalır
    goal_conflict = goal_overlap * (1 - 0.5 * resonance)
    
    # Toplam çatışma
    raw_conflict = (
        RELATIONSHIP_CONFLICT_WEIGHT * relationship_conflict +
        GOAL_CONFLICT_WEIGHT * goal_conflict
    )
    
    # Clamp [0, 1] - Defensive fix (Alice önerisi)
    conflict_score = max(0.0, min(1.0, raw_conflict))
    
    return round(conflict_score, 4)


def calculate_conflict_score_from_result(
    empathy_result: Optional[Any],
    goal_overlap: float = 0.0
) -> float:
    """
    EmpathyResult objesinden çatışma skoru hesapla.
    
    Args:
        empathy_result: EmpathyOrchestrator'dan dönen sonuç
        goal_overlap: Hedef çakışması (0-1)
    
    Returns:
        Çatışma skoru (0-1)
    """
    if empathy_result is None:
        return 0.0
    
    resonance = getattr(empathy_result, 'resonance', 0.0)
    
    # other_entity'den relationship al
    other_entity = getattr(empathy_result, 'other_entity', None)
    relationship = getattr(other_entity, 'relationship', 0.0) if other_entity else 0.0
    
    return calculate_conflict_score(
        resonance=resonance,
        relationship=relationship,
        goal_overlap=goal_overlap
    )


# ============================================================================
# AGENT COUNT HESAPLAMA
# ============================================================================

def calculate_agent_count(
    other_entities: Optional[List[Any]] = None
) -> int:
    """
    Toplam ajan sayısını hesapla.
    
    Formül:
        count = len(other_entities) + 1  # +1 for self
    
    Args:
        other_entities: Algılanan diğer varlıklar listesi
    
    Returns:
        Toplam ajan sayısı (minimum 1 = self)
    """
    if not other_entities:
        return 1  # Sadece self
    
    return len(other_entities) + 1


# ============================================================================
# COORDINATION MODE HESAPLAMA
# ============================================================================

def calculate_coordination_mode_single(
    resonance: float,
    relationship: float
) -> str:
    """
    Tek bir ajan için koordinasyon modu hesapla.
    
    Karar Ağacı:
        1. relationship > 0.3 → cooperative
        2. relationship < -0.3 → competitive
        3. resonance > 0.7 → cooperative (duygusal uyum)
        4. resonance < 0.3 → competitive (duygusal çatışma)
        5. Aksi halde → neutral
    
    Args:
        resonance: Duygusal rezonans (0-1)
        relationship: İlişki değeri (-1 to +1)
    
    Returns:
        Koordinasyon modu: cooperative / competitive / neutral
    """
    # İlişki bazlı karar (öncelikli)
    if relationship > COOPERATIVE_THRESHOLD:
        return "cooperative"
    elif relationship < COMPETITIVE_THRESHOLD:
        return "competitive"
    
    # Resonance bazlı karar (ilişki nötr ise)
    if resonance > RESONANCE_COOPERATIVE_THRESHOLD:
        return "cooperative"
    elif resonance < RESONANCE_COMPETITIVE_THRESHOLD:
        return "competitive"
    
    return "neutral"


def calculate_coordination_mode(
    other_entities: Optional[List[Any]] = None,
    empathy_results: Optional[List[Any]] = None
) -> str:
    """
    Koordinasyon modunu hesapla.
    
    Mode Seti (Alice önerisi):
        - single: Tek ajan (başka kimse yok)
        - cooperative: İşbirliği
        - competitive: Rekabet
        - neutral: Nötr
        - mixed: Karışık (çoklu ajanda farklı modlar)
    
    Args:
        other_entities: Diğer varlıklar listesi
        empathy_results: Her varlık için empati sonuçları
    
    Returns:
        Koordinasyon modu string
    """
    # Başka varlık yoksa → single
    if not other_entities:
        return "single"
    
    # Empati sonuçları yoksa → neutral (fallback)
    if not empathy_results:
        return "neutral"
    
    # Her ajan için mod hesapla
    modes = []
    for result in empathy_results:
        if result is None:
            continue
        
        resonance = getattr(result, 'resonance', 0.5)
        other_entity = getattr(result, 'other_entity', None)
        relationship = getattr(other_entity, 'relationship', 0.0) if other_entity else 0.0
        
        mode = calculate_coordination_mode_single(resonance, relationship)
        modes.append(mode)
    
    if not modes:
        return "neutral"
    
    # Tek bir mod varsa → o modu döndür
    unique_modes = set(modes)
    if len(unique_modes) == 1:
        return modes[0]
    
    # Farklı modlar varsa → mixed
    return "mixed"


# ============================================================================
# MULTI-AGENT AGGREGATION
# ============================================================================

def aggregate_empathy_scores(
    empathy_results: List[Any]
) -> float:
    """
    Çoklu ajan empati skorlarını birleştir.
    
    Formül (Ağırlıklı Ortalama):
        weight_i = |relationship_i| × confidence_i
        aggregated = sum(empathy_i × weight_i) / sum(weight_i)
    
    Args:
        empathy_results: EmpathyResult listesi
    
    Returns:
        Birleştirilmiş empati skoru (0-1)
    
    Konsensüs:
        - Alice: Ağırlıklı ortalama, ağırlık = |rel| × conf
    """
    if not empathy_results:
        return 0.0
    
    total_weight = 0.0
    weighted_sum = 0.0
    
    for result in empathy_results:
        if result is None:
            continue
        
        # Değerleri al
        empathy_level = getattr(result, 'empathy_level', 0.0)
        resonance = getattr(result, 'resonance', 0.0)
        confidence = getattr(result, 'confidence', 0.0)
        
        other_entity = getattr(result, 'other_entity', None)
        relationship = getattr(other_entity, 'relationship', 0.0) if other_entity else 0.0
        
        # Bireysel empati skoru
        individual_score = calculate_empathy_score(
            empathy_level=empathy_level,
            resonance=resonance,
            confidence=confidence,
            has_other_entity=True
        )
        
        # Ağırlık: |relationship| × confidence
        weight = abs(relationship) * confidence
        
        # Ağırlık 0 ise minimum ağırlık ver (sıfır bölme önleme)
        if weight == 0:
            weight = 0.1  # Minimum ağırlık
        
        weighted_sum += individual_score * weight
        total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    aggregated = weighted_sum / total_weight
    return round(max(0.0, min(1.0, aggregated)), 4)


def aggregate_conflict_scores(
    empathy_results: List[Any],
    goal_overlap: float = 0.0
) -> float:
    """
    Çoklu ajan çatışma skorlarını birleştir.
    
    Strateji: Maksimum (en riskli durumu göster)
    
    Args:
        empathy_results: EmpathyResult listesi
        goal_overlap: Hedef çakışması (0-1)
    
    Returns:
        Birleştirilmiş çatışma skoru (0-1)
    
    Konsensüs:
        - Claude + Alice: max(conflict_score_i)
    """
    if not empathy_results:
        return 0.0
    
    conflict_scores = []
    
    for result in empathy_results:
        score = calculate_conflict_score_from_result(result, goal_overlap)
        conflict_scores.append(score)
    
    if not conflict_scores:
        return 0.0
    
    return max(conflict_scores)


def aggregate_coordination_modes(
    modes: List[str]
) -> str:
    """
    Çoklu ajan koordinasyon modlarını birleştir.
    
    Strateji:
        - Hepsi aynı → o mod
        - Farklı → mixed
    
    Args:
        modes: Koordinasyon modları listesi
    
    Returns:
        Birleştirilmiş mod string
    """
    if not modes:
        return "single"
    
    unique_modes = set(modes)
    
    if len(unique_modes) == 1:
        return modes[0]
    
    return "mixed"


# ============================================================================
# UNIFIED CALCULATION (Tek Çağrı ile Tüm Alanları Hesapla)
# ============================================================================

def calculate_all_multiagent_fields(
    other_entities: Optional[List[Any]] = None,
    empathy_results: Optional[List[Any]] = None,
    goal_overlap: float = 0.0
) -> Dict[str, Any]:
    """
    Tüm multi-agent PreData alanlarını tek seferde hesapla.
    
    Args:
        other_entities: Algılanan diğer varlıklar
        empathy_results: Her varlık için empati sonuçları
        goal_overlap: Hedef çakışması (0-1)
    
    Returns:
        Dict with keys:
            - empathy_score: float
            - ma_agent_count: int
            - ma_coordination_mode: str
            - ma_conflict_score: float
    """
    # Agent count
    agent_count = calculate_agent_count(other_entities)
    
    # Başka ajan yoksa
    if not other_entities or agent_count == 1:
        return {
            'empathy_score': 0.0,
            'ma_agent_count': 1,
            'ma_coordination_mode': 'single',
            'ma_conflict_score': 0.0,
        }
    
    # Empati sonuçları yoksa
    if not empathy_results:
        return {
            'empathy_score': 0.0,
            'ma_agent_count': agent_count,
            'ma_coordination_mode': 'neutral',
            'ma_conflict_score': 0.0,
        }
    
    # Tek ajan varsa
    if len(empathy_results) == 1:
        result = empathy_results[0]
        empathy_score = calculate_empathy_score_from_result(result)
        conflict_score = calculate_conflict_score_from_result(result, goal_overlap)
        
        resonance = getattr(result, 'resonance', 0.5)
        other_entity = getattr(result, 'other_entity', None)
        relationship = getattr(other_entity, 'relationship', 0.0) if other_entity else 0.0
        mode = calculate_coordination_mode_single(resonance, relationship)
        
        return {
            'empathy_score': empathy_score,
            'ma_agent_count': agent_count,
            'ma_coordination_mode': mode,
            'ma_conflict_score': conflict_score,
        }
    
    # Çoklu ajan → aggregation
    empathy_score = aggregate_empathy_scores(empathy_results)
    conflict_score = aggregate_conflict_scores(empathy_results, goal_overlap)
    coordination_mode = calculate_coordination_mode(other_entities, empathy_results)
    
    return {
        'empathy_score': empathy_score,
        'ma_agent_count': agent_count,
        'ma_coordination_mode': coordination_mode,
        'ma_conflict_score': conflict_score,
    }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Config
    'EMPATHY_WEIGHT',
    'RESONANCE_WEIGHT', 
    'CONFIDENCE_WEIGHT',
    'RELATIONSHIP_CONFLICT_WEIGHT',
    'GOAL_CONFLICT_WEIGHT',
    'COORDINATION_MODES',
    
    # Data classes
    'EmpathyData',
    'MultiAgentResult',
    
    # Single calculations
    'calculate_empathy_score',
    'calculate_empathy_score_from_result',
    'calculate_conflict_score',
    'calculate_conflict_score_from_result',
    'estimate_goal_overlap',
    'calculate_agent_count',
    'calculate_coordination_mode',
    'calculate_coordination_mode_single',
    
    # Aggregation
    'aggregate_empathy_scores',
    'aggregate_conflict_scores',
    'aggregate_coordination_modes',
    
    # Unified
    'calculate_all_multiagent_fields',
]
