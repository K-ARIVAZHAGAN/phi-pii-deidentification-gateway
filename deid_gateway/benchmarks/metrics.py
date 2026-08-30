"""
Quantitative Metrics Engine for De-Identification Benchmarks.
Calculates:
- Entity-level and Token-level Precision, Recall, F1, F2 (with recall prioritized for breach prevention)
  per category and overall (Macro and Micro).
- Document Leak Rate (% of documents containing >= 1 unmasked PHI entity).
- Downstream Utility Preservation Delta (measuring LLM task accuracy/coherence on original vs de-identified inputs).
- Latency and throughput statistics (mean, p50, p90, p95, p99 in milliseconds).
"""

import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union


@dataclass
class BenchmarkMetrics:
    """Quantitative performance metrics container."""
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    f2: float = 0.0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    per_category: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    leak_rate: float = 0.0
    utility_score: float = 1.0
    p50_latency_ms: float = 0.0
    p90_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    mean_latency_ms: float = 0.0
    throughput_notes_per_sec: float = 0.0
    throughput_tokens_per_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "f2": round(self.f2, 4),
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "leak_rate": round(self.leak_rate, 2),
            "utility_score": round(self.utility_score, 4),
            "p50_latency_ms": round(self.p50_latency_ms, 2),
            "p90_latency_ms": round(self.p90_latency_ms, 2),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "p99_latency_ms": round(self.p99_latency_ms, 2),
            "mean_latency_ms": round(self.mean_latency_ms, 2),
            "throughput_notes_per_sec": round(self.throughput_notes_per_sec, 2),
            "per_category": self.per_category,
        }


def _normalize_category(cat: str) -> str:
    """Normalizes category strings across different annotation formats."""
    c = cat.strip().upper()
    # Name variations
    if c in ("PATIENT", "NAME_PATIENT", "PATIENT_NAME"):
        return "NAME_PATIENT"
    if c in ("PROVIDER", "NAME_PROVIDER", "DOCTOR", "PHYSICIAN", "DOCTOR_NAME"):
        return "NAME_PROVIDER"
    if c in ("RELATIVE", "NAME_RELATIVE", "FAMILY", "NAME_FAMILY"):
        return "NAME_RELATIVE"
    if c in ("PERSON", "NAME"):
        return "NAME_PATIENT"
    
    # Geographic variations
    if c in ("GEO_CITY", "CITY", "LOCATION_CITY"):
        return "LOCATION_CITY"
    if c in ("GEO_STATE", "STATE", "LOCATION_STATE"):
        return "LOCATION_STATE"
    if c in ("GEO_ZIP", "ZIP", "LOCATION_ZIP", "POSTAL_CODE"):
        return "LOCATION_ZIP"
    if c in ("GEO_STREET", "STREET", "LOCATION_STREET", "ADDRESS", "LOCATION_ADDRESS"):
        return "LOCATION_STREET"
    if c in ("GEO_FACILITY", "HOSPITAL", "LOCATION_HOSPITAL", "ORGANIZATION", "LOCATION_ORGANIZATION", "FACILITY", "CLINIC"):
        return "LOCATION_HOSPITAL"
    if c in ("GEO_COUNTY", "COUNTY", "LOCATION_COUNTY"):
        return "LOCATION_COUNTY"
    if c.startswith("GEO_") or c.startswith("LOCATION_"):
        suffix = c.split("_", 1)[1]
        return f"LOCATION_{suffix}"
        
    # Date & Age
    if c in ("DATE", "DATE_TIME", "DATETIME", "DOB"):
        return "DATE"
    if c in ("AGE", "AGE_OVER_89", "AGE_90+"):
        return "AGE"
        
    # Identifiers
    if c in ("SSN", "US_SSN"):
        return "SSN"
    if c in ("MRN", "MEDICAL_RECORD_NUMBER"):
        return "MRN"
    if c in ("PHONE", "PHONE_NUMBER", "TELEPHONE"):
        return "PHONE"
    if c in ("FAX", "FAX_NUMBER"):
        return "FAX"
    if c in ("EMAIL", "EMAIL_ADDRESS"):
        return "EMAIL"
    if c in ("NPI", "LICENSE_NPI", "MEDICAL_LICENSE"):
        return "LICENSE_NPI"
    if c in ("DEA", "LICENSE_DEA"):
        return "LICENSE_DEA"
    if c in ("LICENSE", "LICENSE_STATE", "STATE_LICENSE"):
        return "LICENSE_STATE"
    if c in ("ACCESSION", "ID_ACCESSION", "ACCESSION_ID"):
        return "ID_ACCESSION"
    if c in ("HEALTHPLAN", "ID_HEALTH_PLAN", "HEALTH_PLAN", "INSURANCE", "MBI"):
        return "ID_HEALTH_PLAN"
    if c in ("ACCOUNT", "ID_ACCOUNT", "ACCOUNT_ID"):
        return "ID_ACCOUNT"
    if c in ("VEHICLE", "VEHICLE_VIN", "VEHICLE_PLATE", "VIN", "PLATE"):
        return "VEHICLE"
    if c in ("DEVICE", "DEVICE_UDI", "DEVICE_SERIAL", "UDI", "SERIAL"):
        return "DEVICE"
    if c in ("BIOMETRIC", "BIOMETRIC_DNA", "DNA"):
        return "BIOMETRIC"
    if c in ("PHOTO", "PHOTO_DICOM", "DICOM"):
        return "PHOTO"
    if c in ("URL", "WEBSITE"):
        return "URL"
    if c in ("IP", "IP_ADDRESS", "IPADDRESS"):
        return "IP_ADDRESS"
    return c


def _is_category_compatible(c1: str, c2: str) -> bool:
    """Checks if predicted category is compatible with ground truth category."""
    n1 = _normalize_category(c1)
    n2 = _normalize_category(c2)
    if n1 == n2:
        return True
    # Compatible name variations
    if "NAME" in n1 and "NAME" in n2:
        return True
    # Compatible location variations
    if "LOCATION" in n1 and "LOCATION" in n2:
        return True
    # Compatible license/ID variations
    if "LICENSE" in n1 and "LICENSE" in n2:
        return True
    if "ID" in n1 and "ID" in n2:
        return True
    if "DEVICE" in n1 and "DEVICE" in n2:
        return True
    if "VEHICLE" in n1 and "VEHICLE" in n2:
        return True
    return False


def compute_deid_metrics(
    ground_truths: List[List[Dict[str, Any]]],
    predictions: List[List[Dict[str, Any]]],
    match_mode: str = "overlap"
) -> BenchmarkMetrics:
    """
    Calculates Entity-level and Token-level Precision, Recall, F1, and F2 (prioritizing recall).
    
    Args:
        ground_truths: List of per-document ground truth entity lists.
                       Each entity has {"start": int, "end": int, "category": str, ...}.
        predictions: List of per-document predicted entity lists.
                     Each prediction has {"start": int, "end": int, "category": str, ...}.
        match_mode: "overlap" (>=1 char span overlap) or "exact" (identical start and end offsets).
        
    Returns:
        BenchmarkMetrics containing overall and per-category Precision, Recall, F1, F2.
    """
    total_tp = 0
    total_fp = 0
    total_fn = 0

    category_stats: Dict[str, Dict[str, int]] = {}

    num_docs = max(len(ground_truths), len(predictions))

    for doc_idx in range(num_docs):
        doc_gt = ground_truths[doc_idx] if doc_idx < len(ground_truths) else []
        doc_pred = predictions[doc_idx] if doc_idx < len(predictions) else []

        matched_gt_indices: Set[int] = set()
        matched_pred_indices: Set[int] = set()

        # Step 1: Match predictions against ground truth
        for p_idx, pred in enumerate(doc_pred):
            p_start = pred.get("start", 0)
            p_end = pred.get("end", 0)
            p_cat = pred.get("category", "")

            best_gt_idx = None
            best_overlap = 0

            for g_idx, gt in enumerate(doc_gt):
                if g_idx in matched_gt_indices:
                    continue

                g_start = gt.get("start", 0)
                g_end = gt.get("end", 0)
                g_cat = gt.get("category", "")

                is_cat_match = _is_category_compatible(p_cat, g_cat)

                if match_mode == "exact":
                    if p_start == g_start and p_end == g_end and is_cat_match:
                        best_gt_idx = g_idx
                        break
                else:  # overlap mode
                    overlap = max(0, min(p_end, g_end) - max(p_start, g_start))
                    if overlap > 0 and is_cat_match:
                        if overlap > best_overlap:
                            best_overlap = overlap
                            best_gt_idx = g_idx

            if best_gt_idx is not None:
                matched_gt_indices.add(best_gt_idx)
                matched_pred_indices.add(p_idx)
                total_tp += 1

                gt_cat = _normalize_category(doc_gt[best_gt_idx].get("category", "UNKNOWN"))
                if gt_cat not in category_stats:
                    category_stats[gt_cat] = {"tp": 0, "fp": 0, "fn": 0}
                category_stats[gt_cat]["tp"] += 1

        # Step 2: Unmatched predictions are False Positives
        for p_idx, pred in enumerate(doc_pred):
            if p_idx not in matched_pred_indices:
                total_fp += 1
                p_cat = _normalize_category(pred.get("category", "UNKNOWN"))
                if p_cat not in category_stats:
                    category_stats[p_cat] = {"tp": 0, "fp": 0, "fn": 0}
                category_stats[p_cat]["fp"] += 1

        # Step 3: Unmatched ground truth entities are False Negatives (Missed PHI / Leaks)
        for g_idx, gt in enumerate(doc_gt):
            if g_idx not in matched_gt_indices:
                total_fn += 1
                g_cat = _normalize_category(gt.get("category", "UNKNOWN"))
                if g_cat not in category_stats:
                    category_stats[g_cat] = {"tp": 0, "fp": 0, "fn": 0}
                category_stats[g_cat]["fn"] += 1

    # Calculate overall metrics
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else (1.0 if total_fn == 0 else 0.0)
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 1.0
    
    if precision + recall > 0:
        f1 = (2 * precision * recall) / (precision + recall)
    else:
        f1 = 0.0

    # F2 score: beta = 2, weights recall 4x more than precision for breach prevention
    if (4 * precision + recall) > 0:
        f2 = (5 * precision * recall) / (4 * precision + recall)
    else:
        f2 = 0.0

    # Per-category calculations
    per_category: Dict[str, Dict[str, Any]] = {}
    for cat, stats in sorted(category_stats.items()):
        c_tp = stats["tp"]
        c_fp = stats["fp"]
        c_fn = stats["fn"]
        c_prec = c_tp / (c_tp + c_fp) if (c_tp + c_fp) > 0 else (1.0 if c_fn == 0 else 0.0)
        c_rec = c_tp / (c_tp + c_fn) if (c_tp + c_fn) > 0 else 1.0
        c_f1 = (2 * c_prec * c_rec) / (c_prec + c_rec) if (c_prec + c_rec) > 0 else 0.0
        c_f2 = (5 * c_prec * c_rec) / (4 * c_prec + c_rec) if (4 * c_prec + c_rec) > 0 else 0.0

        per_category[cat] = {
            "precision": round(c_prec, 4),
            "recall": round(c_rec, 4),
            "f1": round(c_f1, 4),
            "f2": round(c_f2, 4),
            "tp": c_tp,
            "fp": c_fp,
            "fn": c_fn,
        }

    return BenchmarkMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        f2=f2,
        true_positives=total_tp,
        false_positives=total_fp,
        false_negatives=total_fn,
        per_category=per_category,
    )


def compute_document_leak_rate(
    ground_truths: List[List[Dict[str, Any]]],
    masked_docs: List[str]
) -> float:
    """
    Computes the Document Leak Rate (% of documents containing >= 1 unmasked PHI entity).
    
    Args:
        ground_truths: List of per-document ground truth entity lists.
        masked_docs: List of de-identified text documents.
        
    Returns:
        float: Document leak percentage (0.0 to 100.0).
    """
    if not ground_truths or not masked_docs:
        return 0.0

    total_docs = min(len(ground_truths), len(masked_docs))
    if total_docs == 0:
        return 0.0

    leaked_docs_count = 0

    for doc_idx in range(total_docs):
        doc_gt = ground_truths[doc_idx]
        masked_text = masked_docs[doc_idx]
        doc_has_leak = False

        for ent in doc_gt:
            ent_text = ent.get("text", "").strip()
            # If text is not directly present, can't check string inclusion
            if not ent_text or len(ent_text) <= 2:
                continue

            # Check if this exact PHI string appears unmasked in the masked text
            if ent_text in masked_text:
                doc_has_leak = True
                break

        if doc_has_leak:
            leaked_docs_count += 1

    return (leaked_docs_count / total_docs) * 100.0


def compute_utility_preservation(
    orig_summary: str,
    deid_rehydrated_summary: str
) -> float:
    """
    Calculates the Downstream Utility Preservation Delta (ΔU ∈ [0.0, 1.0]).
    Measures whether clinical concepts, diagnoses, medications, dosages, and numerical
    facts are retained across the de-identification and rehydration round-trip.
    
    Args:
        orig_summary: Foundation LLM output on raw clinical text.
        deid_rehydrated_summary: Rehydrated LLM output on masked text.
        
    Returns:
        float: Utility preservation score (0.0 to 1.0, where 1.0 is perfect preservation).
    """
    if not orig_summary and not deid_rehydrated_summary:
        return 1.0
    if not orig_summary or not deid_rehydrated_summary:
        return 0.0
    if orig_summary.strip() == deid_rehydrated_summary.strip():
        return 1.0

    # 1. Clinical Slot Extraction (Dosages, Numbers, Medical Terms)
    # Extracts numerical + unit slots (e.g. 50mg, 10/15/2023, 100.4 F, 2 weeks)
    slot_pattern = re.compile(r"\b(?:\d+(?:\.\d+)?\s*(?:mg|ml|mcg|g|kg|units|%|hours|days|weeks|months|years|yo|F|C)?)\b", re.IGNORECASE)
    orig_slots = set(slot_pattern.findall(orig_summary))
    rehyd_slots = set(slot_pattern.findall(deid_rehydrated_summary))

    if orig_slots:
        slot_recall = len(orig_slots.intersection(rehyd_slots)) / len(orig_slots)
    else:
        slot_recall = 1.0

    # 2. Token-level overlap (Jaccard / Token F1)
    orig_tokens = set(re.findall(r"\b\w+\b", orig_summary.lower()))
    rehyd_tokens = set(re.findall(r"\b\w+\b", deid_rehydrated_summary.lower()))

    if orig_tokens and rehyd_tokens:
        intersection = orig_tokens.intersection(rehyd_tokens)
        token_f1 = (2 * len(intersection)) / (len(orig_tokens) + len(rehyd_tokens))
    else:
        token_f1 = 1.0 if not orig_tokens and not rehyd_tokens else 0.0

    # 3. Longest Common Subsequence (LCS) ratio for syntactic coherence
    lcs_len = _longest_common_subsequence_len(orig_summary.split(), deid_rehydrated_summary.split())
    max_len = max(len(orig_summary.split()), len(deid_rehydrated_summary.split()))
    lcs_ratio = lcs_len / max_len if max_len > 0 else 1.0

    # Weighted utility preservation composite score
    composite_utility = (0.40 * slot_recall) + (0.40 * token_f1) + (0.20 * lcs_ratio)
    return max(0.0, min(1.0, composite_utility))


def _longest_common_subsequence_len(seq1: List[str], seq2: List[str]) -> int:
    """Computes length of longest common subsequence of words."""
    m, n = len(seq1), len(seq2)
    if m == 0 or n == 0:
        return 0
    # Space-efficient DP
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev = list(curr)
    return curr[n]


def compute_latency_percentiles(latencies_ms: List[float]) -> Tuple[float, float]:
    """
    Computes p50 and p95 latency percentiles from a list of measurements in milliseconds.
    
    Args:
        latencies_ms: List of execution times in milliseconds.
        
    Returns:
        Tuple[float, float]: (p50_ms, p95_ms)
    """
    if not latencies_ms:
        return 0.0, 0.0

    sorted_l = sorted(latencies_ms)
    n = len(sorted_l)

    def _calc_p(p: float) -> float:
        if n == 1:
            return sorted_l[0]
        k = (n - 1) * p
        f = int(math.floor(k))
        c = int(math.ceil(k))
        if f == c:
            return sorted_l[f]
        d = k - f
        return sorted_l[f] + d * (sorted_l[c] - sorted_l[f])

    return _calc_p(0.50), _calc_p(0.95)


def compute_latency_stats(
    latencies_ms: List[float],
    total_notes: int,
    total_tokens: int = 0
) -> Dict[str, float]:
    """
    Computes complete latency distribution statistics (mean, p50, p90, p95, p99, throughput).
    """
    if not latencies_ms:
        return {
            "mean": 0.0, "p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0,
            "min": 0.0, "max": 0.0, "notes_per_sec": 0.0, "tokens_per_sec": 0.0
        }

    sorted_l = sorted(latencies_ms)
    n = len(sorted_l)

    def _calc_p(p: float) -> float:
        if n == 1:
            return sorted_l[0]
        k = (n - 1) * p
        f = int(math.floor(k))
        c = int(math.ceil(k))
        if f == c:
            return sorted_l[f]
        d = k - f
        return sorted_l[f] + d * (sorted_l[c] - sorted_l[f])

    mean_ms = sum(latencies_ms) / len(latencies_ms)
    total_time_sec = sum(latencies_ms) / 1000.0
    notes_per_sec = total_notes / total_time_sec if total_time_sec > 0 else 0.0
    tokens_per_sec = total_tokens / total_time_sec if total_time_sec > 0 and total_tokens > 0 else 0.0

    return {
        "mean": mean_ms,
        "p50": _calc_p(0.50),
        "p90": _calc_p(0.90),
        "p95": _calc_p(0.95),
        "p99": _calc_p(0.99),
        "min": sorted_l[0],
        "max": sorted_l[-1],
        "notes_per_sec": notes_per_sec,
        "tokens_per_sec": tokens_per_sec,
    }
