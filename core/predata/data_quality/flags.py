"""Data quality flag generation."""
from typing import Any, List, Optional, Dict
from enum import Enum


class QualityFlag(Enum):
    """Quality flag types."""
    CLEAN = "clean"
    INCOMPLETE = "incomplete"
    NOISY = "noisy"
    INCONSISTENT = "inconsistent"
    UNTRUSTED_SOURCE = "untrusted_source"
    MISSING_REQUIRED = "missing_required"
    FORMAT_ERROR = "format_error"
    ENCODING_ISSUE = "encoding_issue"
    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    DUPLICATE = "duplicate"


class QualityFlagger:
    """
    Generates quality flags for input data.
    
    Usage:
        flagger = QualityFlagger()
        flags = flagger.check(input_data)
    """
    
    def __init__(
        self,
        min_length: int = 1,
        max_length: int = 100000,
        required_fields: Optional[List[str]] = None
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.required_fields = required_fields or []
    
    def check(
        self,
        input_data: Any,
        noise_level: Optional[float] = None,
        trust_score: Optional[float] = None
    ) -> List[str]:
        """
        Check input and return list of quality flags.
        Empty list = clean data.
        """
        flags = []
        
        # None check
        if input_data is None:
            return [QualityFlag.INCOMPLETE.value]
        
        # String checks
        if isinstance(input_data, str):
            flags.extend(self._check_string(input_data))
        
        # Dict checks
        elif isinstance(input_data, dict):
            flags.extend(self._check_dict(input_data))
        
        # List checks
        elif isinstance(input_data, list):
            flags.extend(self._check_list(input_data))
        
        # External scores
        if noise_level is not None and noise_level > 0.5:
            flags.append(QualityFlag.NOISY.value)
        
        if trust_score is not None and trust_score < 0.4:
            flags.append(QualityFlag.UNTRUSTED_SOURCE.value)
        
        # Clean if no flags
        if not flags:
            flags.append(QualityFlag.CLEAN.value)
        
        return list(set(flags))  # Remove duplicates
    
    def _check_string(self, text: str) -> List[str]:
        """Check string quality."""
        flags = []
        
        if len(text) < self.min_length:
            flags.append(QualityFlag.TOO_SHORT.value)
        
        if len(text) > self.max_length:
            flags.append(QualityFlag.TOO_LONG.value)
        
        # Encoding issues (replacement character)
        if '\ufffd' in text:
            flags.append(QualityFlag.ENCODING_ISSUE.value)
        
        # Suspicious patterns
        if text.count('???') > 3 or text.count('...') > 10:
            flags.append(QualityFlag.SUSPICIOUS_PATTERN.value)
        
        return flags
    
    def _check_dict(self, data: Dict) -> List[str]:
        """Check dict quality."""
        flags = []
        
        if not data:
            flags.append(QualityFlag.INCOMPLETE.value)
            return flags
        
        # Required fields
        for field in self.required_fields:
            if field not in data or data[field] is None:
                flags.append(QualityFlag.MISSING_REQUIRED.value)
                break
        
        # Check for empty values
        empty_count = sum(1 for v in data.values() if v is None or v == "")
        if empty_count > len(data) / 2:
            flags.append(QualityFlag.INCOMPLETE.value)
        
        # Inconsistent types
        value_types = set(type(v).__name__ for v in data.values() if v is not None)
        if len(value_types) > 5:
            flags.append(QualityFlag.INCONSISTENT.value)
        
        return flags
    
    def _check_list(self, data: List) -> List[str]:
        """Check list quality."""
        flags = []
        
        if not data:
            flags.append(QualityFlag.INCOMPLETE.value)
            return flags
        
        if len(data) > self.max_length:
            flags.append(QualityFlag.TOO_LONG.value)
        
        # Check for duplicates
        if len(data) != len(set(str(x) for x in data)):
            flags.append(QualityFlag.DUPLICATE.value)
        
        return flags
