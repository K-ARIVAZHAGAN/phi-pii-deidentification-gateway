"""
Core HIPAA Safe Harbor De-Identification Pipeline.
Exports: deidentify(text, config=None, **kwargs) -> tuple[str, dict]
"""

from typing import Any, Dict, Optional, Tuple, Union

from deid_gateway.core.collision_guard import CollisionGuard
from deid_gateway.core.config import DeidConfig
from deid_gateway.core.date_shifter import DateShifter
from deid_gateway.core.eponyms import EponymDisambiguator
from deid_gateway.core.models.classifier import EntitySpan, HybridTokenClassifier
from deid_gateway.core.pseudonymizer import Pseudonymizer


def deidentify(
    text: str,
    config: Optional[Union[DeidConfig, Dict[str, Any]]] = None,
    **kwargs
) -> Tuple[str, Dict[str, Any]]:
    """
    De-identifies clinical text in accordance with HIPAA Safe Harbor (45 CFR § 164.514(b)(2)).
    
    Detects and pseudonymises all 18 Safe Harbor identifier categories, performs deterministic
    relative date shifting (preserving exact clinical intervals), aggregates ages >= 90 to [AGE_90+],
    and disambiguates medical eponyms to protect diagnostic meaning.
    
    Args:
        text: Raw clinical text containing potential PHI/PII.
        config: Optional DeidConfig instance or dict of configuration parameters.
        **kwargs: Configuration overrides (e.g. date_shift_days, patient_id, masking_mode).
        
    Returns:
        tuple[str, dict]:
            - masked_text: De-identified text with consistent surrogate tokens or shifted dates.
            - mapping: Cryptographically isolated session dictionary for exact round-trip rehydration.
    """
    # 1. Resolve configuration
    if isinstance(config, DeidConfig):
        cfg_dict = config.to_dict()
        cfg_dict.update(kwargs)
        cfg = DeidConfig.from_dict(cfg_dict)
    elif isinstance(config, dict):
        cfg_dict = dict(config)
        cfg_dict.update(kwargs)
        cfg = DeidConfig.from_dict(cfg_dict)
    else:
        cfg = DeidConfig.from_dict(kwargs)

    if not text or not isinstance(text, str):
        empty_pseudonymizer = Pseudonymizer(mode=cfg.masking_mode)
        return text or "", empty_pseudonymizer.build_mapping()

    # 2. Escape literal non-PHI brackets in source document
    working_text = text
    bracket_map: Dict[str, str] = {}
    if cfg.escape_literal_brackets:
        working_text, bracket_map = CollisionGuard.escape_literal_brackets(working_text)

    # 3. Multi-layer Entity Span Extraction (<1B Parameter Model + Regex Ensemble)
    classifier = HybridTokenClassifier(config=cfg)
    spans = classifier.predict_spans(working_text, config=cfg)

    # 4. Clinical Ambiguity & Eponym Disambiguation Tri-Filter
    if cfg.preserve_eponyms:
        eponym_engine = EponymDisambiguator()
        spans = eponym_engine.filter_spans(spans, working_text)

    # 5. Deterministic Date Shifting & Age > 89 Aggregation
    date_shifter = DateShifter(salt=cfg.salt)
    delta_days = date_shifter.compute_delta_days(
        seed=cfg.patient_id or text,
        explicit_days=cfg.date_shift_days
    )

    processed_spans: list[EntitySpan] = []
    for span in spans:
        cat_upper = span.category.upper()
        
        # Check for relative durations to preserve
        if cat_upper == "DATE" and cfg.preserve_relative_dates:
            if date_shifter.is_relative_expression(span.text):
                # Relative clinical duration phrase (e.g. "post-operative day 2") - DO NOT MASK
                continue
            
            # Attempt date shift calculation
            shift_res = date_shifter.parse_and_shift(span.text, delta_days)
            if shift_res:
                span.shifted_text = shift_res.shifted_text
        
        # Check for Age >= 90 aggregation
        if cat_upper == "AGE" or date_shifter.is_age_90_plus(span.text):
            span.custom_token = "[AGE_90+]"

        processed_spans.append(span)

    # 6. Pseudonymization and Token Allocation
    pseudonymizer = Pseudonymizer(mode=cfg.masking_mode)
    pseudonymizer.date_shift_days = delta_days
    pseudonymizer.bracket_map = bracket_map

    masked_text, mapping = pseudonymizer.apply_masking_to_text(working_text, processed_spans)

    return masked_text, mapping
