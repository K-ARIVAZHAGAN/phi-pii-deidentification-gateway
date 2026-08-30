# E2E Test Infra: HIPAA Safe Harbor PHI/PII De-Identification Gateway

## Test Philosophy
- Opaque-box, requirement-driven, testing against public API and CLI entry points.
- Zero-leak policy: Any unmasked PHI in de-identified output is a critical failure.
- Downstream clinical integrity: Eponyms, relative time intervals, and normal clinical terms must never be corrupted.
- Methodology: Category-Partition + Boundary Value Analysis (BVA) + Pairwise Combinatorial Testing + 55-Note Real-World Clinical Scenarios.

---

## Feature Inventory & Test Mapping
| # | Feature | Source (Requirement) | Tier 1 (Feature Coverage) | Tier 2 (Boundary & Corner) | Tier 3 (Cross-Feature) | Tier 4 (Real-World) |
|---|---|---|:---:|:---:|:---:|:---:|
| 1 | 18 HIPAA Safe Harbor Categories | ORIGINAL_REQUEST §R1 | 5 per category (90) | 5 per category (90) | ✓ | ✓ |
| 2 | Model Parameter Count < 1B | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 3 | Callable Python API (`deidentify`/`rehydrate`) | ORIGINAL_REQUEST §R1 | 10 | 10 | ✓ | ✓ |
| 4 | Consistent Pseudonymisation | ORIGINAL_REQUEST §R1 | 8 | 8 | ✓ | ✓ |
| 5 | Deterministic Relative Date Shifting | ORIGINAL_REQUEST §R1 | 10 | 10 | ✓ | ✓ |
| 6 | Age > 89 Aggregation (`[AGE_90+]`) | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 7 | Medical Eponym Disambiguation | ORIGINAL_REQUEST §R1 | 10 | 10 | ✓ | ✓ |
| 8 | Collision & Hallucination Guard | ORIGINAL_REQUEST §R1 | 8 | 8 | ✓ | ✓ |
| 9 | Pluggable LLM Adapter Interface | ORIGINAL_REQUEST §R2 | 6 | 6 | ✓ | ✓ |
| 10 | Hermetic Mock LLM Adapter | ORIGINAL_REQUEST §R2 | 8 | 8 | ✓ | ✓ |
| 11 | Cloud LLM Adapters (OpenAI/Anthropic/Gemini) | ORIGINAL_REQUEST §R2 | 6 | 6 | ✓ | ✓ |
| 12 | End-to-End Gateway Pipeline | ORIGINAL_REQUEST §R2 | 8 | 8 | ✓ | ✓ |
| 13 | Demo Scripts & CLI Execution | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 14 | Regex-Only Baseline | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |
| 15 | Presidio / spaCy Baseline | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |
| 16 | Quantitative Metrics Calculation | ORIGINAL_REQUEST §R3 | 10 | 10 | ✓ | ✓ |
| 17 | 55-Note Held-Out Annotated Corpus | ORIGINAL_REQUEST §R3 | 55 | 55 | ✓ | ✓ |
| 18 | Benchmark Runner Reporting | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |

---

## Test Architecture
- **Framework**: `pytest` test runner.
- **Annotated Test Dataset**: `tests/data/annotated_clinical_notes_55.json` containing 55 detailed clinical notes across 10 medical specialties (Oncology, Cardiology, Neurology, Pediatrics, Geriatrics, Psychiatry, Orthopedics, Gastroenterology, Telehealth, Emergency Medicine) with ground-truth entity spans, categories, and expected masked outputs.
- **Benchmark Suite**: `python -m deid_gateway.benchmarks.run_benchmarks` computing:
  - Token-level and entity-level Precision, Recall, F1, F2 score.
  - Document Leak Rate (% notes with >=1 unmasked PHI).
  - Downstream Utility Preservation Delta.
  - Latency p50 and p95.

---

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Clinical Specialty | Adversarial Challenge |
|---|---|---|---|---|
| 1 | Note 01-05: Eponym-Heavy Oncology Notes | F1, F3, F4, F7, F8, F10, F12 | Oncology | Hodgkin vs Dr. Hodgkin, Whipple procedure vs Dr. Whipple |
| 2 | Note 06-10: Geriatric & Nonagenarian Inpatient Notes | F1, F3, F5, F6, F8, F10, F12 | Geriatrics | Age 92/97/104 aggregation, multi-date shifting |
| 3 | Note 11-15: Pediatric Multi-Family Member Notes | F1, F3, F4, F8, F10, F12 | Pediatrics | Mother/father/guardian/child names, school locations |
| 4 | Note 16-20: Cardiology Device & Implant Notes | F1, F3, F8, F10, F12 | Cardiology | Pacemaker serials, catheter models, telemetry IPs |
| 5 | Note 21-25: Neurology Movement Disorder Consult | F1, F3, F7, F8, F10, F12 | Neurology | Parkinson's disease vs Dr. Parkinson, Huntington |
| 6 | Note 26-30: Telehealth Logs with Network & URL Metadata | F1, F3, F8, F10, F12 | Telemedicine | Zoom/portal URLs, IPv4/IPv6, dial-in pins |
| 7 | Note 31-35: Orthopedic Surgery Operative Records | F1, F3, F5, F7, F8, F10, F12 | Orthopedics | Post-op interval preservation, implant lot # |
| 8 | Note 36-40: Gastroenterology Endoscopy Reports | F1, F3, F7, F8, F10, F12 | Gastroenterology | Crohn's disease, Barrett's esophagus |
| 9 | Note 41-45: Psychiatric Inpatient Intake & Legal Holds | F1, F3, F4, F8, F10, F12 | Psychiatry | Police report #, courtroom dates, emergency contacts |
| 10 | Note 46-50: Emergency Department Trauma Resuscitation | F1, F3, F4, F5, F8, F10, F12 | Emergency Medicine | Rapid timestamps, trauma surgeon names, triage vitals |
| 11 | Note 51-55: Complex Pathology & Clinical Trials | F1, F3, F4, F8, F10, F12 | Pathology/Research | Accession IDs, trial subject IDs, genetic markers |

---

## Coverage Thresholds
- Tier 1: Feature Coverage (>=5 tests per feature)
- Tier 2: Boundary & Corner Cases (>=5 tests per feature)
- Tier 3: Pairwise Combinations of major feature interactions
- Tier 4: 55 held-out annotated synthetic clinical notes
- Target: 100% test pass rate with 0 unmasked PHI leaks on the evaluation corpus.
