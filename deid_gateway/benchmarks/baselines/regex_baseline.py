"""
Baseline 1: Regex-Only De-Identification Engine.
Implements a pure deterministic, regular-expression-based de-identifier using compiled patterns
for structured and semi-structured HIPAA Safe Harbor identifiers.
"""

import re
from typing import Any, Dict, List, Optional, Tuple


class RegexDeidBaseline:
    """
    Baseline 1: High-speed, rule-based regular expression de-identifier.
    Covers structured patterns: SSN, Phone, Fax, Email, IP, URL, Dates, MRN, Zip codes,
    NPI/Licenses, Age > 89, and honorific capitalized name heuristics.
    """

    # Comprehensive compiled regex patterns
    PATTERNS: Dict[str, List[re.Pattern]] = {
        "SSN": [
            re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            re.compile(r"\b\d{9}\b"),
        ],
        "PHONE": [
            re.compile(r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"),
            re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b"),
        ],
        "FAX": [
            re.compile(r"(?i)\b(?:fax|facsimile)[\s:#]*((?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4})\b"),
        ],
        "EMAIL": [
            re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        ],
        "URL": [
            re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+"),
        ],
        "IP_ADDRESS": [
            re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"),
        ],
        "DATE": [
            # ISO: 2023-10-15
            re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
            # US: 10/15/2023 or 10-15-2023
            re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
            # Textual: October 15, 2023 or 15 October 2023
            re.compile(
                r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s*,?\s+\d{4}\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b",
                re.IGNORECASE,
            ),
        ],
        "MRN": [
            re.compile(r"(?i)\b(?:MRN|Medical Record Number|Chart\s*#|Patient\s*ID)[\s:#]*([A-Z0-9-]{6,15})\b"),
            re.compile(r"\b[A-Z]{2,5}-\d{6,8}\b"),
        ],
        "LOCATION_ZIP": [
            re.compile(r"\b\d{5}(?:-\d{4})?\b"),
        ],
        "LICENSE_NPI": [
            re.compile(r"(?i)\b(?:NPI|National Provider Identifier)[\s:#]*(\d{10})\b"),
            re.compile(r"\b1\d{9}\b"),
        ],
        "LICENSE_DEA": [
            re.compile(r"(?i)\b(?:DEA\s*#?|DEA\s*Reg)[\s:#]*([A-Z]{2}\d{7})\b"),
        ],
        "AGE": [
            re.compile(r"\b(?:9[0-9]|1\d{2})\s*(?:year[s]?-old|yo|years of age|year old)\b", re.IGNORECASE),
        ],
        "NAME_PROVIDER": [
            re.compile(r"\b(?:Dr\.|Doctor|Attending(?:\s+Oncologist|\s+Physician)?|Consultant:?|Physician:?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:,\s*(?:MD|DO|MBBS|PhD))?)\b"),
            re.compile(r"(?i)\bSigned\s+by:?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:,\s*(?:MD|DO|MBBS|PhD))?)\b"),
        ],
        "NAME_PATIENT": [
            re.compile(r"(?i)\bPATIENT(?:\s+NAME)?[\s:#]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b"),
            re.compile(r"(?i)\b(?:Mr\.|Mrs\.|Ms\.|Miss)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"),
        ],
    }

    def __init__(self):
        self.model_name = "RegexBaselineDeidentifier"
        self.parameter_count = 0  # Pure heuristic / regex

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Scans text with all regex patterns and returns sorted, deduplicated, non-overlapping entity spans.
        """
        if not text:
            return []

        raw_spans: List[Dict[str, Any]] = []

        for category, pattern_list in self.PATTERNS.items():
            for pattern in pattern_list:
                for match in pattern.finditer(text):
                    # If pattern has capturing group, use that span if group 1 is populated
                    if match.groups() and match.group(1):
                        start, end = match.start(1), match.end(1)
                        matched_text = match.group(1)
                    else:
                        start, end = match.start(), match.end()
                        matched_text = match.group()

                    if len(matched_text.strip()) > 0:
                        raw_spans.append({
                            "start": start,
                            "end": end,
                            "text": matched_text,
                            "category": category,
                            "confidence": 1.0,
                        })

        # Resolve overlaps by priority: longer span wins, earlier start wins
        raw_spans.sort(key=lambda s: (s["start"], -(s["end"] - s["start"])))

        resolved_spans: List[Dict[str, Any]] = []
        last_end = -1

        for span in raw_spans:
            if span["start"] >= last_end:
                resolved_spans.append(span)
                last_end = span["end"]
            elif span["end"] > last_end and (span["end"] - span["start"]) > (last_end - resolved_spans[-1]["start"]):
                # Current span is significantly longer and overlaps: replace last span if starting earlier or equal
                if span["start"] == resolved_spans[-1]["start"]:
                    resolved_spans[-1] = span
                    last_end = span["end"]

        return resolved_spans

    def predict_spans(self, text: str) -> List[Dict[str, Any]]:
        """Evaluation alias for span extraction."""
        return self.extract_entities(text)

    def deidentify(self, text: str, config: Optional[Any] = None) -> Tuple[str, Dict[str, Any]]:
        """
        De-identifies text using regex pattern extraction and substitutes surrogate tokens.
        
        Returns:
            masked_text: De-identified text string.
            mapping: Dictionary mapping surrogate tokens to original entity values.
        """
        if not text:
            return "", {"token_to_original": {}, "original_to_token": {}, "entities": []}

        spans = self.extract_entities(text)
        
        token_to_original: Dict[str, str] = {}
        original_to_token: Dict[str, str] = {}
        category_counters: Dict[str, int] = {}

        # Replace from end to beginning to preserve character offsets
        sorted_spans = sorted(spans, key=lambda s: s["start"], reverse=True)
        masked_chars = list(text)

        for span in sorted_spans:
            orig = span["text"]
            cat = span["category"]

            # Format surrogate token
            prefix = cat.replace("NAME_", "").replace("LOCATION_", "")
            if cat == "AGE" and any(str(a) in orig for a in ["90", "91", "92", "93", "94", "95", "96", "97", "98", "99", "100", "101", "102"]):
                surrogate = "[AGE_90+]"
            else:
                if orig in original_to_token:
                    surrogate = original_to_token[orig]
                else:
                    category_counters[prefix] = category_counters.get(prefix, 0) + 1
                    surrogate = f"[{prefix}_{category_counters[prefix]}]"

            token_to_original[surrogate] = orig
            original_to_token[orig] = surrogate

            masked_chars[span["start"]:span["end"]] = list(surrogate)

        masked_text = "".join(masked_chars)

        mapping = {
            "version": "1.0.0",
            "model": self.model_name,
            "token_to_original": token_to_original,
            "original_to_token": original_to_token,
            "entities": spans,
        }

        return masked_text, mapping


# Alias for spec compliance
RegexBaselineDeidentifier = RegexDeidBaseline
