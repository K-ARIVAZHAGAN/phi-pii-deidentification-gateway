# Test Ready: PHI/PII De-Identification Gateway E2E Test Suite

**Status**: READY FOR MILESTONE VERIFICATION & CONTINUOUS CI  
**Test Framework**: `pytest`  
**Evaluation Corpus**: `tests/data/annotated_clinical_notes_55.json` (55 Gold-Standard Annotated Clinical Notes across 10 Specialties & 9 Adversarial Axes)

---

## 1. Test Suite Architecture & Tiers Overview

The test suite implements a rigorous 4-tier verification matrix covering all 18 HIPAA Safe Harbor categories, sub-1B parameter model constraints, deterministic date shifting, medical eponym disambiguation, and foundation LLM gateway roundtrip integrity.

| Tier | Focus | Test Files | Coverage & Invariants |
|---|---|---|---|
| **Tier 1** | **Feature Coverage** | `tests/test_core_deid.py`<br>`tests/test_pseudonymizer.py`<br>`tests/test_date_shifter.py`<br>`tests/test_eponyms.py`<br>`tests/test_adapters.py`<br>`tests/test_benchmarks.py` | All 18 Safe Harbor categories, sub-1B model parameter ceiling (<125M params), consistent surrogate generation, date shift offset calculation, tri-filter eponym rules, MockLLMAdapter task modes (Summarize, QA, Extract). |
| **Tier 2** | **Boundary & Corner Cases** | `tests/test_core_deid.py`<br>`tests/test_pseudonymizer.py`<br>`tests/test_date_shifter.py`<br>`tests/test_eponyms.py`<br>`tests/test_rehydration.py`<br>`tests/test_adapters.py` | Empty string inputs, non-PHI clinical notes, punctuation and delimiter adjacency, unicode/accents, leap years (Feb 29), year-end boundaries, nonagenarian/centenarian age > 89 aggregation, fuzzy token mutation normalization (`[ patient 1 ]` -> `[PATIENT_1]`), hallucinated surrogate token resistance, literal non-PHI bracket preservation (`[x]`, `[1]`, `[Normal]`). |
| **Tier 3** | **Cross-Feature & Pipeline Integration** | `tests/test_gateway_pipeline.py`<br>`tests/test_benchmarks.py` | Full roundtrip pipeline (`Raw Note -> deidentify -> Mock/Cloud LLM -> rehydrate`), **Zero Raw PHI Transmission Guard** (asserts 0 PHI delivered to foundation LLM adapter), timing telemetry and latency percentiles (p50/p95), quantitative metrics calculation (Precision/Recall/F1/F2, Document Leak Rate, Utility Delta). |
| **Tier 4** | **Real-World E2E Application Scenarios** | `tests/test_e2e_scenarios.py` | Executes all 55 held-out annotated synthetic clinical notes across 10 specialties with 9 adversarial challenge axes; asserts **0% Document Leak Rate**, 100% Medical Eponym Preservation, and 100% Rehydration Restoration. |

---

## 2. 55-Note Evaluation Corpus Distribution (`tests/data/annotated_clinical_notes_55.json`)

The evaluation corpus contains **732 ground-truth entity annotations** with exact character start/end offsets, validated against their source spans:

### 2.1 Clinical Specialty Coverage (10 Disciplines)
1. **Oncology & Hematology** (Notes 01–06): Hodgkin lymphoma vs Dr. Hodgkin, Whipple procedure vs Dr. Whipple, Raynaud's phenomenon, clinical trial subject IDs, DICOM facial photo tags.
2. **Cardiology & Cardiothoracic Surgery** (Notes 07–12): Pacemaker UDI & serials, Bundle of His / Purkinje fibers vs Dr. His, Swan-Ganz catheter, Medicare MBI, CABG operative flowsheets.
3. **Neurology & Neurosurgery** (Notes 13–18): Parkinson's disease vs Dr. Parkinson, Alzheimer's dementia vs Dr. Alzheimer, Circle of Willis, Bell's palsy, Babinski reflex, EEG reports.
4. **Pediatrics & Neonatology** (Notes 19–23): NICU discharge, Apgar score, multi-family member names (mother, father, guardian), Kawasaki disease, school locations, DNA barcodes.
5. **Geriatrics & Palliative Care** (Notes 24–29): Nonagenarian and centenarian ages (91yo, 94yo, 97yo, 102yo), DOB calculations, hospice transition, multi-date interval shifts.
6. **Psychiatry & Behavioral Health** (Notes 30–34): Involuntary hold intake, police report #, Wernicke-Korsakoff syndrome, telehealth psychotherapy URLs, adolescent ADHD intake.
7. **Orthopedics & Sports Medicine** (Notes 35–39): Total Knee Arthroplasty implant serials, Tinel's sign & Phalen's maneuver, Lachman & McMurray signs, Ponseti clubfoot method, Trendelenburg sign.
8. **Gastroenterology & Hepatology** (Notes 40–44): Crohn's disease vs Dr. Crohn, Barrett's esophagus, Zollinger-Ellison syndrome, Mallory-Weiss tear, Whipple's disease, biliary stent lot #.
9. **Telehealth & Infectious Disease** (Notes 45–49): Telehealth IPv4/IPv6 session logs, encrypted Zoom URLs, Lyme disease timelines, Paxlovid virtual care, Bluetooth pulse oximeter telemetry.
10. **Emergency Medicine & Trauma Resuscitation** (Notes 50–55): Level 1 trauma flowsheet, Glasgow Coma Scale, McBurney's point & Murphy's sign, MVC vehicle VIN & plates, Foley catheter resuscitation, molecular pathology NGS accession barcodes.

### 2.2 Adversarial Challenge Axes Covered (9 Categories)
- `eponym_vs_doctor_name`: Disambiguation of physician surnames matching disease/sign/procedure concepts.
- `nicknames_and_aliases`: Informal diminutive names ("Skip", "Billy", "Chuck", "Artie", "Spidey", "Hulk").
- `typos_and_phonetic_misspellings`: OCR and STT transcription errors in names and medical keywords.
- `tables_and_flowsheets`: Multi-column pipe-delimited ASCII tables and compact telemetry logs.
- `signatures_headers_footers`: Multi-line digital physician signatures, NPI, DEA, and pager numbers.
- `age_over_89_geriatrics`: Safe Harbor 45 CFR § 164.514(b)(2)(i)(C) age aggregation rule.
- `unusual_identifiers_telehealth`: Device UDIs, MAC/IP addresses, trial subject IDs, barcodes.
- `relative_timeline_preservation`: Invariant chronological intervals ($\Delta t' = \Delta t$).
- `mixed_formatting_and_delimiters`: Slashes, brackets, unicode hyphens, and multi-part hyphenated names.

---

## 3. How to Run the Tests

### 3.1 Run Complete Test Suite (All Tiers)
```bash
python -m pytest tests/ -v
```

### 3.2 Run by Tier
```bash
# Tier 1 & 2: Unit & Boundary Tests
python -m pytest tests/test_core_deid.py tests/test_pseudonymizer.py tests/test_date_shifter.py tests/test_eponyms.py tests/test_rehydration.py tests/test_adapters.py -v

# Tier 3: Integration & Pipeline Tests
python -m pytest tests/test_gateway_pipeline.py tests/test_benchmarks.py -v

# Tier 4: Real-World 55-Note E2E Scenarios (Zero-Leak & Eponym Invariance)
python -m pytest tests/test_e2e_scenarios.py -v
```

### 3.3 Run Automated Benchmark Harness (Milestone 3 / CLI)
```bash
python -m deid_gateway.benchmarks.run_benchmarks --dataset tests/data/annotated_clinical_notes_55.json --render-markdown
```

---

## 4. Key Security & Quality Gates
- **Zero Raw PHI Leak Gate**: Any test failure detecting unmasked PHI in `masked_text` or foundation LLM prompts blocks release.
- **Eponym Diagnostic Gate**: Any test failure masking clinical disease names (*Parkinson's*, *Crohn's*, *Whipple*, *Bell's*, *Hodgkin*) blocks release.
- **Sub-1B Model Parameter Gate**: Parameter verification confirms all active token classification backbones use $\le 125\text{M}$ parameters ($< 13\%$ of 1B budget).
- **Rehydration Guard Gate**: Verifies that LLM syntax deviations (`[ patient 1 ]`, `(PROVIDER_A)`) and literal brackets (`[x]`, `[Normal]`) roundtrip with 100% fidelity.
