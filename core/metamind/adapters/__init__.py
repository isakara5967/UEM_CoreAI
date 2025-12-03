"""
MetaMind v1.9 - Adapters Module

Mevcut scorer'ları wrap eden adapter'lar.
Mevcut metrics/ klasörü DEĞİŞMEZ.
"""

from .metrics_adapter import MetricsAdapter, create_metrics_adapter

__all__ = ['MetricsAdapter', 'create_metrics_adapter']
