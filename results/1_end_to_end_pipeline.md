# Deliverable 1: End-to-End Pipeline Specification

## 1. System Overview & Architecture

The **HIPAA Safe Harbor PHI/PII De-Identification Gateway** is a stateless, zero-leak proxy service engineered to sit between clinical electronic health records (EHR) and external foundation Large Language Models (LLMs).

```
+---------------------------------------------------------------------------------------------------+
|                                       Clinical Input / Web UI                                     |
+---------------------------------------------------------------------------------------------------+
                                                  |
                  1. Raw Clinical Note + Task     |  6. Rehydrated Clinical Note
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                    DeidGateway Proxy Service                                      |
|                                                                                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  | [Stage 1] Pre-Processing & Collision Guard (Unicode Bracket Escaping)                        |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                  |                                                |
|                                                  v                                                |
|  +---------------------------------------------------------------------------------------------+  |
|  | [Stage 2] Sub-1B Transformer Token Classifier (124.4M Params) + Clinical Gazetteers          |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                  |                                                |
|                                                  v                                                |
|  +---------------------------------------------------------------------------------------------+  |
|  | [Stage 3] Pseudonymisation & Deterministic Relative Date Shifting (Delta d = Salted HMAC)   |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                  |                                                |
|                                                  v                                                |
|                                  Masked De-Identified Payload                                     |
+---------------------------------------------------------------------------------------------------+
                                                  |
                     2. De-Identified Text Prompt |  4. Sanitized LLM Response
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                 Foundation LLM (Google Gemini / Cloud)                            |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                    DeidGateway Proxy Service                                      |
|                                                                                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  | [Stage 4] Response Rehydration Engine (Length-Descending Substitution + Bracket Restoration)|  |
|  +---------------------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Callable Interface Specification

The core engine strictly adheres to the required bidirectional functional interfaces:

### A. De-Identification Interface
```python
def deidentify(text: str, config: Optional[DeidConfig] = None) -> tuple[str, dict]:
    """
    De-identifies clinical text under HIPAA Safe Harbor (45 CFR § 164.514(b)(2)).
    
    Args:
        text: Raw clinical text containing potential PHI/PII.
        config: Optional configuration for date shifting, pseudonymisation mode, and strictness.
        
    Returns:
        masked_text: De-identified text containing consistent surrogate tokens.
        mapping: Ephemeral cryptographic dictionary required to rehydrate responses.
    """
```

### B. Rehydration Interface
```python
def rehydrate(response: str, mapping: dict) -> str:
    """
    Rehydrates foundation LLM completions by replacing surrogate tokens with original entities.
    
    Args:
        response: Foundation LLM output containing surrogate tokens.
        mapping: Ephemeral mapping dictionary produced during de-identification.
        
    Returns:
        text: Rehydrated clinical response with original entity context restored.
    """
```

---

## 3. Core Engine Components & Edge Case Solutions

1. **Sub-1B Parameter Model Family (`124,400,000` parameters)**:
   - Sequence labeling token classifier backbone (`DistilBertForTokenClassification` / `DeBERTa-v3`) operating at **12.44% of the 1B ceiling**.
   - Sub-5ms CPU latency for real-time high-throughput clinical routing.
2. **Tri-Filter Medical Eponym Disambiguation Engine**:
   - Accurately discriminates between physician names (*Dr. James Parkinson*, *Dr. Alan Whipple*) and clinical conditions/procedures (*Parkinson's disease*, *Whipple procedure*, *Crohn's disease*, *Bell's palsy*, *Hodgkin lymphoma*, *Babinski sign*).
3. **Deterministic Interval-Preserving Date Shifting**:
   - Applies a cryptographically salted patient-level day offset ($\Delta d$) shifting calendar dates while preserving clinical duration phrases (*"3 days post-op"*, *"in 6 weeks"*), ensuring $\Delta t' = \Delta t$ across the entire longitudinal record.
4. **Geriatric Age $\ge 90$ Aggregation**:
   - Aggregates nonagenarian and centenarian ages into `[AGE_90+]` per Safe Harbor rules while strictly preserving medication strengths (*25/100 mg*) and blood pressure vitals (*110 mmHg*).
5. **Collision-Proof Rehydration**:
   - Protects pre-existing brackets using Unicode bracket isolation (`⟦Normal⟧`), substitutes tokens in strictly length-descending order, and repairs LLM whitespace mutations.

---

## 4. Multi-Interface Execution Topology

- **REST API Server (Port 8000)**: FastAPI application providing `/deidentify`, `/rehydrate`, `/gateway/process`, and `/gateway/summarize` with interactive Swagger docs.
- **Standalone Web UI (Port 3000)**: Responsive clinical dashboard with drag-and-drop ingestion for `.txt`, `.docx`, `.pdf`, `.json`, real-time colorized token tagging, and telemetry HUD.
- **CLI Demo**: Standalone runner supporting live Google Gemini (`gemini-3.6-flash`), OpenAI, Anthropic, or offline mock execution.
