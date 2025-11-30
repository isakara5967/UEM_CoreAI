"""Input noise level estimation."""
from typing import Any, Optional
import re


class NoiseEstimator:
    """
    Estimates noise level in input data.
    
    Noise indicators:
    - Typos, special characters
    - Inconsistent formatting
    - Missing/corrupted data
    - Repetition
    """
    
    def __init__(self):
        self._special_char_pattern = re.compile(r'[^\w\s\.,!?\-\'"()]')
        self._repetition_pattern = re.compile(r'(.)\1{3,}')
        self._url_pattern = re.compile(r'https?://\S+')
    
    def estimate(self, input_data: Any) -> float:
        """
        Estimate noise level (0.0 = clean, 1.0 = very noisy).
        """
        if input_data is None:
            return 0.5  # Unknown
        
        if isinstance(input_data, str):
            return self._estimate_text_noise(input_data)
        
        if isinstance(input_data, dict):
            return self._estimate_dict_noise(input_data)
        
        if isinstance(input_data, list):
            if not input_data:
                return 0.0
            noises = [self.estimate(item) for item in input_data[:10]]
            return sum(noises) / len(noises)
        
        return 0.0
    
    def _estimate_text_noise(self, text: str) -> float:
        """Estimate noise in text."""
        if not text:
            return 0.0
        
        noise_score = 0.0
        
        # Special characters ratio
        special_chars = len(self._special_char_pattern.findall(text))
        special_ratio = special_chars / max(len(text), 1)
        noise_score += min(special_ratio * 2, 0.3)
        
        # Repetition
        repetitions = len(self._repetition_pattern.findall(text))
        if repetitions > 0:
            noise_score += min(repetitions * 0.1, 0.2)
        
        # Very short or very long
        if len(text) < 3:
            noise_score += 0.2
        elif len(text) > 10000:
            noise_score += 0.1
        
        # All caps
        if text.isupper() and len(text) > 10:
            noise_score += 0.1
        
        # URL density (not necessarily noise, but complexity)
        urls = len(self._url_pattern.findall(text))
        if urls > 5:
            noise_score += 0.1
        
        return min(noise_score, 1.0)
    
    def _estimate_dict_noise(self, data: dict) -> float:
        """Estimate noise in dict."""
        if not data:
            return 0.0
        
        noise_score = 0.0
        
        # Empty values
        empty_count = sum(1 for v in data.values() if v is None or v == "")
        empty_ratio = empty_count / max(len(data), 1)
        noise_score += empty_ratio * 0.3
        
        # Check text values
        text_noises = []
        for v in data.values():
            if isinstance(v, str):
                text_noises.append(self._estimate_text_noise(v))
        
        if text_noises:
            noise_score += sum(text_noises) / len(text_noises) * 0.5
        
        return min(noise_score, 1.0)
