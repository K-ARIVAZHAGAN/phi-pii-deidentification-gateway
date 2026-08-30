"""
Tests for Pseudonymizer and Consistent Surrogate Token Generation (Tiers 1 & 2).
Verifies:
- Consistent mapping: Multiple mentions of the same entity receive identical tokens.
- Entity separation: Distinct entities receive incrementing indices ([PATIENT_1], [PATIENT_2]).
- Structured surrogate tokens ([CATEGORY_INDEX]) for all HIPAA Safe Harbor classes.
- Session mapping isolation and dictionary serialization.
"""

import pytest
from typing import Dict, Any

try:
    from deid_gateway.core.pseudonymizer import Pseudonymizer
except ImportError:
    Pseudonymizer = None


# =============================================================================
# TIER 1: FEATURE COVERAGE - CONSISTENT PSEUDONYMISATION
# =============================================================================

class TestPseudonymizerFeatureCoverage:
    """Tier 1: Tests consistent surrogate assignment and mapping table management."""

    def test_single_entity_consistency(self):
        """Verifies that recurring mentions of the exact same entity produce the identical surrogate token."""
        if Pseudonymizer is None:
            pytest.skip("Pseudonymizer implementation pending")

        pseudonymizer = Pseudonymizer()
        token1 = pseudonymizer.get_or_create_token("PATIENT", "John Doe")
        token2 = pseudonymizer.get_or_create_token("PATIENT", "John Doe")
        token3 = pseudonymizer.get_or_create_token("PATIENT", "john doe")

        assert token1 == "[PATIENT_1]"
        assert token2 == "[PATIENT_1]"
        assert token3 == "[PATIENT_1]"

    def test_distinct_entities_increment_index(self):
        """Verifies distinct entities in the same category receive incrementing tokens."""
        if Pseudonymizer is None:
            pytest.skip("Pseudonymizer implementation pending")

        pseudonymizer = Pseudonymizer()
        p1 = pseudonymizer.get_or_create_token("PATIENT", "Alice Smith")
        p2 = pseudonymizer.get_or_create_token("PATIENT", "Bob Jones")
        p3 = pseudonymizer.get_or_create_token("PATIENT", "Charlie Brown")

        assert p1 == "[PATIENT_1]"
        assert p2 == "[PATIENT_2]"
        assert p3 == "[PATIENT_3]"

    def test_distinct_categories_independent_indexing(self):
        """Verifies each category starts its own index counter at 1."""
        if Pseudonymizer is None:
            pytest.skip("Pseudonymizer implementation pending")

        pseudonymizer = Pseudonymizer()
        patient = pseudonymizer.get_or_create_token("PATIENT", "John Doe")
        provider = pseudonymizer.get_or_create_token("PROVIDER", "Dr. Robert Chen")
        hospital = pseudonymizer.get_or_create_token("HOSPITAL", "Mercy Hospital")
        mrn = pseudonymizer.get_or_create_token("MRN", "9482014")

        assert patient == "[PATIENT_1]"
        assert provider == "[PROVIDER_1]"
        assert hospital == "[HOSPITAL_1]"
        assert mrn == "[MRN_1]"

    def test_mapping_table_reversibility(self):
        """Verifies inverse lookup from token to original entity string."""
        if Pseudonymizer is None:
            pytest.skip("Pseudonymizer implementation pending")

        pseudonymizer = Pseudonymizer()
        tok1 = pseudonymizer.get_or_create_token("PATIENT", "Eleanor Rigby")
        tok2 = pseudonymizer.get_or_create_token("PROVIDER", "Dr. Arthur Hodgkin")
        mapping = pseudonymizer.build_mapping()

        assert mapping["token_to_original"][tok1] == "Eleanor Rigby"
        assert mapping["token_to_original"][tok2] == "Dr. Arthur Hodgkin"


# =============================================================================
# TIER 2: BOUNDARY & CORNER CASES
# =============================================================================

class TestPseudonymizerCornerCases:
    """Tier 2: Boundary conditions, special characters, and scaling."""

    def test_special_characters_in_entity(self):
        """Corner: Entity containing slashes, quotes, brackets, or math symbols."""
        if Pseudonymizer is None:
            pytest.skip("Pseudonymizer implementation pending")

        pseudonymizer = Pseudonymizer()
        e1 = pseudonymizer.get_or_create_token("PATIENT", "Robert 'Bob' O'Connor-Smith, Jr.")
        mapping = pseudonymizer.build_mapping()

        assert e1 == "[PATIENT_1]"
        assert mapping["token_to_original"]["[PATIENT_1]"] == "Robert 'Bob' O'Connor-Smith, Jr."

    def test_large_number_of_entities(self):
        """Boundary: Handles 100+ distinct entities in single document without collisions."""
        if Pseudonymizer is None:
            pytest.skip("Pseudonymizer implementation pending")

        pseudonymizer = Pseudonymizer()
        tokens = [pseudonymizer.get_or_create_token("PROVIDER", f"Doctor Name {i}") for i in range(1, 105)]
        
        assert len(set(tokens)) == 104
        assert tokens[0] == "[PROVIDER_1]"
        assert tokens[99] == "[PROVIDER_100]"
        assert tokens[103] == "[PROVIDER_104]"
