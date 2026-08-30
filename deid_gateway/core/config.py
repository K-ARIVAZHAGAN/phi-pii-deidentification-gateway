"""
Configuration module for PHI/PII De-Identification Gateway.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class DeidConfig:
    """
    Configuration options for the de-identification and rehydration pipeline.
    
    Attributes:
        masking_mode: "surrogate_token" (e.g. [PATIENT_1]) or "synthetic_replacement" (e.g. John -> Michael)
        date_shift_enabled: Whether to shift calendar dates deterministically
        date_shift_days: Explicit signed day offset; if None, deterministically derived from patient_id / document
        patient_id: Optional patient identifier for deterministic per-patient salt/offset
        salt: Cryptographic salt for deterministic hashing
        age_aggregation_threshold: Cutoff age for Safe Harbor aggregation (default 89 -> ages >= 90 mapped to [AGE_90+])
        strictness: "high_recall", "balanced", or "strict"
        preserve_eponyms: Whether to disambiguate and protect medical eponyms (e.g. Parkinson's disease)
        escape_literal_brackets: Whether to escape pre-existing non-PHI brackets in source text
        enable_model_ner: Whether to enable sub-1B transformer/hybrid NER classification
        confidence_threshold: Minimum confidence score for entity span extraction (0.0 to 1.0)
        preserve_relative_dates: Whether to leave relative duration phrases (e.g. "post-op day 2") unmasked
        custom_regex: Optional custom dictionary mapping category names to regex patterns
    """
    masking_mode: str = "surrogate_token"
    date_shift_enabled: bool = True
    date_shift_days: Optional[int] = None
    patient_id: Optional[str] = None
    salt: str = "deid_gateway_secure_salt_v1"
    age_aggregation_threshold: int = 89
    strictness: str = "high_recall"
    preserve_eponyms: bool = True
    escape_literal_brackets: bool = True
    enable_model_ner: bool = True
    confidence_threshold: float = 0.5
    preserve_relative_dates: bool = True
    custom_regex: Optional[Dict[str, str]] = None
    extra_options: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]] = None) -> "DeidConfig":
        """Build DeidConfig from dictionary or return default config if None."""
        if not d:
            return cls()
        valid_fields = {f for f in cls.__dataclass_fields__ if f != "extra_options"}
        known_kwargs = {}
        extras = {}
        for k, v in d.items():
            if k in valid_fields:
                known_kwargs[k] = v
            else:
                extras[k] = v
        return cls(**known_kwargs, extra_options=extras)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary representation."""
        res = {
            "masking_mode": self.masking_mode,
            "date_shift_enabled": self.date_shift_enabled,
            "date_shift_days": self.date_shift_days,
            "patient_id": self.patient_id,
            "salt": self.salt,
            "age_aggregation_threshold": self.age_aggregation_threshold,
            "strictness": self.strictness,
            "preserve_eponyms": self.preserve_eponyms,
            "escape_literal_brackets": self.escape_literal_brackets,
            "enable_model_ner": self.enable_model_ner,
            "confidence_threshold": self.confidence_threshold,
            "preserve_relative_dates": self.preserve_relative_dates,
            "custom_regex": self.custom_regex,
        }
        res.update(self.extra_options)
        return res
