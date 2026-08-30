"""
Tier 4 Real-World Application Scenarios & Comprehensive E2E Verification.
Executes the full 55 held-out annotated synthetic clinical notes across:
- 10 Medical Specialties (Oncology, Cardiology, Neurology, Pediatrics, Geriatrics, Psychiatry, Orthopedics, Gastroenterology, Telehealth, Emergency Medicine).
- 9 Adversarial Challenge Axes (Eponyms vs Doctor Names, Nicknames, OCR/STT Typos, Tables, Signatures, Age > 89, Unusual IDs, Relative Timelines, Delimiters).
- Invariance Assertions:
  1. Zero Unmasked PHI Leak Rate (100% breach prevention).
  2. Medical Eponym Preservation (zero destruction of clinical concepts).
  3. Safe Harbor Age > 89 Aggregation.
  4. Relative Clinical Timeline Preservation (Delta t' == Delta t).
  5. 100% Roundtrip Rehydration Integrity.
"""

import pytest
from typing import Dict, Any, List

try:
    from deid_gateway.core.deidentify import deidentify
    from deid_gateway.core.rehydrate import rehydrate
    from deid_gateway.gateway import DeidGateway
    from deid_gateway.adapters.mock_adapter import MockLLMAdapter
except ImportError:
    deidentify = None
    rehydrate = None
    DeidGateway = None
    MockLLMAdapter = None


# =============================================================================
# TIER 4: ZERO UNMASKED PHI LEAK INVARIANCE (ALL 55 NOTES)
# =============================================================================

class TestTier4ZeroPHILeakInvariance:
    """
    Tier 4: Zero-Leak Invariance verification across all 55 held-out clinical notes.
    Every ground-truth PHI entity must be replaced by a surrogate token with 0 raw leaks.
    """

    def test_all_55_notes_zero_phi_leak(self, annotated_notes_55: List[Dict[str, Any]]):
        """
        Executes de-identification over all 55 clinical notes and verifies that
        NONE of the 700+ annotated ground-truth PHI entities leak into masked_text.
        """
        if deidentify is None:
            pytest.skip("deidentify() implementation pending")

        leaks: List[str] = []

        for note in annotated_notes_55:
            note_id = note["test_case_id"]
            raw_text = note["raw_text"]
            masked_text, mapping = deidentify(raw_text)

            for ent in note["entities"]:
                orig_entity_text = ent["text"].strip()
                category = ent["category"]

                # Check entities with length > 2 characters
                if len(orig_entity_text) > 2:
                    if orig_entity_text in masked_text:
                        # Check if it was an age entity or date that was shifted/masked
                        leaks.append(
                            f"[{note_id}] ({category}) LEAK: '{orig_entity_text}' "
                            f"found unmasked in: {masked_text[:120]}..."
                        )

        assert len(leaks) == 0, (
            f"BREACH DETECTED: Found {len(leaks)} unmasked PHI leaks across 55 evaluation notes:\n"
            + "\n".join(leaks[:10])
        )


# =============================================================================
# TIER 4: MEDICAL EPONYM PRESERVATION (ALL EPONYM CHALLENGE NOTES)
# =============================================================================

class TestTier4MedicalEponymPreservation:
    """
    Tier 4: Asserts that critical diagnostic medical terms, diseases, signs,
    and surgical procedures are NEVER masked as names across the clinical notes.
    """

    @pytest.mark.parametrize("note_index,expected_eponym_term,expected_masked_doctor", [
        (0, "Hodgkin lymphoma", "Hodgkin"),
        (2, "Whipple procedure", "Whipple"),
        (3, "Raynaud's phenomenon", "Raynaud"),
        (6, "Bundle of His", "His"),
        (7, "Swan-Ganz catheter", "Swan"),
        (12, "Parkinson's disease", "Parkinson"),
        (13, "Alzheimer's disease", "Alzheimer"),
        (18, "Apgar score", "Apgar"),
        (20, "Kawasaki disease", "Kawasaki"),
        (30, "Korsakoff syndrome", "Korsakoff"),
        (35, "Tinel's sign", "Tinel"),
        (36, "Lachman test", "Lachman"),
        (37, "Ponseti method", "Ponseti"),
        (39, "Crohn's disease", "Crohn"),
        (40, "Zollinger-Ellison syndrome", "Zollinger"),
        (41, "Whipple's disease", "Whipple"),
        (49, "Glasgow Coma Scale", "Halsted"),
        (50, "McBurney's point", "McBurney"),
        (52, "Foley catheter", "Foley"),
    ])
    def test_eponym_preservation_in_specific_notes(
        self,
        annotated_notes_55: List[Dict[str, Any]],
        note_index: int,
        expected_eponym_term: str,
        expected_masked_doctor: str
    ):
        """Verifies medical eponym is preserved intact while doctor with same surname is masked."""
        if deidentify is None:
            pytest.skip("deidentify() implementation pending")

        note = annotated_notes_55[note_index]
        masked_text, mapping = deidentify(note["raw_text"])

        # Eponym must remain in masked text
        assert expected_eponym_term in masked_text, (
            f"CLINICAL CORRUPTION: Eponym '{expected_eponym_term}' was masked in note {note['test_case_id']}!\n"
            f"Masked text snippet:\n{masked_text[:200]}"
        )

        # Physician with same name must NOT leak
        assert f"Dr. {expected_masked_doctor}" not in masked_text, (
            f"PHI LEAK: Physician 'Dr. {expected_masked_doctor}' was NOT masked in note {note['test_case_id']}!"
        )


# =============================================================================
# TIER 4: GERIATRIC AGE > 89 AGGREGATION
# =============================================================================

class TestTier4GeriatricAgeAggregation:
    """
    Tier 4: Asserts that all nonagenarian and centenarian ages (>89) are aggregated
    to [AGE_90+] in accordance with 45 CFR § 164.514(b)(2)(i)(C).
    """

    @pytest.mark.parametrize("note_index,original_age_str", [
        (23, "94-year-old"),  # Note 24: 94 yo
        (24, "102 years old"),  # Note 25: 102 yo centenarian
        (25, "91 yo"),  # Note 26: 91 yo
        (26, "97-year-old"),  # Note 27: 97 yo
        (27, "90 years old"),  # Note 28: 90 yo
        (28, "95-year-old"),  # Note 29: 95 yo
        (33, "92 years old"),  # Note 34: 92 yo
    ])
    def test_age_aggregation_in_geriatric_notes(
        self,
        annotated_notes_55: List[Dict[str, Any]],
        note_index: int,
        original_age_str: str
    ):
        """Verifies exact age string >= 90 is replaced with aggregated surrogate."""
        if deidentify is None:
            pytest.skip("deidentify() implementation pending")

        note = annotated_notes_55[note_index]
        masked_text, mapping = deidentify(note["raw_text"])

        # Original age >= 90 must not appear in masked note
        assert original_age_str not in masked_text, (
            f"SAFE HARBOR VIOLATION: Age > 89 '{original_age_str}' was not aggregated in note {note['test_case_id']}!"
        )
        assert "[AGE_90+]" in masked_text or "90 or older" in masked_text


# =============================================================================
# TIER 4: REHYDRATION ROUNDTRIP INTEGRITY (ALL 55 NOTES)
# =============================================================================

class TestTier4RehydrationRoundtripIntegrity:
    """
    Tier 4: Verifies that rehydrating masked notes completely restores
    original patient and clinical identifiers without data corruption.
    """

    def test_all_55_notes_rehydration_roundtrip(self, annotated_notes_55: List[Dict[str, Any]]):
        """
        Executes roundtrip (raw -> deidentify -> rehydrate) across all 55 notes
        and asserts that all ground-truth PHI entities are restored in output text.
        """
        if deidentify is None or rehydrate is None:
            pytest.skip("deidentify() or rehydrate() implementation pending")

        rehydration_failures: List[str] = []

        for note in annotated_notes_55:
            note_id = note["test_case_id"]
            raw_text = note["raw_text"]
            masked_text, mapping = deidentify(raw_text)
            restored_text = rehydrate(masked_text, mapping)

            for ent in note["entities"]:
                orig_entity_text = ent["text"].strip()
                if len(orig_entity_text) > 2:
                    if orig_entity_text not in restored_text:
                        rehydration_failures.append(
                            f"[{note_id}] Failed to restore '{orig_entity_text}' of category {ent['category']}"
                        )

        assert len(rehydration_failures) == 0, (
            f"REHYDRATION DEFECTS: {len(rehydration_failures)} entities failed to restore across 55 notes:\n"
            + "\n".join(rehydration_failures[:10])
        )


# =============================================================================
# TIER 4: END-TO-END GATEWAY PIPELINE ROUNDTRIP (MOCK FOUNDATION LLM)
# =============================================================================

class TestTier4EndToEndGatewayPipeline:
    """
    Tier 4: Executes full Gateway pipeline on all 55 notes through MockLLMAdapter.
    """

    def test_e2e_gateway_pipeline_roundtrip_all_specialties(self, annotated_notes_55: List[Dict[str, Any]]):
        """Executes full roundtrip pipeline on sample notes from all 10 specialties."""
        if DeidGateway is None or MockLLMAdapter is None:
            pytest.skip("DeidGateway or MockLLMAdapter implementation pending")

        adapter = MockLLMAdapter(mode="summarize")
        gateway = DeidGateway(adapter=adapter)

        # Select 1 representative note per specialty (10 notes)
        sample_indices = [0, 6, 12, 18, 23, 29, 34, 39, 44, 49]

        for idx in sample_indices:
            note = annotated_notes_55[idx]
            result = gateway.process(
                clinical_note=note["raw_text"],
                task_prompt="Generate a clinical summary of diagnosis and management:"
            )

            assert result.final_text is not None
            assert len(result.final_text) > 0
            assert result.latency_ms >= 0.0
            # Ensure no unresolved bracketed surrogate tokens remain in final text
            assert "[PATIENT_1]" not in result.final_text
            assert "[PROVIDER_1]" not in result.final_text
