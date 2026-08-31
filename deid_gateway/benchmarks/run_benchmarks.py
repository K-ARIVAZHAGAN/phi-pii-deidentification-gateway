"""
CLI Benchmark Runner for PHI/PII De-Identification Gateway.
Usage:
    python -m deid_gateway.benchmarks.run_benchmarks --dataset tests/data/annotated_clinical_notes_55.json --render-markdown
"""

import argparse
import json
import os
import sys

# Ensure repository root is in sys.path for direct script execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from deid_gateway.benchmarks.evaluator import BenchmarkEvaluator


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="Run automated comparative benchmarks for PHI/PII De-Identification Gateway."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="tests/data/annotated_clinical_notes_55.json",
        help="Path to annotated clinical notes dataset JSON file (default: tests/data/annotated_clinical_notes_55.json)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/benchmark_results.json",
        help="Path to save benchmark results JSON (default: reports/benchmark_results.json)",
    )
    parser.add_argument(
        "--render-markdown",
        action="store_true",
        help="Render and print Markdown comparison table to stdout.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of latency timing iterations per note (default: 1)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed per-category metrics breakdown.",
    )

    args = parser.parse_args()

    print("\n[BENCHMARK] Starting PHI/PII De-Identification Benchmark Suite...")
    print(f"[DATASET] Dataset: {args.dataset}")
    print(f"[TIMING] Latency Iterations: {args.iterations}")

    evaluator = BenchmarkEvaluator()
    try:
        results = evaluator.evaluate(dataset=args.dataset, iterations=args.iterations)
    except Exception as e:
        print(f"\n[ERROR] Benchmark execution failed: {e}", file=sys.stderr)
        sys.exit(1)

    # 1. Render Rich / Terminal Table
    evaluator.render_rich_table(results)

    # 2. Render Markdown Table if requested
    if args.render_markdown:
        md_table = evaluator.render_comparison_markdown(results)
        print("\n--- Markdown Output ---")
        print(md_table)
        print("-----------------------\n")

    # 3. Print Verbose Per-Category Breakdown if requested
    if args.verbose:
        print("\n[METRICS] Per-Category Detailed Breakdown (Core Gateway Model):")
        core_cat = results.get("core_gateway", {}).get("per_category", {})
        for cat, metrics in sorted(core_cat.items()):
            print(f"  * {cat:22s} | P: {metrics['precision']*100:5.1f}% | R: {metrics['recall']*100:5.1f}% | F1: {metrics['f1']*100:5.1f}% | TP: {metrics['tp']:2d} | FN: {metrics['fn']:2d}")

    # 4. Save JSON Benchmark Artifact
    if args.output:
        out_dir = os.path.dirname(args.output)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"[SAVED] Benchmark results saved to: {args.output}\n")


if __name__ == "__main__":
    main()
