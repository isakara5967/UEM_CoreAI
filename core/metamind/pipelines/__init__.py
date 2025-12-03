"""
MetaMind v1.9 - Pipelines Module

Pipeline modülleri:
- SocialHealthPipeline: Social meta-analiz (⚠️ STUB - v2.0 için hazır)

⚠️ ALICE UYARISI:
SocialHealth interface'i korunmalı - STUB dışında başka yerden
social meta-analiz YAZILMAYACAK!
"""

from .social import SocialHealthPipeline, SocialHealthMetrics, create_social_pipeline

__all__ = [
    'SocialHealthPipeline',
    'SocialHealthMetrics',
    'create_social_pipeline',
]
