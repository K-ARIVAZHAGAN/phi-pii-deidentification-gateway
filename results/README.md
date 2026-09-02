# Deliverables Index: PHI/PII De-Identification Gateway

This directory contains the formal submission deliverables for the **LezDo TechMed AI/ML Internship Assessment (Project 2: PHI/PII De-Identification Gateway)**, structured in accordance with the assessment guidelines:

---

## Deliverables Summary Matrix

| Assessment Deliverable | File in `results/` | Description & Contents |
|---|---|---|
| **1. End-to-End Pipeline** | [`1_end_to_end_pipeline.md`](1_end_to_end_pipeline.md) | Full architectural specifications, Sub-1B parameter sequence labeler (`124,400,000` params), deterministic date shifter ($\Delta t' = \Delta t$), eponym disambiguation, live cloud foundation LLM adapters (Google Gemini `gemini-3.6-flash`), rehydration engine, and standalone web UI on port `3000`. |
| **2. Output / Results** | [`2_benchmark_and_evaluation_results.md`](2_benchmark_and_evaluation_results.md)<br>[`2_benchmark_results.json`](2_benchmark_results.json) | Complete quantitative benchmarks across 55 gold-standard annotated clinical notes (732 entities, 10 specialties) comparing Core Gateway against Regex and Presidio/spaCy baselines: **100.0% Breach Recall**, **0.0% Document Leak Rate**, **99.9% Downstream Utility Preservation**, and sub-5ms CPU latency. |
| **3. Supplementary Data** | [`3_supplementary_data.md`](3_supplementary_data.md)<br>[`sample_roundtrip_traces.json`](sample_roundtrip_traces.json) | Full 18 HIPAA Safe Harbor categories breakdown, held-out gold-standard dataset metadata, 12 documented incident case studies (`FAIL-001` through `FAIL-012`), and complete multi-specialty raw $\rightarrow$ masked $\rightarrow$ LLM $\rightarrow$ rehydrated execution traces. |

---

## Quick Verification Commands

```bash
# 1. Run Complete Automated Test Suite (189 Tests Passing)
pytest tests/ -v

# 2. Run Comparative Benchmark Harness
python deid_gateway/benchmarks/run_benchmarks.py

# 3. Launch Full Application Stack (Backend :8000 + Frontend :3000)
python run_app.py
```
