"""
Core Response Rehydration Engine.
Exports: rehydrate(response, mapping, **kwargs) -> str
"""

import re
from typing import Any, Dict, Optional

from deid_gateway.core.collision_guard import CollisionGuard


def rehydrate(
    response: str,
    mapping: Optional[Dict[str, Any]],
    strict_mode: bool = False,
    **kwargs
) -> str:
    """
    Rehydrates foundation LLM response using the session mapping dictionary.
    
    Reverses surrogate tokens ([PATIENT_1], [PROVIDER_1], [DATE_1], [AGE_90+]) back
    to their original clinical entity values, resolves LLM fuzzy/mutated tokens,
    safely rejects hallucinated tokens, and restores non-PHI literal brackets.
    
    Args:
        response: LLM generated output containing surrogate tokens or references.
        mapping: The isolated dictionary produced by deidentify().
        strict_mode: If True, raises warning or tracks missing tokens in logs.
        **kwargs: Additional optional parameters.
        
    Returns:
        str: Rehydrated response with original clinical entities restored.
    """
    if not response or not isinstance(response, str):
        return response or ""

    if not mapping or not isinstance(mapping, dict):
        return response

    token_to_original = mapping.get("token_to_original", {})
    bracket_map = mapping.get("bracket_map", {})
    date_mappings = mapping.get("date_mappings", [])

    # Step 1: Normalize fuzzy or mutated LLM tokens (e.g. '[ patient 1 ]' -> '[PATIENT_1]')
    working_text = CollisionGuard.normalize_fuzzy_tokens(response)

    # Step 2: Validate against hallucinated tokens (tokens not present in mapping)
    valid_tokens = set(token_to_original.keys())
    working_text, _hallucinated = CollisionGuard.validate_and_filter_hallucinations(
        working_text,
        valid_tokens=valid_tokens
    )

    # Step 3: Replace surrogate tokens in descending order of length to avoid prefix collisions
    sorted_tokens = sorted(token_to_original.items(), key=lambda x: len(x[0]), reverse=True)
    for token, original_val in sorted_tokens:
        if token in working_text:
            working_text = working_text.replace(token, original_val)

    # Step 4: Invert shifted dates only when operating in direct date-shift mode (no surrogate tokens)
    if not token_to_original and date_mappings:
        for d_map in date_mappings:
            shifted_str = d_map.get("shifted_str")
            orig_str = d_map.get("original_str")
            if shifted_str and orig_str and shifted_str in working_text:
                # Only replace exact whole-word date matches
                working_text = re.sub(rf'\b{re.escape(shifted_str)}\b', orig_str, working_text)

    # Step 5: Restore non-PHI literal brackets
    working_text = CollisionGuard.unescape_literal_brackets(working_text, bracket_map)

    # Step 6: Clean up redundant age suffix duplication from generative completions
    # e.g. "94-year-old years old" -> "94-year-old", "90th birthday birthday" -> "90th birthday"
    working_text = re.sub(r'\b(\d+-(?:year-old|yr-old)|nonagenarian|centenarian)\s+(?:years?\s+old|yo|y/o|yr\s+old|yrs\s+old)\b', r'\1', working_text, flags=re.IGNORECASE)
    working_text = re.sub(r'\b(\d+(?:th|st|nd|rd)\s+birthday)\s+birthday\b', r'\1', working_text, flags=re.IGNORECASE)

    return working_text
