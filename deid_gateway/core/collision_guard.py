"""
Collision Guard, Bracket Escaping, and LLM Hallucination / Corruption Defense Engine.
Safeguards clinical text against literal bracket collisions, fuzzy token mutations,
and hallucinated surrogate tags from downstream foundation models.
"""

import re
from typing import Dict, List, Optional, Set, Tuple


class CollisionGuard:
    """
    Guards roundtrip integrity between De-Identification Gateway and Foundation LLMs.
    """

    # Unicode mathematical white square brackets for safe escaping
    ESCAPE_OPEN = "\u27E6"   # ⟦
    ESCAPE_CLOSE = "\u27E7"  # ⟧

    # Known PHI category tags used by the gateway
    KNOWN_CATEGORIES = {
        "PATIENT", "PROVIDER", "DOCTOR", "PHYSICIAN", "FAMILY", "HOSPITAL", "FACILITY",
        "ADDRESS", "STREET", "CITY", "COUNTY", "STATE", "ZIP", "DATE", "AGE", "AGE_90+",
        "PHONE", "FAX", "EMAIL", "SSN", "MRN", "HEALTHPLAN", "ACCOUNT", "LICENSE", "NPI",
        "VEHICLE", "DEVICE", "URL", "IP", "BIOMETRIC", "PHOTO", "ACCESSION", "ID", "ORGANIZATION"
    }

    # Regex matching fuzzy or mutated surrogate tokens in LLM responses
    FUZZY_TOKEN_PATTERN = re.compile(
        r'(?:\[|\()\s*(PATIENT|PROVIDER|DOCTOR|PHYSICIAN|FAMILY|HOSPITAL|FACILITY|'
        r'ADDRESS|STREET|CITY|COUNTY|STATE|ZIP|DATE|AGE|PHONE|FAX|EMAIL|SSN|MRN|'
        r'HEALTHPLAN|ACCOUNT|LICENSE|NPI|VEHICLE|DEVICE|URL|IP|BIOMETRIC|PHOTO|ACCESSION|ID)'
        r'[\s_]+([A-Za-z0-9_+-]+)\s*(?:\]|\))|'
        r'\[\s*([A-Za-z0-9_+-]+)\s*\]',
        re.IGNORECASE
    )

    # Standalone unbracketed surrogate token pattern (e.g. "PATIENT_1 was discharged")
    UNBRACKETED_TOKEN_PATTERN = re.compile(
        r'(?<!\[)\b(PATIENT_\d+|PROVIDER_[A-Za-z0-9]+|FAMILY_\d+|HOSPITAL_\d+|ADDRESS_\d+|'
        r'CITY_\d+|COUNTY_\d+|ZIP_\d+|DATE_\d+|AGE_90\+_\d+|AGE_90\+|AGE_\d+|PHONE_\d+|FAX_\d+|'
        r'EMAIL_\d+|SSN_\d+|MRN_\d+|HEALTHPLAN_\d+|ACCOUNT_\d+|LICENSE_\d+|NPI_\d+|'
        r'VEHICLE_\d+|DEVICE_\d+|URL_\d+|IP_\d+|BIOMETRIC_\d+|PHOTO_\d+|ACCESSION_\d+|ID_\d+)\b(?!\])'
    )

    @classmethod
    def escape_literal_brackets(cls, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Escapes literal non-PHI brackets in source clinical notes (e.g. '[x]', '[1]', '[Normal]').
        
        Returns:
            escaped_text: Text with non-PHI brackets replaced with Unicode white brackets.
            bracket_map: Dictionary mapping placeholder strings to original brackets.
        """
        bracket_map: Dict[str, str] = {}
        
        def _replace_bracket(match: re.Match) -> str:
            content = match.group(1).strip()
            # Check if content looks like a PHI tag (e.g. PATIENT_1, DATE_1, AGE_90+)
            tokens = content.upper().split()
            first_word = tokens[0].split('_')[0] if tokens else ""
            if first_word in cls.KNOWN_CATEGORIES:
                return match.group(0)  # Keep PHI tag unescaped
            
            # Non-PHI bracket: escape to Unicode delimiters
            escaped = f"{cls.ESCAPE_OPEN}{match.group(1)}{cls.ESCAPE_CLOSE}"
            bracket_map[escaped] = match.group(0)
            return escaped

        # Match bracketed expressions that don't span multiple lines
        escaped_text = re.sub(r'\[([^\]\n]+)\]', _replace_bracket, text)
        return escaped_text, bracket_map

    @classmethod
    def unescape_literal_brackets(cls, text: str, bracket_map: Optional[Dict[str, str]] = None) -> str:
        """
        Restores escaped brackets (Unicode white brackets) back to original standard brackets.
        """
        if bracket_map:
            for escaped_placeholder, original_bracket in bracket_map.items():
                text = text.replace(escaped_placeholder, original_bracket)

        # Also replace any remaining Unicode escape delimiters directly
        text = text.replace(cls.ESCAPE_OPEN, "[").replace(cls.ESCAPE_CLOSE, "]")
        return text

    @classmethod
    def normalize_fuzzy_tokens(cls, text: str) -> str:
        """
        Normalizes mutated or whitespace-altered surrogate tokens from LLM outputs.
        E.g. '[ patient 1 ]' -> '[PATIENT_1]', '(PROVIDER_A)' -> '[PROVIDER_A]'.
        """
        # Step 1: Wrap unbracketed tokens if foundation LLM dropped brackets
        def _wrap_unbracketed(match: re.Match) -> str:
            token = match.group(1).upper()
            return f"[{token}]"

        text = cls.UNBRACKETED_TOKEN_PATTERN.sub(_wrap_unbracketed, text)

        # Step 2: Normalize fuzzy spaced/cased brackets
        def _normalize_match(match: re.Match) -> str:
            if match.group(3):  # Single word inside brackets: [PATIENT_1] or [age_90+]
                raw = match.group(3).strip()
                raw_upper = raw.upper()
                if re.fullmatch(r'AGE_90\+(?:_\d+)?', raw_upper):
                    return f"[{raw_upper}]"
                # Handle [AGE 90+] or [AGE90+]
                if "AGE" in raw_upper and "90" in raw_upper:
                    return "[AGE_90+]"
                
                # Check if it corresponds to a known PHI category prefix
                prefix = raw_upper.split('_')[0] if '_' in raw_upper else raw_upper
                if prefix in cls.KNOWN_CATEGORIES:
                    return f"[{raw_upper}]"
                return match.group(0)  # Preserve non-PHI brackets as-is
            
            cat = match.group(1).strip().upper()
            idx = match.group(2).strip().upper()
            
            # Unify category aliases
            if cat in {"DOCTOR", "PHYSICIAN"}:
                cat = "PROVIDER"
            elif cat in {"STREET"}:
                cat = "ADDRESS"
            elif cat in {"FACILITY"}:
                cat = "HOSPITAL"
                
            if cat == "AGE" and "90" in idx:
                if re.fullmatch(r'90\+(?:_\d+)?', idx):
                    return f"[AGE_{idx}]"
                return "[AGE_90+]"
                
            return f"[{cat}_{idx}]"

        # Apply regex replacement
        normalized = cls.FUZZY_TOKEN_PATTERN.sub(_normalize_match, text)
        return normalized

    @classmethod
    def validate_and_filter_hallucinations(
        cls,
        text: str,
        valid_tokens: Set[str]
    ) -> Tuple[str, List[str]]:
        """
        Detects any surrogate tokens present in LLM text that were not generated in the session mapping.
        Preserves them without crashing and reports the list of hallucinated tokens.
        """
        hallucinated: List[str] = []
        found_tokens = re.findall(r'\[[A-Z0-9_+-]+\]', text)
        for token in found_tokens:
            if token not in valid_tokens:
                hallucinated.append(token)

        return text, hallucinated
