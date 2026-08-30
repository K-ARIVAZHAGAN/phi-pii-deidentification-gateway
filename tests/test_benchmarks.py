"""
Tests for Benchmark Harness, Baselines, and Quantitative Metrics (Tiers 1, 2, & 3).
Verifies:
- Baseline 1: Regex-only de-identifier.
- Baseline 2: Presidio / spaCy NER baseline.
- Metric calculations: Entity-level Precision, Recall, F1, F2 (prioritizing recall).
- Document Leak Rate calculation (% notes with >= 1 missed PHI).
- Downstream Clinical Utility Preservation Delta.
- Latency profiling (p50 and p95 percentiles).
- Benchmark runner execution and Markdown table formatting.
"""

import pytest
from typing import Dict, List, Any

try:
    from deid_gateway.benchmarks.baselines.regex_baseline import RegexDeidBaseline
    from deid_gateway.benchmarks.baselines.presidio_baseline import PresidioDeidBaseline
    from deid_gateway.benchmarks.metrics import (
        compute_deid_metrics,
        compute_document_leak_rate,
        compute_utility_preservation,
        compute_latency_percentiles,
        BenchmarkMetrics
    )
    from deid_gateway.benchmarks.evaluator import BenchmarkEvaluator
except ImportError:
    RegexDeidBaseline = None
    PresidioDeidBaseline = None
    compute_deid_metrics = None
    compute_document_leak_rate = None
    compute_utility_preservation = None
    compute_latency_percentiles = None
    BenchmarkMetrics = None
    BenchmarkEvaluator = None


# =============================================================================
# TIER 1: FEATURE COVERAGE - BASELINE DE-IDENTIFIERS
# =============================================================================

class TestBaselineDeidentifiers:
    """Tier 1: Tests Regex and Presidio baseline models."""

    def test_regex_baseline_deidentification(self, sample_clinical_note: str):
        """Verifies Regex baseline detects standard formatted entities (SSN, Phone, MRN, Dates)."""
        if RegexDeidBaseline is None:
            pytest.skip("RegexDeidBaseline implementation pending")

        baseline = RegexDeidBaseline()
        masked_text, mapping = baseline.deidentify(sample_clinical_note)

        # Regex baseline should catch structured entities
        assert "078-45-9921" not in masked_text  # SSN
        assert "617-555-0144" not in masked_text  # Phone
        assert "884-9102-X" not in masked_text   # MRN

    def test_presidio_baseline_deidentification(self, sample_clinical_note: str):
        """Verifies Presidio / spaCy NER baseline handles entity extraction."""
        if PresidioDeidBaseline is None:
            pytest.skip("PresidioDeidBaseline implementation pending")

        baseline = PresidioDeidBaseline()
        masked_text, mapping = baseline.deidentify(sample_clinical_note)
        assert isinstance(masked_text, str)
        assert isinstance(mapping, dict)


# =============================================================================
# TIER 1 & 2: QUANTITATIVE METRICS ENGINE
# =============================================================================

class TestMetricsCalculationEngine:
    """Tier 1 & 2: Tests entity precision/recall/F1, leak rate, utility, and latency."""

    def test_perfect_precision_and_recall_metric_calculation(self):
        """Mathematical verification: 100% TP with 0 FP and 0 FN yields P=1.0, R=1.0, F1=1.0."""
        if compute_deid_metrics is None:
            pytest.skip("compute_deid_metrics implementation pending")

        # Ground truth spans and predicted spans exactly match
        ground_truth = [{"start": 10, "end": 20, "category": "PATIENT"}]
        predictions = [{"start": 10, "end": 20, "category": "PATIENT"}]

        metrics = compute_deid_metrics([ground_truth], [predictions])

        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.f1 == 1.0
        assert metrics.f2 == 1.0

    def test_imperfect_recall_and_false_negatives(self):
        """Mathematical verification: 2 ground truth entities, 1 detected -> Recall = 0.5."""
        if compute_deid_metrics is None:
            pytest.skip("compute_deid_metrics implementation pending")

        ground_truth = [
            {"start": 10, "end": 20, "category": "PATIENT"},
            {"start": 30, "end": 40, "category": "SSN"}
        ]
        predictions = [
            {"start": 10, "end": 20, "category": "PATIENT"}
        ]

        metrics = compute_deid_metrics([ground_truth], [predictions])

        assert metrics.recall == 0.5
        assert metrics.precision == 1.0
        assert metrics.false_negatives == 1
        assert metrics.true_positives == 1

    def test_document_leak_rate_calculation(self):
        """
        Document Leak Rate = (Number of notes with >= 1 missed PHI) / Total Notes.
        If Note 1 has 0 leaks, Note 2 has 1 leak -> Leak Rate = 50.0%.
        """
        if compute_document_leak_rate is None:
            pytest.skip("compute_document_leak_rate implementation pending")

        # Doc 1: Perfect (0 missed)
        # Doc 2: 1 missed entity
        ground_truths = [
            [{"start": 0, "end": 5, "text": "Alice"}],
            [{"start": 0, "end": 3, "text": "Bob"}]
        ]
        masked_docs = [
            "[PATIENT_1] arrived.",  # Alice masked
            "Bob arrived."           # Bob unmasked (LEAK!)
        ]

        leak_rate = compute_document_leak_rate(ground_truths, masked_docs)
        assert leak_rate == 50.0, f"Expected 50.0% leak rate, got {leak_rate}%"

    def test_latency_p50_p95_percentiles_calculation(self):
        """Verifies p50 and p95 percentile latency calculation across timing distributions."""
        if compute_latency_percentiles is None:
            pytest.skip("compute_latency_percentiles implementation pending")

        latencies = [10.0, 12.0, 15.0, 18.0, 20.0, 22.0, 25.0, 30.0, 45.0, 100.0]
        p50, p95 = compute_latency_percentiles(latencies)

        assert 15.0 <= p50 <= 25.0
        assert p95 > p50
        assert p95 >= 45.0

    def test_utility_preservation_delta(self):
        """Verifies semantic similarity / clinical slot retention scoring between original and de-id notes."""
        if compute_utility_preservation is None:
            pytest.skip("compute_utility_preservation implementation pending")

        orig_summary = "Patient diagnosed with Parkinson's disease. Started on carbidopa-levodopa."
        deid_rehydrated_summary = "Patient diagnosed with Parkinson's disease. Started on carbidopa-levodopa."

        score = compute_utility_preservation(orig_summary, deid_rehydrated_summary)
        assert score >= 0.99, f"Expected near 1.0 utility score, got {score}"


# =============================================================================
# TIER 3: BENCHMARK EVALUATOR & REPORTING
# =============================================================================

class TestBenchmarkEvaluatorRunner:
    """Tier 3: Evaluator comparing Regex vs Presidio vs Core Gateway."""

    def test_benchmark_evaluator_generates_comparison_table(self, annotated_notes_55: list):
        """Verifies evaluator produces comparative metrics across baselines on evaluation corpus."""
        if BenchmarkEvaluator is None:
            pytest.skip("BenchmarkEvaluator implementation pending")

        evaluator = BenchmarkEvaluator()
        # Run on subset of 5 notes for fast test execution
        report = evaluator.evaluate(annotated_notes_55[:5])

        assert "regex" in report
        assert "core_gateway" in report
        assert "presidio" in report
        assert report["core_gateway"]["recall"] >= 0.95 or report["core_gateway"]["leak_rate"] <= 40.0

        # Markdown rendering check
        md_table = evaluator.render_comparison_markdown(report)
        assert "| Metric | Baseline 1 (Regex-Only)" in md_table
        assert "Overall Recall (Breach Prevention)" in md_table
        assert "Core Gateway Model (<1B)" in md_table

    def test_exact_vs_overlap_matching_regimes(self):
        """Verifies strict span matching vs relaxed overlap matching."""
        if compute_deid_metrics is None:
            pytest.skip("compute_deid_metrics implementation pending")

        # Overlapping but not identical span
        ground_truth = [[{"start": 10, "end": 25, "category": "NAME_PATIENT"}]]
        predictions = [[{"start": 10, "end": 20, "category": "NAME_PATIENT"}]]

        overlap_metrics = compute_deid_metrics(ground_truth, predictions, match_mode="overlap")
        assert overlap_metrics.recall == 1.0
        assert overlap_metrics.true_positives == 1

        exact_metrics = compute_deid_metrics(ground_truth, predictions, match_mode="exact")
        assert exact_metrics.recall == 0.0
        assert exact_metrics.true_positives == 0
        assert exact_metrics.false_negatives == 1

    def test_f2_breach_prevention_weighting(self):
        """
        Verifies F2 score prioritization:
        If Precision = 0.5 and Recall = 1.0:
        F1 = 2 * (0.5 * 1.0) / (0.5 + 1.0) = 0.667
        F2 = 5 * (0.5 * 1.0) / (4 * 0.5 + 1.0) = 5 * 0.5 / 3.0 = 0.833 (higher than F1)
        """
        if compute_deid_metrics is None:
            pytest.skip("compute_deid_metrics implementation pending")

        # 1 TP (GT matched), 1 FP (extra prediction) -> P=0.5, R=1.0
        ground_truth = [[{"start": 10, "end": 20, "category": "DATE"}]]
        predictions = [
            [
                {"start": 10, "end": 20, "category": "DATE"},
                {"start": 50, "end": 60, "category": "DATE"},
            ]
        ]

        metrics = compute_deid_metrics(ground_truth, predictions)
        assert metrics.precision == 0.5
        assert metrics.recall == 1.0
        assert metrics.f2 > metrics.f1
        assert abs(metrics.f2 - 0.8333) < 0.01

    def test_empty_and_zero_division_safety(self):
        """Verifies metric computation handles empty inputs without ZeroDivisionError."""
        if compute_deid_metrics is None:
            pytest.skip("compute_deid_metrics implementation pending")

        empty_metrics = compute_deid_metrics([], [])
        assert empty_metrics.precision == 1.0
        assert empty_metrics.recall == 1.0
        assert empty_metrics.f1 == 1.0

        p50, p95 = compute_latency_percentiles([])
        assert p50 == 0.0
        assert p95 == 0.0

        leak_rate = compute_document_leak_rate([], [])
        assert leak_rate == 0.0

        utility = compute_utility_preservation("", "")
        assert utility == 1.0
