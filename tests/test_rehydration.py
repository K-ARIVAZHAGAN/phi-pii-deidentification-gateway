"""
Tests for Rehydration Engine and Collision / Hallucination Guards (Tiers 1 & 2).
Verifies:
- Callable interface: rehydrate(response, mapping) -> text.
- Perfect inverse mapping of surrogate tokens back to original PHI.
- Fuzzy token mutation tolerance ([ patient 1 ], [provider_1], (DATE_1), unbracketed TOKENS).
- Hallucination resistance (unmapped tokens like [PATIENT_99] preserved without crash).
- Literal bracket preservation ([x] checked, [1] normal labs).
"""

import pytest
from typing import Dict, Any

try:
    from deid_gateway.core.rehydrate import rehydrate
    from deid_gateway.core.collision_guard import CollisionGuard
except ImportError:
    try:
        from deid_gateway.core.collision_guard import CollisionGuard
    except ImportError:
        CollisionGuard = None
    rehydrate = None


# =============================================================================
# TIER 1: FEATURE COVERAGE - REHYDRATION INVERSE MAPPING
# =============================================================================

class TestRehydrationFeatureCoverage:
    """Tier 1: Tests standard rehydration of LLM responses using session mapping."""

    def test_basic_rehydration_roundtrip(self, mock_llm_response: str, sample_mapping: Dict[str, Any]):
        """Verifies standard surrogate tokens are accurately replaced with original values."""
        if rehydrate is None:
            pytest.skip("rehydrate() implementation pending")

        restored = rehydrate(mock_llm_response, sample_mapping)

        # Assert all original PHI values are restored
        assert "Robert Henderson" in restored
        assert "05/14/1958" in restored
        assert "884-9102-X" in restored
        assert "Dr. James Parkinson" in restored
        assert "St. Luke's Hospital" in restored
        assert "10/14/2023" in restored
        assert "09/10/2023" in restored

        # Assert no surrogate tokens remain in restored text
        assert "[PATIENT_1]" not in restored
        assert "[PROVIDER_1]" not in restored
        assert "[HOSPITAL_1]" not in restored

    def test_repeated_surrogate_tokens(self, sample_mapping: Dict[str, Any]):
        """Verifies that multiple occurrences of [PATIENT_1] in different sentences are all restored."""
        if rehydrate is None:
            pytest.skip("rehydrate() implementation pending")

        llm_text = "[PATIENT_1] was admitted. Later, [PATIENT_1] received medication. [PATIENT_1] was discharged."
        restored = rehydrate(llm_text, sample_mapping)

        assert restored.count("Robert Henderson") == 3
        assert "[PATIENT_1]" not in restored

    def test_response_with_no_tokens(self, sample_mapping: Dict[str, Any]):
        """Verifies responses containing no surrogate tokens are returned unchanged."""
        if rehydrate is None:
            pytest.skip("rehydrate() implementation pending")

        plain_text = "The patient has no acute distress. Vital signs are stable. Continue current medications."
        restored = rehydrate(plain_text, sample_mapping)
        assert restored == plain_text


# =============================================================================
# TIER 1 & 2: COLLISION GUARD & FUZZY TOKEN NORMALIZATION
# =============================================================================

class TestCollisionGuardAndFuzzyNormalization:
    """Tier 1 & 2: Tests handling of LLM whitespace mutations, bracket stripping, and casing."""

    def test_fuzzy_casing_and_spacing_normalization(self):
        """Verifies fuzzy normalizer unifies [ patient 1 ], [provider_1], [DATE 2], (PATIENT_1)."""
        if CollisionGuard is None:
            pytest.skip("CollisionGuard implementation pending")

        mutated_llm_output = (
            "Assessment for [ patient 1 ] conducted by [provider_1] on [DATE 1]. "
            "Follow-up scheduled at [ hospital 1 ] on (DATE_2)."
        )

        normalized = CollisionGuard.normalize_fuzzy_tokens(mutated_llm_output)

        assert "[PATIENT_1]" in normalized
        assert "[PROVIDER_1]" in normalized
        assert "[DATE_1]" in normalized
        assert "[HOSPITAL_1]" in normalized
        assert "[DATE_2]" in normalized

    def test_unbracketed_token_wrapping(self):
        """Verifies unbracketed surrogate tokens output by foundation LLM are re-bracketed."""
        if CollisionGuard is None:
            pytest.skip("CollisionGuard implementation pending")

        dropped_bracket_text = "Patient PATIENT_1 was evaluated by PROVIDER_1 on DATE_1."
        normalized = CollisionGuard.normalize_fuzzy_tokens(dropped_bracket_text)

        assert "[PATIENT_1]" in normalized
        assert "[PROVIDER_1]" in normalized
        assert "[DATE_1]" in normalized

    def test_rehydrate_with_mutated_llm_syntax(self, sample_mapping: Dict[str, Any]):
        """Verifies rehydrate successfully handles mutated LLM output."""
        if rehydrate is None:
            pytest.skip("rehydrate() implementation pending")

        mutated_text = "Summary: [ patient 1 ] was seen by [ provider 1 ] on [date_2]."
        restored = rehydrate(mutated_text, sample_mapping)

        assert "Robert Henderson" in restored
        assert "Dr. James Parkinson" in restored
        assert "10/14/2023" in restored


# =============================================================================
# TIER 2: HALLUCINATION AND LITERAL BRACKET DEFENSE
# =============================================================================

class TestHallucinationAndLiteralBrackets:
    """Tier 2: Tests hallucinated surrogate token immunity and non-PHI literal bracket preservation."""

    def test_hallucinated_surrogate_tokens_do_not_crash(self, sample_mapping: Dict[str, Any]):
        """
        Hallucination Guard: If LLM generates [PATIENT_99] or [PROVIDER_X] not in mapping,
        the engine must preserve the text safely without raising KeyError or crashing.
        """
        if rehydrate is None:
            pytest.skip("rehydrate() implementation pending")

        hallucinated_response = (
            "[PATIENT_1] had a consultation. Also recommend follow-up for [PATIENT_99] "
            "and [PROVIDER_X] in room [ROOM_4]."
        )

        restored = rehydrate(hallucinated_response, sample_mapping)

        # Valid token is rehydrated
        assert "Robert Henderson" in restored
        assert "[PATIENT_1]" not in restored

        # Hallucinated tokens are preserved safely
        assert "[PATIENT_99]" in restored
        assert "[PROVIDER_X]" in restored

    def test_literal_brackets_in_clinical_notes_are_preserved(self):
        """
        Literal Collision Guard: Non-PHI bracketed expressions like '[x]', '[1]', '[Normal]'
        must not be corrupted or collided with surrogate tokens.
        """
        if CollisionGuard is None:
            pytest.skip("CollisionGuard implementation pending")

        clinical_note = (
            "Physical Exam:\n"
            "Abdomen: [x] soft, [x] non-tender, [ ] distended.\n"
            "Labs: [1] WBC 7.4 [Normal], [2] Platelets 250k [Normal].\n"
            "Status: [Pending] pathology review."
        )

        # Step 1: Escape
        escaped_text, bracket_map = CollisionGuard.escape_literal_brackets(clinical_note)
        assert "[" not in escaped_text  # Brackets replaced with unicode escape characters

        # Step 2: Unescape
        restored_text = CollisionGuard.unescape_literal_brackets(escaped_text, bracket_map)
        assert restored_text == clinical_note, "Literal non-PHI brackets were corrupted during roundtrip!"

    def test_empty_mapping_and_empty_response(self):
        """Boundary: Handling empty inputs gracefully."""
        if rehydrate is None:
            pytest.skip("rehydrate() implementation pending")

        assert rehydrate("", {}) == ""
        assert rehydrate("Some text without tokens", {}) == "Some text without tokens"
        assert rehydrate("[PATIENT_1]", {}) == "[PATIENT_1]"
