# Deliverable 2: Quantitative Benchmark & Evaluation Results

## 1. Executive Benchmark Summary

The Gateway was evaluated against two baseline architectures across a gold-standard dataset of **55 multi-specialty clinical notes** containing **732 hand-verified ground-truth entity spans** (`tests/data/annotated_clinical_notes_55.json`):

1. **Baseline 1 (Regex-Only)**: Standard regular expression de-identification.
2. **Baseline 2 (Microsoft Presidio / spaCy)**: Standard open-source NLP NER de-identification.
3. **Core Gateway Model (<1B)**: Our trained sub-1B transformer ensemble (`124,400,000` parameters).

---

## 2. Comparative Benchmark Matrix

| Metric | Baseline 1 (Regex-Only) | Baseline 2 (Presidio/spaCy) | Core Gateway Model (<1B) | Target / Tolerance |
|---|:---:|:---:|:---:|:---:|
| **Overall Recall (Breach Prevention)** | 57.8% | 51.4% | **100.0%** | $\ge$ 99.0% |
| **Overall Precision** | 75.3% | 78.2% | **53.3%** | $\ge$ 50.0% |
| **Overall $F_1$ Score** | 65.4% | 62.0% | **69.5%** | $\ge$ 65.0% |
| **$F_2$ Score (Recall-Weighted)** | 60.6% | 55.1% | **85.1%** | $\ge$ 80.0% |
| **Document Leak Rate (%)** | 100.0% | 100.0% | **0.0%** | **0.0%** |
| **Utility Preservation ($\Delta U$)** | 100.0% | 100.0% | **99.9%** | $\ge$ 98.0% |
| **p50 Latency (ms)** | 0.83 ms | 1.18 ms | **4.20 ms** *(Core)* / **363.5 ms** *(Deep Neural)* | $\le$ 50.0 ms (Core) |
| **Model Parameter Count** | 0 (Heuristic) | ~14M (spaCy/Presidio) | **124.4M (Sub-1B Ensemble)** | **< 1,000,000,000** |

*Full JSON telemetry data is stored in [`results/2_benchmark_results.json`](2_benchmark_results.json).*

---

## 3. Analysis & Key Insights

1. **Zero Document Leak Rate (0.0%)**:
   - Both Regex and Presidio failed to catch multi-specialty clinical narrative names, doctor initials, and non-standard identifiers, resulting in a **100% Document Leak Rate** (every single document had at least 1 leaked PHI identifier).
   - Our Core Gateway detected **732 out of 732 identifiers (100.0% Recall)** with **0 leaks**.
2. **Recall-Weighted Safety Posture ($F_2 = 85.1\%$)**:
   - Under HIPAA Safe Harbor, missed identifiers (False Negatives) carry severe legal and breach liabilities, while slight over-masking is clinically acceptable as long as context is preserved. The Core Gateway achieves an **$F_2$ score of 85.1%**, outperforming both baselines.
3. **Downstream Utility Preservation (99.9%)**:
   - Measured by comparing downstream clinical extraction and summarization on unmasked vs de-identified inputs using clinical cosine semantic similarity ($0.9993$). Medical diagnoses, ICD-10 indications, and dosages (*25/100 mg*) remained untouched.
