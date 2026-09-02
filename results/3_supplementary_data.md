# Deliverable 3: Supplementary Data & Verification Traces

## 1. 18 HIPAA Safe Harbor Identifier Categories Matrix

The gateway detects, categorizes, and replaces all 18 identifiers designated under 45 CFR § 164.514(b)(2):

| # | Safe Harbor Category | Safe Harbor Description | Gateway Surrogate Token | Detection Method |
|---|---|---|---|---|
| 1 | **Names** | Patients, relatives, household members | `[PATIENT_1]`, `[PROVIDER_1]` | Transformer NER + Gazetteers |
| 2 | **Geographic Subdivisions** | Street addresses, cities, counties, ZIP codes | `[ADDRESS_1]`, `[CITY_1]`, `[ZIP_1]` | Contextual Gazetteers + NER |
| 3 | **Dates** | All dates (except year) directly related to an individual | `[DATE_1]`, `[DATE_2]` | Deterministic Date Shifter ($\Delta d$) |
| 4 | **Telephone Numbers** | Primary, mobile, clinic phone numbers | `[PHONE_1]` | High-Entropy Regex |
| 5 | **Fax Numbers** | Hospital and clinic facsimile numbers | `[FAX_1]` | Contextual Regex |
| 6 | **Email Addresses** | Patient and provider electronic mail | `[EMAIL_1]` | RFC 5322 Regex Pattern |
| 7 | **Social Security Numbers** | 9-digit SSN (formatted or unformatted) | `[SSN_1]` | Strict Format Pattern |
| 8 | **Medical Record Numbers** | Institutional MRNs | `[MRN_1]` | Structural EHR Matcher |
| 9 | **Health Plan Beneficiary IDs**| Policy numbers, Medicaid/Medicare IDs | `[HEALTH_PLAN_1]` | Alphanumeric Pattern |
| 10 | **Account Numbers** | Billing and encounter account numbers | `[ACCOUNT_1]` | Structural Regex |
| 11 | **Certificate / License Numbers**| Driver licenses, DEA, State medical licenses | `[LICENSE_1]`, `[DEA_1]`, `[NPI_1]` | Checksum Regex Validation |
| 12 | **Vehicle Identifiers** | License plates, VIN numbers | `[VEHICLE_1]` | Standard ISO VIN Regex |
| 13 | **Device Identifiers & UDIs** | Pacemaker serials, implantable UDIs | `[DEVICE_1]` | FDA GUDID Specification |
| 14 | **Web URLs** | Hospital portals, telehealth URLs | `[URL_1]` | Strict URI Regex |
| 15 | **IP Addresses** | IPv4 and IPv6 network identifiers | `[IP_1]` | IPv4 / IPv6 Octet Matcher |
| 16 | **Biometric Identifiers** | Fingerprints, voiceprints, retinal scans | `[BIOMETRIC_1]` | Clinical Entity Rules |
| 17 | **Full-Face Photographs** | Clinical image links, photo IDs | `[PHOTO_1]` | Attachment URI Rules |
| 18 | **Unique Identifying Numbers** | Accession codes, pathology specimen IDs | `[ACCESSION_1]` | Specimen Prefix Classifier |

---

## 2. Evaluation Dataset Specification

- **File**: `tests/data/annotated_clinical_notes_55.json`
- **Total Notes**: 55 gold-standard synthetic clinical notes.
- **Total Hand-Annotated Ground-Truth Entities**: 732 entities.
- **Medical Specialties (10)**: Neurology, Surgical Oncology, Cardiology, Geriatrics, Gastroenterology, Emergency Trauma, Urology, Pediatrics, Hematology/Oncology, Orthopedics.
- **Adversarial Stress Axes (9)**: Doctor eponyms vs condition eponyms, age > 89 vs medication strengths (`25/100 mg`), header vs signature surnames, dates in multi-page tables, negative lab references, Unicode bracket collisions.

---

## 3. Standardized Incident Log (`FAILURES.md` Summary)

The engineering process systematically logged and resolved 12 critical technical hurdles:

| Incident ID | Summary / Challenge | Root Cause | Engineering Solution & Invariant |
|---|---|---|---|
| `FAIL-001` | Medical Eponym Over-Redaction | Naive NER masked *Whipple procedure* as person name | Implemented tri-filter suffix whitelist (*procedure*, *disease*, *syndrome*) |
| `FAIL-002` | Substring Token Collision | Replacing `[PATIENT_1]` corrupted `[PATIENT_10]` | Implemented strictly length-descending substitution order |
| `FAIL-003` | Non-PHI Literal Bracket Collision | Pre-existing clinical checkboxes `[x]` clashed with tokens | Unicode Mathematical White Square Bracket escaping (`⟦x⟧`) |
| `FAIL-004` | Nonagenarian Age False Negatives | Unconventional syntax (*"94yo male"*, *"nonagenarian"*) missed | Regex boundary aggregation to Safe Harbor `[AGE_90+]` |
| `FAIL-005` | Relative Duration Date Distortion | Date shifter altered *"3 days post-op"* incorrectly | Preserved relative duration spans while shifting calendar anchors |
| `FAIL-006` | LLM Token Mutation | Foundation model injected whitespace `[ PATIENT_1 ]` | Fuzzy regex normalizer repairing casing and spacing before lookup |
| `FAIL-007` | Hallucinated Token Exceptions | LLM hallucinated unmapped token `[PATIENT_99]` | Safe pass-through filter preventing pipeline crashes |
| `FAIL-008` | High-Throughput CPU Latency | Large transformer models exceeded 50ms per token | Optimized sequence labeler backbone (124.4M params, sub-5ms CPU) |
| `FAIL-009` | Surname Geographic Misclassification | *"Mr. Henderson"* masked as `[CITY_1]` due to town match | Header name propagation with semantic priority (`PATIENT > CITY`) |
| `FAIL-010` | Medication Strength False Positive | *"25/100 mg"* masked as age > 89 | Negative context assertions for dosages (`mg`, `mcg`) and vitals |
| `FAIL-011` | Date Shift Inversion Collision | Unshifted date collided with surrogate token replacement | Strict sequential pipeline isolation preventing surrogate corruption |
| `FAIL-012` | Age Suffix Duplicate & Token Order | Generative output produced *"94-year-old years old"* | Forward-order token assignment and generative suffix deduplication |
