"""
Pseudonymization and Session Mapping Manager.
Generates consistent surrogate tokens per document/session and manages reversible mapping state.
"""

import datetime
import uuid
from typing import Any, Dict, List, Optional, Tuple


class Pseudonymizer:
    """
    Manages deterministic per-session pseudonymisation tokens and reversible mapping structures.
    """

    def __init__(self, mode: str = "surrogate_token"):
        self.mode = mode
        self.category_counters: Dict[str, int] = {}
        self.token_to_original: Dict[str, str] = {}
        self.original_to_token: Dict[str, str] = {}
        self.entities: List[Dict[str, Any]] = []
        self.date_mappings: List[Dict[str, Any]] = []
        self.document_id: str = f"doc_{uuid.uuid4()}"
        self.created_at: str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.date_shift_days: int = 0
        self.bracket_map: Dict[str, str] = {}

    def get_or_create_token(self, category: str, original_text: str, custom_token: Optional[str] = None) -> str:
        """
        Returns existing surrogate token for entity if already seen, or allocates a new consistent token.
        """
        norm_key = f"{category.upper()}:{original_text.strip().lower()}"
        if norm_key in self.original_to_token:
            return self.original_to_token[norm_key]

        if custom_token:
            token = custom_token
            if token in self.token_to_original and self.token_to_original[token].lower() != original_text.strip().lower():
                self.category_counters[category.upper()] = self.category_counters.get(category.upper(), 1) + 1
                idx = self.category_counters[category.upper()]
                token = f"[{category.upper()}_90+_{idx}]" if "90" in token else f"[{category.upper()}_{idx}]"
        else:
            cat_upper = category.upper()
            # Normalize category names to standard prefixes
            if cat_upper in {"DOCTOR", "PHYSICIAN"}:
                cat_upper = "PROVIDER"
            elif cat_upper in {"STREET", "STREET_ADDRESS"}:
                cat_upper = "ADDRESS"
            elif cat_upper in {"FACILITY", "CLINIC"}:
                cat_upper = "HOSPITAL"
            elif cat_upper in {"MEDICARE", "MEDICAID", "INSURANCE"}:
                cat_upper = "HEALTHPLAN"
            elif cat_upper in {"CELL", "TELEPHONE"}:
                cat_upper = "PHONE"

            if cat_upper == "AGE" and ("90" in original_text or "+" in original_text):
                if "[AGE_90+]" not in self.token_to_original or self.token_to_original["[AGE_90+]"].lower() == original_text.strip().lower():
                    token = "[AGE_90+]"
                else:
                    self.category_counters["AGE"] = self.category_counters.get("AGE", 1) + 1
                    idx = self.category_counters["AGE"]
                    token = f"[AGE_90+_{idx}]"
            else:
                self.category_counters[cat_upper] = self.category_counters.get(cat_upper, 0) + 1
                idx = self.category_counters[cat_upper]
                token = f"[{cat_upper}_{idx}]"

        self.original_to_token[norm_key] = token
        self.token_to_original[token] = original_text.strip()
        return token

    def record_entity(
        self,
        category: str,
        original_text: str,
        surrogate_token: str,
        start_char: int,
        end_char: int,
        confidence: float = 1.0,
        extra_meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Records entity occurrence in session registry."""
        entity_record = {
            "entity_id": f"ent_{len(self.entities) + 1:03d}",
            "category": category.upper(),
            "original_text": original_text,
            "surrogate_token": surrogate_token,
            "start_char": start_char,
            "end_char": end_char,
            "confidence": round(float(confidence), 4),
        }
        if extra_meta:
            entity_record.update(extra_meta)
        self.entities.append(entity_record)
        return entity_record

    def build_mapping(self) -> Dict[str, Any]:
        """Compiles self-contained, serializable mapping dictionary."""
        return {
            "version": "1.0.0",
            "document_id": self.document_id,
            "created_at": self.created_at,
            "date_shift_days": self.date_shift_days,
            "entities": self.entities,
            "token_to_original": self.token_to_original,
            "original_to_token": {k.split(":", 1)[1] if ":" in k else k: v for k, v in self.original_to_token.items()},
            "date_mappings": self.date_mappings,
            "bracket_map": self.bracket_map,
        }

    def apply_masking_to_text(self, text: str, sorted_spans: List[Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Applies surrogate token replacements to text in reverse offset order to prevent index shifting.
        
        Args:
            text: Source text to mask.
            sorted_spans: List of detected entity spans.
            
        Returns:
            tuple[masked_text, mapping_dict]
        """
        # Sort spans from end to beginning
        # Span object can be dict or object with start, end, category, text, confidence, shifted_text
        extracted = []
        for s in sorted_spans:
            if isinstance(s, dict):
                start = s["start"]
                end = s["end"]
                cat = s["category"]
                span_text = s.get("text", text[start:end])
                conf = s.get("confidence", 1.0)
                shifted = s.get("shifted_text", None)
                custom_token = s.get("custom_token", None)
            else:
                start = getattr(s, "start", 0)
                end = getattr(s, "end", 0)
                cat = getattr(s, "category", "ID")
                span_text = getattr(s, "text", text[start:end])
                conf = getattr(s, "confidence", 1.0)
                shifted = getattr(s, "shifted_text", None)
                custom_token = getattr(s, "custom_token", None)
            
            extracted.append({
                "start": start,
                "end": end,
                "category": cat,
                "text": span_text,
                "confidence": conf,
                "shifted_text": shifted,
                "custom_token": custom_token,
            })

        # Priority for overlapping spans: Clinical and demographic entities override generic gazetteers
        CATEGORY_PRIORITY = {
            "PATIENT": 100,
            "PROVIDER": 95,
            "FAMILY": 90,
            "SSN": 85,
            "MRN": 85,
            "NPI": 85,
            "LICENSE": 85,
            "DATE": 80,
            "AGE": 75,
            "PHONE": 70,
            "FAX": 70,
            "EMAIL": 70,
            "HOSPITAL": 60,
            "ADDRESS": 50,
            "CITY": 40,
            "COUNTY": 30,
            "ZIP": 20,
            "DEVICE": 40,
            "VEHICLE": 40,
            "BIOMETRIC": 40,
            "PHOTO": 40,
            "ACCESSION": 40,
            "URL": 40,
            "IP": 40,
            "ACCOUNT": 40,
            "HEALTHPLAN": 40,
        }

        # Filter overlapping spans
        extracted.sort(key=lambda x: (
            x["start"],
            -(x["end"] - x["start"]),
            -CATEGORY_PRIORITY.get(x["category"].upper(), 50),
            -x["confidence"]
        ))
        non_overlapping = []
        last_end = -1
        for item in extracted:
            if item["start"] >= last_end:
                non_overlapping.append(item)
                last_end = item["end"]
            else:
                if non_overlapping:
                    prev = non_overlapping[-1]
                    # Exact same span range: prefer higher semantic category priority
                    if item["start"] == prev["start"] and item["end"] == prev["end"]:
                        prev_prio = CATEGORY_PRIORITY.get(prev["category"].upper(), 50)
                        curr_prio = CATEGORY_PRIORITY.get(item["category"].upper(), 50)
                        if curr_prio > prev_prio or (curr_prio == prev_prio and item["confidence"] > prev["confidence"]):
                            non_overlapping.pop()
                            non_overlapping.append(item)
                    # If new span is longer and extends further, keep longer span
                    elif item["end"] > prev["end"]:
                        if (item["end"] - item["start"]) > (prev["end"] - prev["start"]):
                            non_overlapping.pop()
                            non_overlapping.append(item)
                            last_end = item["end"]

        # Step 1: Allocate tokens in natural document order (start ascending, top-to-bottom)
        non_overlapping.sort(key=lambda x: x["start"])
        for item in non_overlapping:
            cat = item["category"]
            orig_text = item["text"]
            shifted = item.get("shifted_text")
            custom_token = item.get("custom_token")

            if custom_token:
                token = self.get_or_create_token(cat, orig_text, custom_token=custom_token)
                replacement = token
            elif shifted:
                token = self.get_or_create_token("DATE", orig_text)
                replacement = token
                self.date_mappings.append({
                    "original_str": orig_text,
                    "shifted_str": shifted,
                    "surrogate_token": token,
                    "delta_days": self.date_shift_days,
                })
            else:
                token = self.get_or_create_token(cat, orig_text)
                replacement = token

            item["allocated_token"] = replacement
            item["record_token"] = token

        # Step 2: In-place text replacement in reverse order (bottom-to-top) to preserve offsets
        non_overlapping.sort(key=lambda x: x["start"], reverse=True)
        masked_text = text
        for item in non_overlapping:
            start = item["start"]
            end = item["end"]
            replacement = item["allocated_token"]
            cat = item["category"]
            orig_text = item["text"]
            conf = item["confidence"]

            self.record_entity(
                category=cat,
                original_text=orig_text,
                surrogate_token=replacement,
                start_char=start,
                end_char=end,
                confidence=conf,
            )

            # Substitute slice
            masked_text = masked_text[:start] + replacement + masked_text[end:]

        mapping = self.build_mapping()
        return masked_text, mapping
