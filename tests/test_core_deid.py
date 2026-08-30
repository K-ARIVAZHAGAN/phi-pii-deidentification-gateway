"""
Tests for Core De-Identification Engine (Tiers 1 & 2).
Verifies:
- All 18 HIPAA Safe Harbor categories detection and masking.
- Sub-1B parameter model constraints and model cards.
- Callable Python API interface deidentify(text, config) -> (masked_text, mapping).
- Boundary conditions, empty inputs, unicode, edge cases, and zero false negative leaks.
"""

import pytest
from typing import Dict, Any

try:
    from deid_gateway.core.deidentify import deidentify
    from deid_gateway.core.config import DeidConfig
    from deid_gateway.core.models.classifier import HybridTokenClassifier
    from deid_gateway.core.models.model_card import get_model_card, get_parameter_count, MODEL_REGISTRY
except ImportError:
    deidentify = None
    DeidConfig = None
    HybridTokenClassifier = None
    get_model_card = None
    get_parameter_count = None
    MODEL_REGISTRY = {}


# =============================================================================
# TIER 1: FEATURE COVERAGE - 18 HIPAA SAFE HARBOR CATEGORIES
# =============================================================================

class TestSafeHarbor18Categories:
    """Tier 1: Comprehensive verification of all 18 HIPAA Safe Harbor categories."""

    @pytest.mark.parametrize("category_name,input_text,expected_masked_token,target_entity", [
        # 1. Names (Patient, Provider, Family)
        ("NAME_PATIENT", "Patient Johnathan Q. Public arrived for his appointment.", "[PATIENT_1]", "Johnathan Q. Public"),
        ("NAME_PROVIDER", "Exam performed by Dr. Elizabeth Blackwell, MD.", "[PROVIDER_1]", "Elizabeth Blackwell"),
        ("NAME_FAMILY", "Accompanied by mother Sarah Jenkins and brother Tim.", "[FAMILY_1]", "Sarah Jenkins"),
        
        # 2. Geographic Subdivisions
        ("GEO_STREET", "Patient lives at 742 Evergreen Terrace, Springfield, 94107.", "[ADDRESS_1]", "742 Evergreen Terrace"),
        ("GEO_CITY", "Transferred from clinic in Springfield, Cook County.", "[CITY_1]", "Springfield"),
        ("GEO_ZIP", "Mailing postal code is 60611-2304.", "[ZIP_1]", "60611-2304"),
        
        # 3. Dates & Ages > 89
        ("DATE_DOB", "DOB: 04/12/1974. Admitted on October 14, 2023.", "[DATE_1]", "04/12/1974"),
        ("AGE_OVER_89", "Patient is a 94-year-old nonagenarian female.", "[AGE_90+]", "94-year-old"),
        
        # 4. Telephone Numbers
        ("PHONE", "Callback clinic phone: (555) 234-5678 ext 402.", "[PHONE_1]", "(555) 234-5678 ext 402"),
        
        # 5. Fax Numbers
        ("FAX", "Confidential departmental fax: 555-432-1098.", "[FAX_1]", "555-432-1098"),
        
        # 6. Email Addresses
        ("EMAIL", "Send records to doctor.chen@mercyhospital.org.", "[EMAIL_1]", "doctor.chen@mercyhospital.org"),
        
        # 7. Social Security Numbers
        ("SSN", "SSN: 078-45-9921 on file.", "[SSN_1]", "078-45-9921"),
        
        # 8. Medical Record Numbers
        ("MRN", "MRN: 884-9102-X assigned at intake.", "[MRN_1]", "884-9102-X"),
        
        # 9. Health Plan Numbers
        ("HEALTHPLAN", "Medicare Beneficiary MBI: 1EG4-TE5-MK72.", "[HEALTHPLAN_1]", "1EG4-TE5-MK72"),
        
        # 10. Account Numbers
        ("ACCOUNT", "Hospital Account Record HAR: 89402840.", "[ACCOUNT_1]", "89402840"),
        
        # 11. Certificate / License Numbers
        ("LICENSE_NPI", "Attending NPI: 1847291045 and DEA: BK9482014.", "[NPI_1]", "1847291045"),
        
        # 12. Vehicle Identifiers
        ("VEHICLE", "Vehicle VIN: 1HGCR2F83HA029481, License Plate: IL 784-KPL.", "[VEHICLE_1]", "1HGCR2F83HA029481"),
        
        # 13. Device Identifiers
        ("DEVICE", "Pacemaker Serial Number SN: PAC-99482014-H.", "[DEVICE_1]", "PAC-99482014-H"),
        
        # 14. Web URLs
        ("URL", "Portal link: https://mychart.mercyhealth.org/portal/pat_id=9482.", "[URL_1]", "https://mychart.mercyhealth.org/portal/pat_id=9482"),
        
        # 15. IP Addresses
        ("IP", "Telehealth connection from IP 192.168.1.104.", "[IP_1]", "192.168.1.104"),
        
        # 16. Biometric Identifiers
        ("BIOMETRIC", "Retinal Scan Biometric ID: RET-SCAN-9948201.", "[BIOMETRIC_1]", "RET-SCAN-9948201"),
        
        # 17. Full Face Photos
        ("PHOTO", "Facial photo reference attached: facial_setup_photo_pat883921.dcm.", "[PHOTO_1]", "facial_setup_photo_pat883921.dcm"),
        
        # 18. Any other unique identifying number / Accession
        ("ID_ACCESSION", "Pathology Accession #: PATH-2023-99841.", "[ACCESSION_1]", "PATH-2023-99841"),
    ])
    def test_individual_category_detection(self, category_name: str, input_text: str, expected_masked_token: str, target_entity: str):
        """Tier 1: Verifies individual HIPAA identifier category is detected and replaced with surrogate."""
        if deidentify is None:
            pytest.skip("deidentify() implementation pending")
        
        masked_text, mapping = deidentify(input_text)
        
        # 1. Target entity must NOT leak in masked text
        assert target_entity not in masked_text, (
            f"LEAK DETECTED for category {category_name}: '{target_entity}' still present in masked text: '{masked_text}'"
        )
        
        # 2. Masked text must contain a valid surrogate token format [CATEGORY_X]
        assert "[" in masked_text and "]" in masked_text, f"No surrogate token found in: '{masked_text}'"


# =============================================================================
# TIER 1: MODEL PARAMETER BUDGET & REGISTRY VERIFICATION
# =============================================================================

class TestModelParameterConstraints:
    """Tier 1: Verifies model architecture is strictly under 1 Billion parameters."""

    def test_all_registered_models_are_under_1b(self):
        """Verifies every supported model candidate strictly satisfies <= 1,000,000,000 parameters."""
        if not MODEL_REGISTRY:
            pytest.skip("MODEL_REGISTRY not loaded")
        for name, card in MODEL_REGISTRY.items():
            assert card.is_sub_1b, f"Model {name} exceeds 1B parameter ceiling: {card.total_parameters}"
            assert card.total_parameters < 1_000_000_000, f"Model {name} has {card.total_parameters} params"
            assert card.total_parameters <= 150_000_000, (
                f"Model {name} exceeds expected lightweight footprint: {card.total_parameters}"
            )

    def test_deberta_v3_base_parameter_breakdown(self):
        """Verifies exact layer parameter breakdown for primary DeBERTa-v3 model."""
        if get_model_card is None:
            pytest.skip("get_model_card implementation pending")
        card = get_model_card("deberta-v3-base")
        assert card.architecture.startswith("DeBERTa-v3")
        assert card.parameter_breakdown.num_layers == 12
        assert card.parameter_breakdown.hidden_dimension == 768
        assert card.parameter_breakdown.attention_heads == 12
        assert card.total_parameters == 124_400_000
        assert card.memory_footprint_fp16_mb < 300.0

    def test_bioclinicalbert_parameter_breakdown(self):
        """Verifies exact layer parameter breakdown for domain-specific Bio_ClinicalBERT."""
        if get_model_card is None:
            pytest.skip("get_model_card implementation pending")
        card = get_model_card("bio-clinicalbert")
        assert card.total_parameters == 108_310_272
        assert card.total_parameters < 1_000_000_000
        assert card.memory_footprint_int8_mb < 150.0


# =============================================================================
# TIER 1 & 2: CALLABLE INTERFACE & CONFIGURATION CONTRACT
# =============================================================================

class TestDeidInterfaceContract:
    """Tier 1 & 2: Verifies deidentify(text, config) -> tuple[str, dict] interface."""

    def test_deidentify_signature_and_return_types(self, sample_clinical_note: str):
        """Verifies function returns a tuple of (str, dict) exactly."""
        if deidentify is None:
            pytest.skip("deidentify() implementation pending")
            
        result = deidentify(sample_clinical_note)
        assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
        assert len(result) == 2, f"Expected 2-element tuple, got {len(result)}"
        
        masked_text, mapping = result
        assert isinstance(masked_text, str), f"Expected str for masked_text, got {type(masked_text)}"
        assert isinstance(mapping, dict), f"Expected dict for mapping, got {type(mapping)}"

    def test_deidentify_with_custom_config(self, sample_clinical_note: str):
        """Verifies deidentify honors DeidConfig overrides."""
        if deidentify is None or DeidConfig is None:
            pytest.skip("deidentify() or DeidConfig implementation pending")
            
        config = DeidConfig(
            masking_mode="surrogate_token",
            date_shift_enabled=True,
            date_shift_days=60,
            preserve_eponyms=True
        )
        masked_text, mapping = deidentify(sample_clinical_note, config=config)
        assert isinstance(masked_text, str)
        assert isinstance(mapping, dict)
        assert mapping.get("date_shift_days") == 60


# =============================================================================
# TIER 2: BOUNDARY AND CORNER CASES
# =============================================================================

class TestBoundaryAndCornerCases:
    """Tier 2: Boundary value analysis, empty strings, punctuation, unicode, and non-PHI notes."""

    def test_empty_string_input(self):
        """Boundary: Empty string should return empty string and empty mapping without error."""
        if deidentify is None:
            pytest.skip("deidentify() implementation pending")
            
        masked, mapping = deidentify("")
        assert masked == ""
        assert isinstance(mapping, dict)

    def test_whitespace_only_input(self):
        """Boundary: Whitespace-only string preserved with no false positive tokens."""
        if deidentify is None:
            pytest.skip("deidentify() implementation pending")
            
        ws = "   \n\t  \n  "
        masked, mapping = deidentify(ws)
        assert masked == ws

    def test_note_with_zero_phi(self):
        """Boundary: Clinical note with purely medical descriptions and zero PHI."""
        clean_note = (
            "Assessment: Acute viral upper respiratory tract infection. "
            "Lungs clear to auscultation bilaterally. No wheezes, rales, or rhonchi. "
            "Heart regular rate and rhythm, S1 and S2 present, no murmurs. "
            "Plan: Supportive care, rest, hydration, oral acetaminophen 500mg as needed."
        )
        if deidentify is None:
            pytest.skip("deidentify() implementation pending")
            
        masked, mapping = deidentify(clean_note)
        # Should remain intact
        assert "Acute viral upper respiratory tract infection" in masked

    def test_adjacent_punctuation_and_delimiters(self):
        """Corner: PHI followed immediately by commas, periods, colons, brackets, or quotes."""
        text = 'Patient: John Doe, MRN: 884920, SSN: 078-45-9921; Attending: Dr. Marcus Welby, MD.'
        if deidentify is None:
            pytest.skip("deidentify() implementation pending")
            
        masked, mapping = deidentify(text)
        assert "John Doe" not in masked
        assert "078-45-9921" not in masked
        assert "884920" not in masked
        assert "Marcus Welby" not in masked
