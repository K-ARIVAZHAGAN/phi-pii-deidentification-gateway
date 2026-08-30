"""
HIPAA Safe Harbor De-Identification Evaluation Harness & Benchmark Suite.
Exports:
- BenchmarkEvaluator
- BenchmarkMetrics
- compute_deid_metrics
- compute_document_leak_rate
- compute_utility_preservation
- compute_latency_percentiles
- compute_latency_stats
- RegexDeidBaseline
- PresidioDeidBaseline
"""

from deid_gateway.benchmarks.baselines.presidio_baseline import (
    PresidioBaselineDeidentifier,
    PresidioDeidBaseline,
)
from deid_gateway.benchmarks.baselines.regex_baseline import (
    RegexBaselineDeidentifier,
    RegexDeidBaseline,
)
from deid_gateway.benchmarks.evaluator import BenchmarkEvaluator
from deid_gateway.benchmarks.metrics import (
    BenchmarkMetrics,
    compute_deid_metrics,
    compute_document_leak_rate,
    compute_latency_percentiles,
    compute_latency_stats,
    compute_utility_preservation,
)

__all__ = [
    "BenchmarkEvaluator",
    "BenchmarkMetrics",
    "compute_deid_metrics",
    "compute_document_leak_rate",
    "compute_utility_preservation",
    "compute_latency_percentiles",
    "compute_latency_stats",
    "RegexDeidBaseline",
    "RegexBaselineDeidentifier",
    "PresidioDeidBaseline",
    "PresidioBaselineDeidentifier",
]
