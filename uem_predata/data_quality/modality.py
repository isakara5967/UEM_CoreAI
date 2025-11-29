"""Input modality detection - text, image, audio, etc."""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ModalityMix:
    """Detected modality distribution."""
    text: float = 0.0
    image: float = 0.0
    audio: float = 0.0
    video: float = 0.0
    structured: float = 0.0  # JSON, tables, etc.
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "text": self.text,
            "image": self.image,
            "audio": self.audio,
            "video": self.video,
            "structured": self.structured,
        }
    
    @property
    def dominant(self) -> str:
        """Get dominant modality."""
        items = self.to_dict()
        return max(items, key=items.get)


class ModalityDetector:
    """
    Detects input modality mix.
    
    Usage:
        detector = ModalityDetector()
        mix = detector.detect(input_data)
    """
    
    def detect(self, input_data: Any) -> ModalityMix:
        """Detect modalities in input data."""
        mix = ModalityMix()
        
        if input_data is None:
            return mix
        
        # String input
        if isinstance(input_data, str):
            mix.text = 1.0
            return mix
        
        # Dict input - check for different types
        if isinstance(input_data, dict):
            return self._detect_dict(input_data)
        
        # List input
        if isinstance(input_data, list):
            return self._detect_list(input_data)
        
        # Bytes - likely binary (image/audio)
        if isinstance(input_data, bytes):
            mix.image = 0.7  # Assume image by default
            mix.audio = 0.3
            return mix
        
        return mix
    
    def _detect_dict(self, data: Dict) -> ModalityMix:
        """Detect modalities in dict input."""
        mix = ModalityMix()
        
        # Check for explicit type hints
        if "type" in data:
            type_val = data["type"].lower()
            if "image" in type_val:
                mix.image = 1.0
            elif "audio" in type_val:
                mix.audio = 1.0
            elif "video" in type_val:
                mix.video = 1.0
            else:
                mix.text = 0.5
                mix.structured = 0.5
            return mix
        
        # Check for common keys
        if "text" in data or "message" in data or "content" in data:
            mix.text = 0.8
        if "image" in data or "image_url" in data or "pixels" in data:
            mix.image = 0.8
        if "audio" in data or "waveform" in data:
            mix.audio = 0.8
        
        # Default: structured data
        if sum([mix.text, mix.image, mix.audio]) == 0:
            mix.structured = 1.0
        
        # Normalize
        total = mix.text + mix.image + mix.audio + mix.video + mix.structured
        if total > 0:
            mix.text /= total
            mix.image /= total
            mix.audio /= total
            mix.video /= total
            mix.structured /= total
        
        return mix
    
    def _detect_list(self, data: List) -> ModalityMix:
        """Detect modalities in list input."""
        if not data:
            return ModalityMix()
        
        # Check first item
        first = data[0]
        if isinstance(first, str):
            return ModalityMix(text=1.0)
        elif isinstance(first, dict):
            return self._detect_dict(first)
        
        return ModalityMix(structured=1.0)
