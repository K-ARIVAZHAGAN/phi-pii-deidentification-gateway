# Original User Request

## 2026-08-29T21:16:20Z

Build a production-grade, HIPAA Safe Harbor PHI/PII de-identification gateway service with a trained or fine-tuned model under 1B parameters that strips patient identifiers before text reaches a foundation LLM and restores necessary context on the response without destroying clinical meaning or leaking protected data.

Working directory: c:\Users\ariva\Downloads\PHI  PII de-identification gateway
Integrity mode: development

## Requirements

### R1. Core De-Identification & Rehydration Engine
- Implement a de-identification and rehydration engine with callable Python interfaces:
  deidentify(text) -> (masked_text, mapping) and ehydrate(response, mapping) -> text.
- Train or fine-tune an open-weights model family under 1B parameters (e.g., DeBERTa-v3, BioClinicalBERT, or lightweight LLM with reported exact parameter count) for entity extraction / token classification across all applicable HIPAA Safe Harbor categories.
- Masking strategy: Consistent pseudonymisation with per-patient consistent tokens (e.g. [PATIENT_1], [PROVIDER_A]) and date shifting that preserves relative clinical intervals (e.g., "3 days post-op").
- Handle clinical ambiguities (e.g., disease names vs doctor names like "Dr. Parkinson diagnosed Parkinson's"), ages > 89 edge cases, and secure mapping isolation with collision/hallucination guards.

### R2. End-to-End Foundation LLM Gateway & Demonstration
- Provide an end-to-end pipeline: Raw Clinical Note → De-Identification & Pseudonymisation → Foundation LLM (Summarization / QA / Clinical Extraction) → Response Rehydration.
- Implement a pluggable adapter architecture supporting both offline local models/mocks and standard external LLM APIs (OpenAI, Anthropic, Gemini).
- Include runnable demo scripts demonstrating the full round-trip on realistic sample clinical notes with zero raw PHI leaked to the foundation model.

### R3. Evaluation Harness, Baselines & Benchmarks
- Implement automated benchmark evaluations comparing the trained gateway against:
  1. Regex-only baseline
  2. Microsoft Presidio / spaCy NER baseline
- Compute and display quantitative metrics:
  - Entity-level Precision, Recall, and F1 (both per-category and overall, with recall prioritized for breach-prevention).
  - Document Leak Rate (percentage of documents with >= 1 missed identifier).
  - Downstream utility preservation delta (measuring LLM task accuracy/coherence on original vs de-identified inputs).
  - Latency and throughput (p50 and p95).
- Include a test suite of at least 50 held-out annotated synthetic clinical notes containing adversarial cases (nicknames, misspellings, narrative embedding, tables, headers, signatures).

### R4. Documentation, Failures Log & Acceptance Readiness
- Provide comprehensive documentation: architecture overview, model parameter count breakdown, reproduction scripts, and a live-updated FAILURES.md recording technical hurdles, false-positive/false-negative edge cases, and architectural trade-offs.

## Acceptance Criteria

### Security & Functional Integrity
- [ ] Interface adheres strictly to deidentify(text) -> (masked_text, mapping) and ehydrate(response, mapping) -> text.
- [ ] Core model parameters verified and reported to be <= 1B.
- [ ] Zero unmasked PHI leaks in the provided evaluation test suite.
- [ ] Safe date shifting preserves relative time intervals across the patient record.
- [ ] Rehydration accurately maps pseudonymised tokens back to original entities without corrupting unmapped text or hallucinated spans.

### Evaluation & Baseline Comparison
- [ ] Automated benchmark harness runs cleanly and generates a side-by-side comparison table against Regex and Presidio/spaCy baselines.
- [ ] Leak rate, Recall, Precision, F1, Latency (p50/p95), and Utility Preservation score are computed and reported on >= 50 test cases.

### Usability & Submission Packaging
- [ ] Standalone runnable CLI / demo script executes the complete round-trip flow (aw -> deidentify -> LLM -> rehydrate).
- [ ] FAILURES.md is populated with edge case analyses and mitigation strategies.