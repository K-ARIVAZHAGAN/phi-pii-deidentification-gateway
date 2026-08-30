# Project: HIPAA Safe Harbor PHI/PII De-Identification Gateway

## Architecture
A production-grade, HIPAA Safe Harbor de-identification and rehydration gateway service designed to strip Protected Health Information (PHI) and Personally Identifiable Information (PII) before text reaches foundation Large Language Models (LLMs), preserving clinical utility and restoring context upon response rehydration without data leakage.

### Architecture Overview
1. **Core De-Identification Engine (`deid_gateway.core`)**:
   - Multi-layer ensemble token classifier (<1B parameters, DeBERTa-v3/Bio_ClinicalBERT architecture + deterministic regex + medical gazetteers + contextual rules).
   - Consistent pseudonymisation (`[PATIENT_1]`, `[PROVIDER_1]`, `[HOSPITAL_1]`, `[DATE_1]`, etc.) with isolated mapping dict.
   - Deterministic relative date shifting preserving exact clinical time deltas ($\Delta t' = \Delta t$).
   - Age > 89 aggregation to `[AGE_90+]` per 45 CFR § 164.514(b)(2)(i)(C).
   - Clinical ambiguity & eponym disambiguation engine (tri-filter: honorifics, clinical context suffixes, UMLS/SNOMED CT whitelist) protecting medical concepts (e.g. *Parkinson's disease*, *Crohn's disease*, *Bell's palsy*, *Whipple procedure*) while masking provider/patient names.
   - Collision, hallucination, and corruption guards.
2. **Rehydration Engine (`deid_gateway.core.rehydrate`)**:
   - Inverses surrogate tokens in LLM responses safely, handling variations, bracket normalizations, and preventing hallucinated token injection.
3. **Pluggable Foundation LLM Gateway (`deid_gateway.adapters`)**:
   - `BaseLLMAdapter` interface with synchronous and asynchronous execution.
   - `MockLLMAdapter` for hermetic, deterministic offline clinical reasoning, summarization, QA, and slot extraction.
   - `OpenAIAdapter`, `AnthropicAdapter`, `GeminiAdapter` for production cloud LLM integrations.
   - End-to-end pipeline: `Raw Clinical Note -> deidentify -> Foundation LLM -> rehydrate`.
4. **Evaluation Harness & Baselines (`deid_gateway.benchmarks`)**:
   - Baseline 1: Regex-only de-identifier.
   - Baseline 2: Microsoft Presidio / spaCy NER baseline.
   - Core Gateway Model (<1B parameters).
   - Quantitative metrics: Precision, Recall, F1 (per category and overall, prioritizing recall), Document Leak Rate, Downstream Utility Preservation Delta, Latency p50/p95.
   - 55 held-out annotated synthetic clinical notes across 10 specialties and 9 adversarial challenge categories.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---|---|---|---|
| 1 | Safe Harbor 18-Category Detection | Detect all 18 HIPAA Safe Harbor categories (names, geos, dates, phone, fax, email, SSN, MRN, health plan, accounts, licenses, vehicles, devices, URLs, IPs, biometrics, photos, accession IDs) | M1 | ORIGINAL_REQUEST §R1 |
| 2 | Sub-1B Parameter Model | Lightweight sequence labeling / token classification model family (<1B parameters, ~86M-125M params) with exact parameter count breakdown | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Reversible Callable Python Interface | `deidentify(text) -> (masked_text, mapping)` and `rehydrate(response, mapping) -> text` | M1 | ORIGINAL_REQUEST §R1 |
| 4 | Consistent Pseudonymisation | Consistent surrogate tokens per document/patient (`[PATIENT_1]`, `[PROVIDER_1]`, `[DATE_1]`) with isolated session mapping | M1 | ORIGINAL_REQUEST §R1 |
| 5 | Deterministic Date Shifting | Consistent signed day offset preserving relative clinical intervals while shifting calendar anchors | M1 | ORIGINAL_REQUEST §R1 |
| 6 | Age > 89 Aggregation | Detection and aggregation of ages $\ge 90$ to `[AGE_90+]` / `90 or older` | M1 | ORIGINAL_REQUEST §R1 |
| 7 | Medical Eponym Disambiguation | Tri-filter context engine protecting disease/sign/procedure eponyms while masking provider/patient names | M1 | ORIGINAL_REQUEST §R1 |
| 8 | Collision & Hallucination Guard | Safeguards against LLM syntax modification, hallucinated tokens, and collision with existing bracketed text | M1 | ORIGINAL_REQUEST §R1 |
| 9 | Pluggable LLM Adapter Interface | `BaseLLMAdapter` abstract interface for multi-provider foundation model support | M2 | ORIGINAL_REQUEST §R2 |
| 10 | Hermetic Mock LLM Adapter | Offline deterministic mock LLM for summarization, QA, and clinical extraction without network dependencies | M2 | ORIGINAL_REQUEST §R2 |
| 11 | External Cloud LLM Adapters | Production adapters for OpenAI, Anthropic, and Gemini foundation LLMs | M2 | ORIGINAL_REQUEST §R2 |
| 12 | End-to-End Gateway Pipeline & API | Full round-trip pipeline with FastAPI REST API endpoints (`/deidentify`, `/rehydrate`, `/gateway/*`) | M2 | ORIGINAL_REQUEST §R2 |
| 13 | Standalone Runnable Demo Scripts | Interactive CLI and demo scripts showcasing round-trip de-id, LLM processing, and rehydration with 0 raw PHI leaked | M2 | ORIGINAL_REQUEST §R2 |
| 14 | Regex-Only Baseline | Rule-based regex baseline implementation for comparative benchmarking | M3 | ORIGINAL_REQUEST §R3 |
| 15 | Presidio / spaCy Baseline | Microsoft Presidio / spaCy NER baseline implementation for comparative benchmarking | M3 | ORIGINAL_REQUEST §R3 |
| 16 | Quantitative Metrics Engine | Entity Precision/Recall/F1 (per category and overall), Document Leak Rate, Utility Preservation Delta, Latency p50/p95 | M3 | ORIGINAL_REQUEST §R3 |
| 17 | 55-Note Adversarial Test Corpus | Held-out annotated synthetic clinical dataset with ground-truth spans, 10 specialties, and 9 adversarial axes | E2E | ORIGINAL_REQUEST §R3 |
| 18 | Automated Benchmark Runner CLI | CLI tool generating side-by-side comparison tables (Regex vs Presidio vs Core Gateway) in Rich/Markdown | M3 | ORIGINAL_REQUEST §R3 |
| 19 | E2E Test Suite (Tiers 1-4) | Comprehensive opaque-box test suite verifying all features, boundaries, combinations, and real-world clinical notes | E2E | Project Pattern |
| 20 | Adversarial Coverage Hardening (Tier 5) | White-box adversarial testing and gap analysis closing all untested execution paths | Final | Project Pattern |
| 21 | Architecture & Parameter Breakdown Docs | Complete technical documentation detailing architecture, data flow, and exact model parameter count | M4 | ORIGINAL_REQUEST §R4 |
| 22 | Live FAILURES.md Log | Incident log tracking technical hurdles, false-positive/negative edge cases, and architectural trade-offs | M4 | ORIGINAL_REQUEST §R4 |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| E2E | E2E Testing Track | Test harness, 55-note annotated corpus, Tiers 1-4 test suite, publishes `TEST_READY.md` | none | DONE |
| M1 | Core De-Identification & Rehydration Engine | 18 Safe Harbor categories, sub-1B model, pseudonymizer, date shifter, age > 89, eponym disambiguator, collision guards, `deidentify` / `rehydrate` API | none | DONE |
| M2 | Foundation LLM Gateway & Adapters | Pluggable adapters (`BaseLLMAdapter`, `MockLLMAdapter`, `OpenAIAdapter`, `AnthropicAdapter`, `GeminiAdapter`), pipeline, FastAPI server, demo scripts | M1 | DONE |
| M3 | Evaluation Harness & Baselines | Regex baseline, Presidio/spaCy baseline, quantitative metrics (P/R/F1, Leak Rate, Utility Delta, Latency p50/p95), benchmark runner CLI | M1 | DONE |
| Final | 100% E2E Pass & Adversarial Hardening | Phase 1: 100% E2E pass on Tiers 1-4. Phase 2: Tier 5 adversarial white-box challenger & hardening | E2E, M1, M2, M3 | DONE |
| M4 | Documentation, Failures Log & Packaging | Architecture overview, parameter count breakdown, reproduction guide, live `FAILURES.md`, forensic integrity audit | Final | DONE |

---

## Interface Contracts

### 1. Core De-Identification Interface
```python
def deidentify(text: str, config: Optional[DeidConfig] = None) -> tuple[str, dict]:
    """
    De-identifies text in accordance with HIPAA Safe Harbor.
    
    Args:
        text: Raw clinical text containing potential PHI/PII.
        config: Optional configuration (masking mode, date shift parameters, strictness).
        
    Returns:
        masked_text: De-identified text with consistent pseudonymised tokens.
        mapping: Isolated dictionary containing entity lookups, metadata, and date shift offset.
    """
```

### 2. Rehydration Interface
```python
def rehydrate(response: str, mapping: dict) -> str:
    """
    Rehydrates foundation LLM response using the session mapping dictionary.
    
    Args:
        response: LLM generated output containing surrogate tokens or references.
        mapping: The isolated dictionary produced by deidentify().
        
    Returns:
        text: Rehydrated response with original clinical entities restored.
    """
```

### 3. Pluggable Foundation LLM Adapter Interface
```python
class BaseLLMAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Synchronously generate a response from the foundation model."""
        pass

    @abstractmethod
    async def agenerate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Asynchronously generate a response from the foundation model."""
        pass
```

### 4. End-to-End Gateway Pipeline Interface
```python
class DeidGateway:
    def __init__(self, adapter: BaseLLMAdapter, deid_config: Optional[DeidConfig] = None):
        ...
        
    def process(self, clinical_note: str, task_prompt: str, **kwargs) -> GatewayResult:
        """
        Executes full roundtrip:
        1. (masked_text, mapping) = deidentify(clinical_note)
        2. raw_response = adapter.generate(f"{task_prompt}\n\n{masked_text}")
        3. final_response = rehydrate(raw_response, mapping)
        Returns GatewayResult(final_text=final_response, masked_input=masked_text, ...)
        """
```

---

## Code Layout
```
deid_gateway/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── deidentify.py
│   ├── rehydrate.py
│   ├── pseudonymizer.py
│   ├── date_shifter.py
│   ├── eponyms.py
│   ├── collision_guard.py
│   ├── config.py
│   └── models/
│       ├── __init__.py
│       ├── classifier.py
│       └── model_card.py
├── adapters/
│   ├── __init__.py
│   ├── base.py
│   ├── mock_adapter.py
│   ├── openai_adapter.py
│   ├── anthropic_adapter.py
│   └── gemini_adapter.py
├── gateway.py
├── api/
│   ├── __init__.py
│   ├── server.py
│   └── schemas.py
├── benchmarks/
│   ├── __init__.py
│   ├── baselines/
│   │   ├── __init__.py
│   │   ├── regex_baseline.py
│   │   └── presidio_baseline.py
│   ├── metrics.py
│   ├── evaluator.py
│   └── run_benchmarks.py
└── demo/
    ├── __init__.py
    ├── demo_roundtrip.py
    └── demo_cli.py

tests/
├── conftest.py
├── data/
│   └── annotated_clinical_notes_55.json
├── test_core_deid.py
├── test_date_shifter.py
├── test_eponyms.py
├── test_pseudonymizer.py
├── test_rehydration.py
├── test_adapters.py
├── test_gateway_pipeline.py
├── test_benchmarks.py
└── test_e2e_scenarios.py

docs/
├── ARCHITECTURE.md
├── MODEL_PARAMETER_BREAKDOWN.md
└── REPRODUCTION_GUIDE.md

FAILURES.md
```
