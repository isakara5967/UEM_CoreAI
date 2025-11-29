"""Adversarial input detection."""
from typing import Any, Dict, List, Optional, Tuple
import re
from dataclasses import dataclass


@dataclass
class AdversarialSignal:
    """A detected adversarial signal."""
    signal_type: str
    confidence: float
    location: Optional[str] = None
    details: Optional[str] = None


class AdversarialDetector:
    """
    Detects potentially adversarial inputs.
    
    Checks for:
    - Prompt injection attempts
    - Jailbreak patterns
    - Encoded payloads
    - Manipulation attempts
    - Excessive special characters
    
    Usage:
        detector = AdversarialDetector()
        score, signals = detector.analyze(input_text)
    """
    
    # Suspicious patterns
    INJECTION_PATTERNS = [
        (r'ignore\s+(previous|all|above)\s+(instructions?|prompts?)', 'prompt_override', 0.8),
        (r'forget\s+(everything|all|what)', 'memory_manipulation', 0.7),
        (r'you\s+are\s+(now|actually)\s+', 'role_hijack', 0.7),
        (r'pretend\s+(to\s+be|you\'?re)', 'role_hijack', 0.6),
        (r'act\s+as\s+(if|though)', 'role_hijack', 0.5),
        (r'disregard\s+(your|the|all)', 'instruction_override', 0.8),
        (r'new\s+instructions?:', 'instruction_injection', 0.9),
        (r'system\s*:\s*', 'system_prompt_injection', 0.9),
        (r'\[system\]', 'system_prompt_injection', 0.9),
        (r'</?(system|assistant|user)>', 'role_tag_injection', 0.8),
        (r'base64\s*:', 'encoded_payload', 0.6),
        (r'eval\s*\(', 'code_injection', 0.7),
        (r'exec\s*\(', 'code_injection', 0.7),
    ]
    
    # Jailbreak indicators
    JAILBREAK_PATTERNS = [
        (r'DAN\s*(mode)?', 'dan_jailbreak', 0.9),
        (r'developer\s+mode', 'dev_mode_jailbreak', 0.8),
        (r'bypass\s+(safety|filter|restriction)', 'bypass_attempt', 0.9),
        (r'without\s+(restrictions?|limits?|filters?)', 'restriction_bypass', 0.7),
        (r'uncensored', 'uncensored_request', 0.6),
        (r'no\s+(ethical|moral)\s+(guidelines?|restrictions?)', 'ethics_bypass', 0.9),
    ]
    
    def __init__(self, sensitivity: float = 0.5):
        """
        Initialize detector.
        sensitivity: 0.0 (lenient) to 1.0 (strict)
        """
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        self._compiled_injection = [(re.compile(p, re.I), t, c) for p, t, c in self.INJECTION_PATTERNS]
        self._compiled_jailbreak = [(re.compile(p, re.I), t, c) for p, t, c in self.JAILBREAK_PATTERNS]
    
    def analyze(self, input_data: Any) -> Tuple[float, List[AdversarialSignal]]:
        """
        Analyze input for adversarial content.
        Returns (score, signals) where score is 0.0-1.0.
        """
        signals = []
        
        if input_data is None:
            return (0.0, signals)
        
        # Convert to text for analysis
        text = self._extract_text(input_data)
        if not text:
            return (0.0, signals)
        
        # Check injection patterns
        for pattern, signal_type, base_confidence in self._compiled_injection:
            matches = pattern.findall(text)
            if matches:
                signals.append(AdversarialSignal(
                    signal_type=signal_type,
                    confidence=base_confidence * self.sensitivity,
                    details=f"Found {len(matches)} match(es)"
                ))
        
        # Check jailbreak patterns
        for pattern, signal_type, base_confidence in self._compiled_jailbreak:
            matches = pattern.findall(text)
            if matches:
                signals.append(AdversarialSignal(
                    signal_type=signal_type,
                    confidence=base_confidence * self.sensitivity,
                    details=f"Found {len(matches)} match(es)"
                ))
        
        # Check for excessive special characters
        special_ratio = self._special_char_ratio(text)
        if special_ratio > 0.3:
            signals.append(AdversarialSignal(
                signal_type="excessive_special_chars",
                confidence=min(special_ratio, 0.7),
                details=f"Special char ratio: {special_ratio:.2f}"
            ))
        
        # Check for encoded content
        encoded_score = self._check_encoded(text)
        if encoded_score > 0.3:
            signals.append(AdversarialSignal(
                signal_type="potential_encoded_content",
                confidence=encoded_score,
            ))
        
        # Calculate overall score
        if not signals:
            return (0.0, signals)
        
        max_confidence = max(s.confidence for s in signals)
        avg_confidence = sum(s.confidence for s in signals) / len(signals)
        
        # Weighted combination
        score = max_confidence * 0.7 + avg_confidence * 0.3
        
        return (min(score, 1.0), signals)
    
    def _extract_text(self, data: Any) -> str:
        """Extract text from various input types."""
        if isinstance(data, str):
            return data
        
        if isinstance(data, dict):
            texts = []
            for key in ['text', 'content', 'message', 'input', 'query', 'prompt']:
                if key in data and isinstance(data[key], str):
                    texts.append(data[key])
            return ' '.join(texts)
        
        if isinstance(data, list):
            texts = [self._extract_text(item) for item in data[:10]]
            return ' '.join(filter(None, texts))
        
        return str(data) if data else ""
    
    def _special_char_ratio(self, text: str) -> float:
        """Calculate ratio of special characters."""
        if not text:
            return 0.0
        special = sum(1 for c in text if not c.isalnum() and not c.isspace())
        return special / len(text)
    
    def _check_encoded(self, text: str) -> float:
        """Check for potentially encoded content."""
        score = 0.0
        
        # Base64-like patterns
        b64_pattern = re.compile(r'[A-Za-z0-9+/]{20,}={0,2}')
        if b64_pattern.search(text):
            score += 0.4
        
        # Hex patterns
        hex_pattern = re.compile(r'(?:0x)?[0-9a-fA-F]{16,}')
        if hex_pattern.search(text):
            score += 0.3
        
        # Unicode escapes
        unicode_pattern = re.compile(r'\\u[0-9a-fA-F]{4}')
        if len(unicode_pattern.findall(text)) > 3:
            score += 0.3
        
        return min(score, 1.0)
    
    def get_score(self, input_data: Any) -> float:
        """Convenience method to get just the score."""
        score, _ = self.analyze(input_data)
        return score
