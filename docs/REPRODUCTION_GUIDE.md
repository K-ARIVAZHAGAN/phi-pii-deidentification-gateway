# Reproduction & Verification Guide: PHI/PII De-Identification Gateway

## 1. Prerequisites & Environment Setup

### 1.1 System Requirements
- **Python**: Version 3.10, 3.11, or 3.12 (Tested on Python 3.12.3 Windows & Linux x86_64).
- **RAM**: Minimum 2 GB (4 GB recommended).
- **GPU**: Optional (CPU inference latency is sub-5ms).
- **Dependencies**: Listed in `requirements.txt` (FastAPI, Uvicorn, Pytest, Pydantic, Requests).

### 1.2 Installation
Clone or navigate to the repository directory and install dependencies:

```bash
# Navigate to workspace
cd "c:\Users\ariva\Downloads\PHI  PII de-identification gateway"

# Install dependencies
pip install -e .
# or
pip install fastapi uvicorn pydantic pytest requests
```

---

## 2. Running Automated Tests

The test suite contains **167 comprehensive unit, boundary, integration, and scenario tests** across 4 verification tiers.

### 2.1 Run Complete Test Suite
```bash
python -m pytest tests/ -v
```
*Expected Output*: `167 passed in ~2.3s` with exit code 0.

### 2.2 Run Tests by Verification Tier

```bash
# Tier 1 & Tier 2: Core De-Identification, Pseudonymisation, Date Shifting, Eponyms, and Rehydration
python -m pytest tests/test_core_deid.py tests/test_pseudonymizer.py tests/test_date_shifter.py tests/test_eponyms.py tests/test_rehydration.py tests/test_adapters.py -v

# Tier 3: Gateway Pipeline, LLM Adapters, and Benchmark Engine Integration
python -m pytest tests/test_gateway_pipeline.py tests/test_benchmarks.py -v

# Tier 4: Real-World 55-Note E2E Scenarios (Zero PHI Leak & Eponym Invariance)
python -m pytest tests/test_e2e_scenarios.py -v
```

---

## 3. Running the Comparative Benchmark Harness

The benchmark runner evaluates the Core Gateway Model against Baseline 1 (Regex-Only) and Baseline 2 (Microsoft Presidio/spaCy) across the 55 gold-standard annotated clinical notes.

### 3.1 Execute Benchmark CLI
```bash
python -m deid_gateway.benchmarks.run_benchmarks --dataset tests/data/annotated_clinical_notes_55.json --render-markdown --output reports/benchmark_results.json
```

### 3.2 Expected Benchmark Matrix Output
```
# Automated De-Identification Benchmark Comparison Matrix

| Metric | Baseline 1 (Regex-Only) | Baseline 2 (Presidio/spaCy) | Core Gateway Model (<1B) | Target / Tolerance |
|---|---|---|---|---|
| **Overall Recall (Breach Prevention)** | 57.8% | 51.4% | **100.0%** | $\ge$ 99.0% |
| **Overall Precision** | 75.3% | 78.2% | **66.8%** | $\ge$ 65.0% |
| **Overall $F_1$ Score** | 65.4% | 62.0% | **80.1%** | $\ge$ 80.0% |
| **$F_2$ Score (Recall-Weighted)** | 60.6% | 55.1% | **91.0%** | $\ge$ 90.0% |
| **Document Leak Rate (%)** | 100.0% | 100.0% | **0.0%** | **0.0%** |
| **Utility Preservation ($\Delta U$)** | 100.0% | 100.0% | **99.5%** | $\ge$ 98.0% |
| **p50 Latency (ms)** | 1.08 ms | 1.34 ms | **4.78 ms** | $\le$ 50.0 ms |
| **p95 Latency (ms)** | 1.77 ms | 2.30 ms | **7.03 ms** | $\le$ 100.0 ms |
| **Model Parameter Count** | 0 (Heuristic) | ~14M (spaCy/Presidio) | **124.4M (DeBERTa-v3/Ensemble)** | **< 1,000,000,000** |
```

---

## 4. Running the Interactive Demo & CLI

### 4.1 Standalone Multi-Specialty Demo
Run the end-to-end clinical round-trip demonstration across Cardiology, Surgical Oncology, and Geriatric Nonagenarian scenarios:

```bash
python demo.py
```
This script demonstrates:
1. Raw clinical note input.
2. Safe Harbor de-identification & surrogate token generation.
3. Foundation LLM generation (summarization / QA) with zero raw PHI exposed.
4. Response rehydration restoring original entity context.
5. Timing telemetry and latency breakdown.

### 4.2 Interactive CLI
Launch the interactive command-line gateway interface:

```bash
python -m deid_gateway.demo.demo_cli --interactive
```
Or process a specific clinical note file:

```bash
python -m deid_gateway.demo.demo_cli --input-file tests/data/sample_note.txt --task summarize
```

---

## 5. Starting the FastAPI REST Gateway Server

### 5.1 Launch the Gateway Server
```bash
python -m uvicorn deid_gateway.api.server:app --host 0.0.0.0 --port 8000 --reload
```

### 5.2 Server Endpoints Reference

| HTTP Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service health status and loaded model specifications. |
| `POST` | `/deidentify` | De-identifies raw clinical text; returns masked text and session mapping dict. |
| `POST` | `/rehydrate` | Rehydrates LLM response using the session mapping dictionary. |
| `POST` | `/gateway/process` | End-to-end pipeline: de-identifies, queries foundation LLM, and rehydrates response. |
| `POST` | `/gateway/summarize` | Clinical discharge summarization with automatic PHI masking and rehydration. |
| `POST` | `/gateway/qa` | Clinical question-answering with automatic PHI masking and rehydration. |

### 5.3 Example cURL Invocations

#### 1. Check Health & Model Info
```bash
curl -X GET http://localhost:8000/health
```

#### 2. De-Identify Clinical Note
```bash
curl -X POST http://localhost:8000/deidentify \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Dr. Sarah Jenkins examined patient Eleanor Vance (MRN: 8849201) on 10/14/2025 at Johns Hopkins Hospital."
  }'
```

#### 3. Rehydrate LLM Response
```bash
curl -X POST http://localhost:8000/rehydrate \
  -H "Content-Type: application/json" \
  -d '{
    "response": "Patient [PATIENT_1] was evaluated by [PROVIDER_1] at [HOSPITAL_1].",
    "mapping": {
      "token_to_original": {
        "[PATIENT_1]": "Eleanor Vance",
        "[PROVIDER_1]": "Dr. Sarah Jenkins",
        "[HOSPITAL_1]": "Johns Hopkins Hospital"
      }
    }
  }'
```

#### 4. Full Round-Trip Gateway Request
```bash
curl -X POST http://localhost:8000/gateway/process \
  -H "Content-Type: application/json" \
  -d '{
    "clinical_note": "Patient: Arthur Pendelton (DOB: 04/12/1954). Attending: Dr. Alan Whipple. Diagnosis: Whipple procedure for pancreatic mass. Follow up on 11/04/2025.",
    "task_prompt": "Provide a 2-sentence clinical summary of the patient diagnosis and plan.",
    "adapter": "mock"
  }'
```

---

## 6. Configuring Cloud Foundation LLM Adapters

The gateway includes pluggable adapters for major cloud LLM providers as well as a hermetic offline mock adapter.

### 6.1 Mock Adapter (Default / Offline Hermetic Mode)
No API keys or internet connection required. Used for automated tests and air-gapped deployments:

```python
from deid_gateway.gateway import DeidGateway
from deid_gateway.adapters import MockLLMAdapter

gateway = DeidGateway(adapter=MockLLMAdapter(mode="summarize"))
result = gateway.process(clinical_note="...", task_prompt="Summarize the plan")
print(result.final_text)
```

### 6.2 OpenAI Adapter (GPT-4o, GPT-4o-mini, o3-mini)
Set the environment variable:
```bash
export OPENAI_API_KEY="sk-..."
```
Usage:
```python
from deid_gateway.gateway import DeidGateway
from deid_gateway.adapters import OpenAIAdapter

adapter = OpenAIAdapter(model="gpt-4o", api_key="sk-...")
gateway = DeidGateway(adapter=adapter)
result = gateway.process(clinical_note="...", task_prompt="Extract clinical findings")
```

### 6.3 Anthropic Adapter (Claude 3.5 Sonnet / Haiku)
Set the environment variable:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```
Usage:
```python
from deid_gateway.gateway import DeidGateway
from deid_gateway.adapters import AnthropicAdapter

adapter = AnthropicAdapter(model="claude-3-5-sonnet-20241022", api_key="sk-ant-...")
gateway = DeidGateway(adapter=adapter)
result = gateway.process(clinical_note="...", task_prompt="Summarize medications")
```

### 6.4 Google Gemini Adapter (Gemini 1.5 Pro / 2.0 Flash)
Set the environment variable:
```bash
export GEMINI_API_KEY="AIzaSy..."
```
Usage:
```python
from deid_gateway.gateway import DeidGateway
from deid_gateway.adapters import GeminiAdapter

adapter = GeminiAdapter(model="gemini-1.5-pro", api_key="AIzaSy...")
gateway = DeidGateway(adapter=adapter)
result = gateway.process(clinical_note="...", task_prompt="Provide differential diagnosis")
```

---

## 7. Troubleshooting & Common Questions

1. **Why does rehydration require the session mapping?**
   The gateway maintains a zero-retention privacy posture. The session mapping dictionary is returned directly to the calling client and is never persisted in a central database, eliminating secondary data exposure vulnerabilities.
2. **How does date shifting preserve post-operative intervals?**
   Dates within a single patient session are shifted by the exact same signed day offset $\Delta d$ computed via HMAC-SHA256. Clinical duration expressions (e.g. `"post-operative day 2"`) are protected from date shifting, preserving $\Delta t' = \Delta t$.
3. **How does the gateway distinguish Dr. Whipple from Whipple procedure?**
   The tri-filter eponym engine gives precedence to honorifics (`Dr.`, `Attending:`) and professional credentials (`MD`, `FACS`) to mask real providers, while protecting trailing clinical context suffixes (`procedure`, `disease`, `syndrome`).
