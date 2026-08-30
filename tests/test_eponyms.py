"""
Tests for Clinical Ambiguity and Medical Eponym Disambiguation Engine (Tiers 1 & 2).
Verifies:
- Tri-Filter Architecture (Honorific anchors, Lexical suffix rule, Ontology whitelist).
- Medical eponym preservation (Parkinson's, Crohn's, Whipple, Bell's, Hodgkin, Babinski, etc.).
- Strict masking of real healthcare provider and patient names sharing eponym surnames.
- Filtering of candidate spans without false positives on clinical terms.
"""

import pytest
from typing import Dict, List

try:
    from deid_gateway.core.eponyms import EponymDisambiguator
    from deid_gateway.core.deidentify import deidentify
except ImportError:
    EponymDisambiguator = None
    deidentify = None


# =============================================================================
# TIER 1: FEATURE COVERAGE - EPONYM DISAMBIGUATION RULES
# =============================================================================

class TestEponymTriFilterRules:
    """Tier 1: Tests the individual rules of the Tri-Filter Disambiguation Engine."""

    def test_rule_1_honorific_anchor_forces_phi_masking(self):
        """Rule 1: If preceded by 'Dr.', 'Attending:', or succeeded by ', MD', it is PHI (MUST MASK)."""
        if EponymDisambiguator is None:
            pytest.skip("EponymDisambiguator implementation pending")
        disambiguator = EponymDisambiguator()

        # Doctor with surname 'Parkinson'
        is_ep1 = disambiguator.is_eponym(
            candidate_text="Parkinson",
            context_before="The patient was examined by Dr. ",
            context_after=" in the clinic."
        )
        assert is_ep1 is False, "Dr. Parkinson was incorrectly classified as an eponym instead of PHI!"

        # Doctor with surname 'Whipple'
        is_ep2 = disambiguator.is_eponym(
            candidate_text="Whipple",
            context_before="Operative procedure performed by Attending: ",
            context_after=" on Monday."
        )
        assert is_ep2 is False, "Attending Whipple was incorrectly classified as an eponym instead of PHI!"

    def test_rule_2_lexical_suffix_forces_eponym_protection(self):
        """Rule 2: If candidate is followed by 'disease', 'procedure', 'sign', etc., PROTECT it."""
        if EponymDisambiguator is None:
            pytest.skip("EponymDisambiguator implementation pending")
        disambiguator = EponymDisambiguator()

        is_ep1 = disambiguator.is_eponym(
            candidate_text="Parkinson's",
            context_before="Patient has a 5-year history of ",
            context_after=" disease with resting tremor."
        )
        assert is_ep1 is True, "Parkinson's disease was not protected as an eponym!"

        is_ep2 = disambiguator.is_eponym(
            candidate_text="Whipple",
            context_before="Patient scheduled for a pancreaticoduodenectomy (",
            context_after=" procedure) tomorrow morning."
        )
        assert is_ep2 is True, "Whipple procedure was not protected as an eponym!"

    def test_rule_3_ontology_whitelist_lookup(self):
        """Rule 3: Multi-word verified medical eponyms in whitelist are protected."""
        if EponymDisambiguator is None:
            pytest.skip("EponymDisambiguator implementation pending")
        disambiguator = EponymDisambiguator()

        assert disambiguator.is_eponym("Circle of Willis", "CTA revealed aneurysm in the ", " bifurcations.") is True
        assert disambiguator.is_eponym("Guillain-Barré", "Patient recovering from ", " syndrome post-IVIG.") is True


# =============================================================================
# TIER 1 & 2: COMPREHENSIVE CLINICAL DISCIPLINE EPONYM TEST MATRIX
# =============================================================================

class TestClinicalEponymMatrix:
    """Tier 1 & 2: Cross-discipline matrix of classic eponym vs provider/patient pairs."""

    @pytest.mark.parametrize("candidate_text,context_before,context_after,expected_is_eponym,description", [
        # Neurology
        ("Parkinson's", "Diagnosed with ", " disease.", True, "Neurology - Parkinson's disease"),
        ("Parkinson", "Examined by Dr. ", " yesterday.", False, "Neurology - Dr. Parkinson"),
        ("Alzheimer's", "Progression of ", " dementia.", True, "Neurology - Alzheimer's dementia"),
        ("Bell's", "Patient presented with acute ", " palsy.", True, "Neurology - Bell's palsy"),
        ("Babinski", "Plantar response showed positive ", " sign.", True, "Neurology - Babinski sign"),
        ("Babinski", "Resident Dr. ", " checked reflexes.", False, "Neurology - Dr. Babinski"),
        
        # Gastroenterology & Oncology
        ("Crohn's", "Prescribed infliximab for moderate ", " disease.", True, "Gastroenterology - Crohn's disease"),
        ("Crohn", "Attending: Dr. ", ", Chief of GI.", False, "Gastroenterology - Dr. Crohn"),
        ("Whipple", "Successfully completed the ", " procedure.", True, "Surg Onc - Whipple procedure"),
        ("Whipple", "Primary surgeon was Dr. ", ".", False, "Surg Onc - Dr. Whipple"),
        ("Hodgkin", "Biopsy diagnostic of classic ", " lymphoma.", True, "Hematology - Hodgkin lymphoma"),
        ("Barrett's", "EGD revealed short-segment ", " esophagus.", True, "Gastroenterology - Barrett's esophagus"),
        
        # Surgery, Devices & Signs
        ("Foley", "Inserted a 16-Fr ", " catheter to gravity.", True, "Urology - Foley catheter"),
        ("Foley", "Dictated by Dr. ", ", Urologist.", False, "Urology - Dr. Foley"),
        ("Swan-Ganz", "Placed a ", " catheter for hemodynamics.", True, "Cardiology - Swan-Ganz catheter"),
        ("McBurney's", "Tenderness elicited at ", " point.", True, "Emergency - McBurney's point"),
        ("Murphy's", "Right upper quadrant exam showed positive ", " sign.", True, "Emergency - Murphy's sign"),
        ("Apgar", "Infant delivered with ", " score of 9 at 5 minutes.", True, "Pediatrics - Apgar score"),
        ("Glasgow", "Patient has a ", " Coma Scale of 15.", True, "Trauma - Glasgow Coma Scale"),
    ])
    def test_eponym_vs_provider_disambiguation(
        self,
        candidate_text: str,
        context_before: str,
        context_after: str,
        expected_is_eponym: bool,
        description: str
    ):
        """Tier 1 & 2: Tests every paired clinical scenario for exact classification accuracy."""
        if EponymDisambiguator is None:
            pytest.skip("EponymDisambiguator implementation pending")
        disambiguator = EponymDisambiguator()
        result = disambiguator.is_eponym(candidate_text, context_before, context_after)
        assert result == expected_is_eponym, (
            f"Failed on [{description}]: expected is_eponym={expected_is_eponym}, got {result} "
            f"for text='{context_before}[{candidate_text}]{context_after}'"
        )
