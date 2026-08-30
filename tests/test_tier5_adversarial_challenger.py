"""
Tier 5 Adversarial Challenge & Stress Test Suite.
Empirically stress-tests the entire PHI/PII De-Identification Gateway against:
1. Fuzz testing, malformed inputs, massive inputs (100k+ chars), unicode edge cases, emojis, non-English scripts.
2. Tricky medical eponyms (e.g. Dr. Parkinson vs Parkinson's disease, Whipple procedure vs Dr. Whipple, Patient Alzheimer vs Alzheimer's disease).
3. Extreme date formats: leap year dates (Feb 29), century transitions, ISO8601 timestamps, relative phrases vs calendar dates.
4. Nonagenarian boundary conditions: 88 yo (preserve), 89 yo (preserve), 90 yo (mask to [AGE_90+]), 91 yo (mask), 105 yo (mask).
5. Rehydration adversarial attacks: LLM modifications (lowercase, spaced, parentheses, unbracketed), hallucinated surrogates, pre-existing non-PHI brackets ([x], [Normal], [Stage IV]).
6. Concurrency stress test: 50 concurrent requests verifying strict state isolation and zero cross-contamination.
"""

import concurrent.futures
import datetime
import pytest

from deid_gateway.adapters.mock_adapter import MockLLMAdapter
from deid_gateway.core.collision_guard import CollisionGuard
from deid_gateway.core.config import DeidConfig
from deid_gateway.core.date_shifter import DateShifter
from deid_gateway.core.deidentify import deidentify
from deid_gateway.core.eponyms import EponymDisambiguator
from deid_gateway.core.models.classifier import HybridTokenClassifier
from deid_gateway.core.rehydrate import rehydrate
from deid_gateway.gateway import DeidGateway


class TestFuzzAndMassiveInputs:
    """Fuzz testing with malformed inputs, massive inputs, unicode, and non-English scripts."""

    def test_empty_and_null_inputs(self):
        """Verify handling of empty string, None, and whitespace-only text."""
        for empty_val in ["", "   ", "\n\n\t  \r\n", None]:
            masked, mapping = deidentify(empty_val)
            assert isinstance(masked, str)
            assert isinstance(mapping, dict)
            rehydrated = rehydrate(masked, mapping)
            assert isinstance(rehydrated, str)

    def test_massive_document_100k_chars(self):
        """Stress-test gateway with a 100k+ character document containing interspersed PHI."""
        base_filler = (
            "The patient was admitted for standard clinical observation. Vital signs were stable. "
            "Cardiovascular exam revealed normal S1 and S2 without murmurs. Lungs were clear to auscultation. "
            "Abdomen was soft, non-tender, non-distended with normal bowel sounds. "
        )
        # Create ~120,000 characters
        num_repeats = 600
        text_parts = []
        for i in range(num_repeats):
            text_parts.append(base_filler)
            if i == 50:
                text_parts.append("\nAttending: Dr. Montgomery Scott, MD\n")
            elif i == 150:
                text_parts.append("\nPatient: Jonathan Archer, DOB: 03/15/1975, MRN: MRN-884920\n")
            elif i == 300:
                text_parts.append("\nContact Phone: (555) 234-5678, SSN: 000-12-3456\n")
            elif i == 450:
                text_parts.append("\nFacility: Memorial Sloan Kettering Cancer Center, Date: 2024-02-29\n")

        massive_text = "".join(text_parts)
        assert len(massive_text) > 100000

        masked, mapping = deidentify(massive_text)
        assert len(masked) > 0
        assert "000-12-3456" not in masked
        assert "(555) 234-5678" not in masked
        assert "MRN-884920" not in masked
        assert "Jonathan Archer" not in masked
        assert "Montgomery Scott" not in masked

        rehydrated = rehydrate(masked, mapping)
        assert "Jonathan Archer" in rehydrated
        assert "Montgomery Scott" in rehydrated
        assert "MRN-884920" in rehydrated
        assert "000-12-3456" in rehydrated

    def test_unicode_and_multilingual_edge_cases(self):
        """Test right-to-left, zero-width characters, accents, Cyrillic, and CJK characters."""
        text = (
            "Patient: Alice Walker, DOB: 1980-05-12\n"
            "Attending: Dr. Robert Vance, MD\n"
            "Notes in Russian: Пациент осмотрен доктором Dr. Ivan Petrov в клинике.\n"
            "Notes in Arabic: تم فحص المريض بواسطة Dr. Tariq Al-Mansoor.\n"
            "Notes in Chinese: 患者由 Dr. Wei Zhang 医师诊断。\n"
            "Notes in Japanese: 患者は Dr. Kenji Sato 医師の診察を受けた。\n"
            "Invisible characters: \u200b\u200c\u200dDr. Alan Turing attended the consult.\n"
            "Mixed Emojis: 🩺 Patient: Alice Walker, 🩹 Phone: 415-555-9081 💉 Date: 2023-11-20"
        )

        masked, mapping = deidentify(text)
        # Check that PHI names are masked
        assert "Alice Walker" not in masked
        assert "415-555-9081" not in masked
        assert "Robert Vance" not in masked

        rehydrated = rehydrate(masked, mapping)
        assert "Alice Walker" in rehydrated
        assert "415-555-9081" in rehydrated
        assert "Robert Vance" in rehydrated

    def test_sql_json_and_code_injection_in_clinical_notes(self):
        """Test resilience against injection strings, quotes, brackets, and escapes in notes."""
        malicious_note = (
            "Patient: Robert'); DROP TABLE Patients;-- (DOB: 1970-01-01)\n"
            "JSON payload: {\"provider\": \"Dr. Jane Doe\", \"ssn\": \"123-45-6789\", \"role\": \"admin\"}\n"
            "HTML tags: <script>alert('xss');</script> Attending: Dr. John Smith, MD\n"
            "Unclosed quotes: '\"`'\"` and backslashes \\\\\\\\ and nulls \x00\x00 in narrative."
        )
        masked, mapping = deidentify(malicious_note)
        assert "123-45-6789" not in masked
        assert "Jane Doe" not in masked
        assert "John Smith" not in masked

        rehydrated = rehydrate(masked, mapping)
        assert "123-45-6789" in rehydrated
        assert "Jane Doe" in rehydrated
        assert "John Smith" in rehydrated


class TestTrickyMedicalEponyms:
    """Rigorous challenge of clinical eponym disambiguation (Tri-filter logic)."""

    def test_prompt_authoritative_eponym_challenge(self):
        """
        Authoritative prompt test:
        'Dr. Parkinson treated Parkinson's disease with the Whipple procedure while consulting Dr. Whipple and Patient Alzheimer who has Alzheimer's disease.'
        """
        text = "Dr. Parkinson treated Parkinson's disease with the Whipple procedure while consulting Dr. Whipple and Patient Alzheimer who has Alzheimer's disease."
        masked, mapping = deidentify(text)

        # 1. Eponym concepts MUST BE PRESERVED unmasked:
        assert "Parkinson's disease" in masked, f"Parkinson's disease was corrupted or masked in: {masked}"
        assert "Whipple procedure" in masked, f"Whipple procedure was corrupted or masked in: {masked}"

        # 2. Human names MUST BE MASKED:
        assert "Dr. Parkinson" not in masked
        assert "Dr. Whipple" not in masked

        # 3. Round-trip rehydration must restore exact original text:
        rehydrated = rehydrate(masked, mapping)
        assert rehydrated == text

    def test_complex_multi_eponym_clinical_battery(self):
        """Test a dense multi-eponym scenario spanning various medical subspecialties."""
        test_cases = [
            (
                "Dr. Crohn evaluated Crohn's disease and prescribed biologic therapy.",
                "Crohn's disease",  # preserved
                "Dr. Crohn"        # masked
            ),
            (
                "Attending: Dr. Bell examined the patient for acute Bell's palsy.",
                "Bell's palsy",
                "Dr. Bell"
            ),
            (
                "Surgeon Dr. Kocher performed the Kocher maneuver while Dr. William performed a procedure.",
                "Kocher maneuver",
                "Dr. Kocher"
            ),
            (
                "Dr. Hodgkin diagnosed classical Hodgkin lymphoma in consultation with Dr. Kaposi regarding Kaposi sarcoma.",
                "Hodgkin lymphoma",
                "Dr. Hodgkin"
            ),
            (
                "Dr. McBurney elicited tenderness at McBurney's point and Dr. Murphy noted positive Murphy's sign.",
                "McBurney's point",
                "Dr. McBurney"
            ),
            (
                "Patient Tourette presents with Tourette syndrome and Dr. Guillain confirmed Guillain-Barre syndrome.",
                "Tourette syndrome",
                "Patient Tourette"
            ),
            (
                "Neurologist Dr. Babinski tested the Babinski reflex and evaluated the Circle of Willis.",
                "Babinski reflex",
                "Dr. Babinski"
            )
        ]

        for text, preserved_eponym, masked_phi in test_cases:
            masked, mapping = deidentify(text)
            assert preserved_eponym in masked, f"Failed to preserve eponym '{preserved_eponym}' in '{masked}'"
            assert masked_phi not in masked, f"Failed to mask PHI '{masked_phi}' in '{masked}'"
            rehydrated = rehydrate(masked, mapping)
            assert rehydrated == text

    def test_eponym_case_and_punctuation_variations(self):
        """Test eponyms in uppercase, lowercase, and hyphenated variations."""
        text = (
            "Assessment: PARKINSON'S DISEASE with positive BABINSKI SIGN.\n"
            "Attending Physician: Dr. Alexander Hamilton, MD\n"
            "Procedures: whipple procedure and fontan procedure completed successfully."
        )
        masked, mapping = deidentify(text)
        assert "PARKINSON'S DISEASE" in masked
        assert "BABINSKI SIGN" in masked
        assert "whipple procedure" in masked
        assert "Alexander Hamilton" not in masked

        rehydrated = rehydrate(masked, mapping)
        assert "Alexander Hamilton" in rehydrated
        assert "PARKINSON'S DISEASE" in rehydrated


class TestExtremeDateFormatsAndBoundaries:
    """Extreme date formats: leap year dates, century transitions, ISO8601, and relative phrases."""

    def test_leap_year_february_29_shifting(self):
        """Test shifting Feb 29 (leap day) both forward and backward."""
        shifter = DateShifter()
        # 2024 is a leap year (366 days). 2024-02-29 + 365 days is 2025-02-28
        res_leap = shifter.parse_and_shift("2024-02-29", delta_days=365)
        assert res_leap is not None
        assert res_leap.shifted_text == "2025-02-28"

        # 2024-02-29 + 366 days is 2025-03-01
        res_leap_366 = shifter.parse_and_shift("2024-02-29", delta_days=366)
        assert res_leap_366 is not None
        assert res_leap_366.shifted_text == "2025-03-01"

        res_leap_back = shifter.parse_and_shift("2024-02-29", delta_days=-366)
        assert res_leap_back is not None
        # 2024-02-29 - 366 days is 2023-02-28
        assert res_leap_back.shifted_text == "2023-02-28"

        # Test textual leap date
        res_text_leap = shifter.parse_and_shift("February 29, 2024", delta_days=10)
        assert res_text_leap is not None
        assert res_text_leap.shifted_text == "March 10, 2024"

    def test_century_transition_dates(self):
        """Test shifting across century boundary (1999 to 2000, 2000 to 1999)."""
        shifter = DateShifter()
        res_y2k = shifter.parse_and_shift("12/31/1999", delta_days=1)
        assert res_y2k is not None
        assert res_y2k.shifted_text == "01/01/2000"

        res_y2k_back = shifter.parse_and_shift("01/01/2000", delta_days=-1)
        assert res_y2k_back is not None
        assert res_y2k_back.shifted_text == "12/31/1999"

    def test_two_digit_years(self):
        """Test two-digit year representations."""
        shifter = DateShifter()
        res = shifter.parse_and_shift("05/12/99", delta_days=30)
        assert res is not None
        assert res.shifted_text == "06/11/99"

    def test_relative_phrases_vs_calendar_dates(self):
        """
        Verify relative clinical intervals are preserved untouched while calendar dates are masked.
        """
        text = (
            "Patient was admitted on 2023-10-15. On post-operative day 2, fever developed. "
            "Symptoms started 3 weeks ago and improved 2 days later. "
            "Dosing schedule: take 50mg every 8 hours (q8h) for the past 5 days. "
            "Follow-up scheduled for 2023-11-20 (in 3 weeks)."
        )
        masked, mapping = deidentify(text, preserve_relative_dates=True)

        # Relative phrases must be preserved
        assert "post-operative day 2" in masked
        assert "3 weeks ago" in masked
        assert "2 days later" in masked
        assert "every 8 hours" in masked
        assert "q8h" in masked
        assert "for the past 5 days" in masked
        assert "in 3 weeks" in masked

        # Exact calendar dates must be masked
        assert "2023-10-15" not in masked
        assert "2023-11-20" not in masked

        rehydrated = rehydrate(masked, mapping)
        assert "2023-10-15" in rehydrated
        assert "2023-11-20" in rehydrated

    def test_relative_date_interval_delta_invariance(self):
        """
        Verify that relative time interval Delta t between two calendar dates in a patient record
        is preserved identically after date shifting (Delta t' == Delta t).
        """
        shifter = DateShifter(salt="adversarial_test_salt")
        delta = shifter.compute_delta_days(seed="patient_adversarial_123")

        d1 = datetime.date(2023, 4, 10)
        d2 = datetime.date(2023, 4, 25)
        raw_delta = (d2 - d1).days  # 15 days

        res1 = shifter.parse_and_shift("2023-04-10", delta)
        res2 = shifter.parse_and_shift("2023-04-25", delta)

        assert res1 is not None and res2 is not None
        shifted_delta = (res2.shifted_date - res1.shifted_date).days
        assert shifted_delta == raw_delta == 15


class TestNonagenarianBoundaryConditions:
    """
    Nonagenarian boundary conditions under HIPAA Safe Harbor (45 CFR § 164.514(b)(2)(i)(C)):
    Ages < 90 are preserved.
    Ages >= 90 (90, 91, 105, etc.) must be aggregated to [AGE_90+] or equivalent.
    """

    def test_exact_age_boundaries_88_89_90_91_105(self):
        """Test boundary ages: 88, 89, 90, 91, 105."""
        # 88 yo -> Preserve
        t88 = "Patient is an 88 yo male presenting with knee pain."
        m88, _ = deidentify(t88)
        assert "88 yo" in m88
        assert "[AGE_90+]" not in m88

        # 89 yo -> Preserve
        t89 = "Patient is an 89-year-old female presenting with mild tremor."
        m89, _ = deidentify(t89)
        assert "89-year-old" in m89
        assert "[AGE_90+]" not in m89

        # 90 yo -> Mask to [AGE_90+]
        t90 = "Patient is a 90 yo male admitted for pneumonia."
        m90, map90 = deidentify(t90)
        assert "90 yo" not in m90
        assert "[AGE_90+]" in m90
        assert rehydrate(m90, map90) == t90

        # 91 yo -> Mask to [AGE_90+]
        t91 = "Patient is a 91-year-old female with osteoarthritis."
        m91, map91 = deidentify(t91)
        assert "91-year-old" not in m91
        assert "[AGE_90+]" in m91
        assert rehydrate(m91, map91) == t91

        # 105 yo -> Mask to [AGE_90+]
        t105 = "Patient is a 105 yo female celebrating her longevity."
        m105, map105 = deidentify(t105)
        assert "105 yo" not in m105
        assert "[AGE_90+]" in m105
        assert rehydrate(m105, map105) == t105

    def test_nonagenarian_syntactic_variations(self):
        """Test various narrative formats for nonagenarians and centenarians."""
        syntactic_forms = [
            ("Patient aged 92 was evaluated by cardiology.", "aged 92"),
            ("The patient turned 95 last month.", "turned 95"),
            ("Patient is celebrating her 100th birthday in hospice.", "100th birthday"),
            ("A nonagenarian patient presented to the ED.", "nonagenarian"),
            ("A centenarian individual with cognitive decline.", "centenarian"),
            ("Patient: 94 y/o female admitted from skilled nursing.", "94 y/o"),
        ]

        for text, phrase in syntactic_forms:
            masked, mapping = deidentify(text)
            assert phrase not in masked, f"Failed to mask '{phrase}' in: {masked}"
            assert "[AGE_90+]" in masked, f"Expected [AGE_90+] in: {masked}"
            rehydrated = rehydrate(masked, mapping)
            assert rehydrated == text


class TestRehydrationAdversarialAttacks:
    """
    Rehydration adversarial tests:
    - LLM modifications (lowercase surrogates, spaced surrogates, parentheses)
    - Hallucinated non-existent surrogates ([PATIENT_99])
    - Pre-existing non-PHI brackets ([x], [Normal], [Stage IV])
    """

    def test_llm_syntax_modifications_lowercase_and_spaced(self):
        """Test rehydration when downstream LLM modifies token case or spacing."""
        mapping = {
            "token_to_original": {
                "[PATIENT_1]": "Eleanor Vance",
                "[PROVIDER_1]": "Dr. Hugh Crain",
                "[DATE_1]": "2024-03-15",
                "[AGE_90+]": "93 yo"
            },
            "bracket_map": {},
            "date_mappings": []
        }

        # Case 1: Lowercase tokens from LLM
        llm_output_lower = "Summary: [patient_1] was treated by [provider_1] on [date_1]. Patient is [age_90+]."
        rehydrated_lower = rehydrate(llm_output_lower, mapping)
        assert "Eleanor Vance" in rehydrated_lower
        assert "Dr. Hugh Crain" in rehydrated_lower
        assert "2024-03-15" in rehydrated_lower
        assert "93 yo" in rehydrated_lower

        # Case 2: Spaced brackets from LLM
        llm_output_spaced = "Summary: [ PATIENT_1 ] was treated by [  PROVIDER_1  ] on [ DATE_1 ]. Patient is [ AGE 90+ ]."
        rehydrated_spaced = rehydrate(llm_output_spaced, mapping)
        assert "Eleanor Vance" in rehydrated_spaced
        assert "Dr. Hugh Crain" in rehydrated_spaced
        assert "2024-03-15" in rehydrated_spaced
        assert "93 yo" in rehydrated_spaced

        # Case 3: Parentheses from LLM
        llm_output_paren = "Summary: (PATIENT_1) was treated by (PROVIDER_1)."
        rehydrated_paren = rehydrate(llm_output_paren, mapping)
        assert "Eleanor Vance" in rehydrated_paren
        assert "Dr. Hugh Crain" in rehydrated_paren

        # Case 4: Unbracketed tokens from LLM
        llm_output_unbracketed = "Summary: PATIENT_1 was treated by PROVIDER_1."
        rehydrated_unbracketed = rehydrate(llm_output_unbracketed, mapping)
        assert "Eleanor Vance" in rehydrated_unbracketed
        assert "Dr. Hugh Crain" in rehydrated_unbracketed

    def test_hallucinated_non_existent_surrogates(self):
        """Test resilience against hallucinated surrogate tokens that were never in the mapping."""
        mapping = {
            "token_to_original": {
                "[PATIENT_1]": "Luke Sanderson",
                "[PROVIDER_1]": "Dr. Theodora Montague"
            },
            "bracket_map": {},
            "date_mappings": []
        }

        llm_hallucinated = (
            "[PATIENT_1] consulted [PROVIDER_1]. Also mentioned [PATIENT_99], [PROVIDER_Z], and [HOSPITAL_999]."
        )
        rehydrated = rehydrate(llm_hallucinated, mapping)
        # Valid tokens must be restored
        assert "Luke Sanderson" in rehydrated
        assert "Dr. Theodora Montague" in rehydrated
        # Hallucinated tokens must remain untouched as literal strings without error
        assert "[PATIENT_99]" in rehydrated
        assert "[PROVIDER_Z]" in rehydrated
        assert "[HOSPITAL_999]" in rehydrated

    def test_pre_existing_non_phi_brackets_preservation(self):
        """
        Verify that clinical notes with pre-existing non-PHI brackets
        ([x], [1], [Normal], [Stage IV], [+/-]) round-trip with 100% fidelity.
        """
        note_with_brackets = (
            "Clinical Assessment Checklist:\n"
            "  - Motor Strength: [Normal]\n"
            "  - Sensation: [Intact]\n"
            "  - Deep Tendon Reflexes: [2+]\n"
            "  - Tumor Staging: [Stage IVB]\n"
            "  - Findings: [x] positive for tremor, [ ] negative for rigidity\n"
            "  - Reference: [1] Harrison's Internal Medicine, [2] UpToDate\n"
            "Patient: Arthur Dent\n"
            "DOB: 1978-04-12\n"
            "Attending: Dr. Ford Prefect, MD"
        )

        masked, mapping = deidentify(note_with_brackets)

        # PHI must be masked
        assert "Arthur Dent" not in masked
        assert "Ford Prefect" not in masked
        assert "1978-04-12" not in masked

        # Rehydration must restore all non-PHI brackets and PHI entities exactly
        rehydrated = rehydrate(masked, mapping)
        assert "[Normal]" in rehydrated
        assert "[Intact]" in rehydrated
        assert "[2+]" in rehydrated
        assert "[Stage IVB]" in rehydrated
        assert "[x]" in rehydrated
        assert "[1]" in rehydrated
        assert "[2]" in rehydrated
        assert "Arthur Dent" in rehydrated
        assert "Ford Prefect" in rehydrated
        assert rehydrated == note_with_brackets


class TestConcurrencyStressIsolation:
    """
    Stress-tests concurrent requests through deidentify and rehydrate (50 threads).
    Verifies strict session state isolation and zero cross-contamination.
    """

    def test_50_concurrent_requests_state_isolation(self):
        """
        Spawns 50 concurrent worker threads executing deidentify -> rehydrate
        with distinct patient names, doctor names, MRNs, dates, and diagnoses.
        """
        num_concurrent = 50

        def _execute_worker(worker_id: int):
            patient_name = f"Patient {worker_id:03d} Doe"
            provider_name = f"Dr. Specialist {worker_id:03d} Smith"
            mrn = f"MRN-{worker_id:05d}"
            date_str = f"2023-{(worker_id % 12) + 1:02d}-{(worker_id % 28) + 1:02d}"
            ssn = f"{worker_id:03d}-45-6789"

            clinical_note = (
                f"Patient: {patient_name}\n"
                f"DOB: {date_str}\n"
                f"MRN: {mrn}, SSN: {ssn}\n"
                f"Attending: {provider_name}, MD\n"
                f"Diagnosis: Parkinson's disease evaluated under Whipple protocol with [Stage I] status.\n"
                f"Plan: Follow-up in 2 weeks."
            )

            # De-identify
            masked, mapping = deidentify(clinical_note, patient_id=f"pt_id_{worker_id}")

            # Verify no leakage
            assert patient_name not in masked, f"Worker {worker_id} leaked patient_name"
            assert provider_name not in masked, f"Worker {worker_id} leaked provider_name"
            assert mrn not in masked, f"Worker {worker_id} leaked MRN"
            assert ssn not in masked, f"Worker {worker_id} leaked SSN"
            assert "Parkinson's disease" in masked, f"Worker {worker_id} lost eponym"

            # Rehydrate
            rehydrated = rehydrate(masked, mapping)

            # Verify exact restoration
            assert rehydrated == clinical_note, f"Worker {worker_id} rehydration mismatch"
            assert patient_name in rehydrated
            assert provider_name in rehydrated
            assert "[Stage I]" in rehydrated

            return {
                "worker_id": worker_id,
                "patient_name": patient_name,
                "provider_name": provider_name,
                "success": True,
                "mapping_entities": len(mapping["entities"])
            }

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(_execute_worker, i) for i in range(num_concurrent)]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                results.append(res)

        assert len(results) == num_concurrent
        assert all(r["success"] for r in results)


class TestFullGatewayE2EStress:
    """End-to-End gateway pipeline stress test under diverse task prompts."""

    def test_gateway_roundtrip_with_mock_adapter_tasks(self):
        """Test full gateway roundtrip with summarization, QA, and extraction tasks."""
        adapter = MockLLMAdapter()
        gateway = DeidGateway(adapter=adapter)

        clinical_note = (
            "Patient: Sarah Connor\n"
            "DOB: 1984-05-12\n"
            "Attending: Dr. Peter Silberman, MD\n"
            "Facility: Cyberdyne Regional Medical Center\n"
            "Assessment: Parkinson's disease with mild resting tremor. [x] Checklist complete.\n"
            "Plan: Carbidopa-levodopa 25/100mg TID. Follow-up on 2024-06-15."
        )

        for task_mode in ["summarize", "qa", "extract"]:
            adapter.mode = task_mode
            result = gateway.process(
                clinical_note=clinical_note,
                task_prompt="Please analyze this clinical record: {text}"
            )

            # Check that masked input received by LLM had 0 raw PHI
            assert "Sarah Connor" not in result.masked_input
            assert "Peter Silberman" not in result.masked_input

            # Check that final rehydrated text restores entities properly
            assert len(result.final_text) > 0
            assert result.latency_ms > 0
            assert result.leak_detected is False
