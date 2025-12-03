"""
MetaMind v1.9 - Insights Module

Human-readable insight ve rapor üretimi:
- InsightGenerator: Cycle, episode, run seviyesinde raporlar
- MetaInsight: Yapılandırılmış insight formatı
"""

from .insight_generator import InsightGenerator, create_insight_generator

__all__ = [
    'InsightGenerator',
    'create_insight_generator',
]
