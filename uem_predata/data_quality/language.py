"""Language detection for input/output."""
from typing import Optional, Tuple
import re


class LanguageDetector:
    """
    Detects language of text input.
    
    Uses heuristic-based detection (no external dependencies).
    For production, consider using langdetect or similar.
    """
    
    # Common words by language
    LANGUAGE_MARKERS = {
        "en": ["the", "is", "are", "was", "were", "have", "has", "been", "will", "would", "could", "should", "this", "that", "with", "from", "they", "what", "which"],
        "tr": ["bir", "ve", "bu", "için", "ile", "olan", "olarak", "gibi", "daha", "çok", "var", "ne", "kadar", "ama", "ancak", "veya", "hem", "değil", "şey", "nasıl"],
        "de": ["der", "die", "das", "und", "ist", "sind", "war", "haben", "wird", "nicht", "ein", "eine", "mit", "von", "auf", "für", "auch", "nach", "noch"],
        "fr": ["le", "la", "les", "est", "sont", "être", "avoir", "pour", "dans", "que", "qui", "une", "avec", "sur", "pas", "plus", "tout", "fait", "cette"],
        "es": ["el", "la", "los", "las", "es", "son", "estar", "para", "con", "que", "una", "por", "más", "como", "pero", "muy", "todo", "esta", "tiene"],
    }
    
    # Character patterns
    SCRIPT_PATTERNS = {
        "ar": re.compile(r'[\u0600-\u06FF]'),  # Arabic
        "zh": re.compile(r'[\u4e00-\u9fff]'),  # Chinese
        "ja": re.compile(r'[\u3040-\u30ff]'),  # Japanese
        "ko": re.compile(r'[\uac00-\ud7af]'),  # Korean
        "ru": re.compile(r'[\u0400-\u04FF]'),  # Cyrillic
        "el": re.compile(r'[\u0370-\u03FF]'),  # Greek
    }
    
    def detect(self, text: str) -> Tuple[str, float]:
        """
        Detect language of text.
        Returns (language_code, confidence).
        """
        if not text or len(text.strip()) < 3:
            return ("unknown", 0.0)
        
        text_lower = text.lower()
        
        # Check script-based languages first
        for lang, pattern in self.SCRIPT_PATTERNS.items():
            matches = len(pattern.findall(text))
            if matches > len(text) * 0.1:
                return (lang, min(0.5 + matches / len(text), 0.95))
        
        # Word-based detection
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        scores = {}
        for lang, markers in self.LANGUAGE_MARKERS.items():
            matches = len(words.intersection(markers))
            scores[lang] = matches
        
        if not scores or max(scores.values()) == 0:
            return ("unknown", 0.0)
        
        best_lang = max(scores, key=scores.get)
        confidence = min(scores[best_lang] / 5, 0.95)  # Cap at 0.95
        
        return (best_lang, round(confidence, 2))
    
    def detect_input(self, input_data) -> Optional[str]:
        """Detect language from various input types."""
        if isinstance(input_data, str):
            lang, conf = self.detect(input_data)
            return lang if conf > 0.3 else None
        
        if isinstance(input_data, dict):
            # Try common text fields
            for key in ["text", "content", "message", "input"]:
                if key in input_data and isinstance(input_data[key], str):
                    lang, conf = self.detect(input_data[key])
                    if conf > 0.3:
                        return lang
        
        return None
    
    def detect_output(self, output_data) -> Optional[str]:
        """Detect language from output."""
        return self.detect_input(output_data)
