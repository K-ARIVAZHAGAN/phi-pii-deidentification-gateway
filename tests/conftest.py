"""
Pytest configuration, path resolution, and shared fixtures for PHI/PII De-Identification Gateway.
Covers all 4 test tiers, the 55-note annotated dataset, and mock foundation LLM infrastructure.
"""

import json
import os
import sys
from typing import Any, Dict, List
import pytest

# Ensure root workspace directory is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

DATASET_PATH = os.path.join(os.path.dirname(__file__), "data", "annotated_clinical_notes_55.json")


@pytest.fixture(scope="session")
def annotated_notes_55() -> List[Dict[str, Any]]:
    """Loads the 55-note gold-standard annotated synthetic clinical corpus."""
    if os.path.exists(DATASET_PATH):
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            notes = json.load(f)
            assert len(notes) == 55, f"Expected 55 notes, found {len(notes)}"
            return notes
    return []


@pytest.fixture
def sample_clinical_note() -> str:
    """Standard multi-identifier clinical consultation note for unit and integration testing."""
    return (
        "PATIENT: Robert Henderson | DOB: 05/14/1958 | MRN: 884-9102-X | SSN: 078-45-9921\n"
        "DATE OF CONSULT: 10/14/2023\n"
        "ATTENDING: Dr. James Parkinson, MD (NPI: 1982736450, Phone: 617-555-0144)\n"
        "FACILITY: St. Luke's Hospital, Boston, MA 02115\n\n"
        "REASON FOR CONSULT: Progressive resting tremor.\n"
        "HISTORY: Mr. Henderson is a 65-year-old male evaluated for Parkinson's disease. "
        "He underwent appendectomy on 09/10/2023. Exam reveals cogwheel rigidity. "
        "Babinski reflex is normal. Initiating carbidopa-levodopa.\n\n"
        "PLAN: Follow-up on 11/25/2023 in 6 weeks.\n"
        "Signed: James Parkinson, MD"
    )


@pytest.fixture
def nonagenarian_clinical_note() -> str:
    """Clinical note featuring patient over 89 years old (Safe Harbor Age Aggregation test)."""
    return (
        "GERIATRIC INTAKE NOTE\n"
        "PATIENT: Florence Nightingale | AGE: 94-year-old female | DOB: 03/12/1929\n"
        "MRN: GER-994820 | DATE: 10/12/2023\n"
        "PHYSICIAN: Dr. Walter Cunningham, MD (NPI: 1492019482)\n"
        "HOSPITAL: Oakwood Senior Living, Evanston, IL 60201\n\n"
        "ASSESSMENT: 94yo nonagenarian admitted for UTI. Celebrated 90th birthday in 2019."
    )


@pytest.fixture
def sample_mapping() -> Dict[str, Any]:
    """Sample session mapping dictionary for rehydration testing."""
    return {
        "version": "1.0.0",
        "document_id": "doc_test_12345",
        "created_at": "2026-08-30T00:00:00Z",
        "date_shift_days": -42,
        "token_to_original": {
            "[PATIENT_1]": "Robert Henderson",
            "[PROVIDER_1]": "Dr. James Parkinson",
            "[HOSPITAL_1]": "St. Luke's Hospital",
            "[DATE_1]": "05/14/1958",
            "[DATE_2]": "10/14/2023",
            "[DATE_3]": "09/10/2023",
            "[MRN_1]": "884-9102-X",
            "[SSN_1]": "078-45-9921",
            "[NPI_1]": "1982736450",
            "[PHONE_1]": "617-555-0144",
            "[CITY_1]": "Boston",
            "[ZIP_1]": "02115",
            "[AGE_90+]": "94",
        },
        "original_to_token": {
            "Robert Henderson": "[PATIENT_1]",
            "Dr. James Parkinson": "[PROVIDER_1]",
            "St. Luke's Hospital": "[HOSPITAL_1]",
            "05/14/1958": "[DATE_1]",
            "10/14/2023": "[DATE_2]",
            "09/10/2023": "[DATE_3]",
            "884-9102-X": "[MRN_1]",
            "078-45-9921": "[SSN_1]",
            "1982736450": "[NPI_1]",
            "617-555-0144": "[PHONE_1]",
            "Boston": "[CITY_1]",
            "02115": "[ZIP_1]",
            "94": "[AGE_90+]",
        },
        "bracket_map": {},
        "date_mappings": [],
        "entities": [],
    }


@pytest.fixture
def mock_llm_response() -> str:
    """Mock foundation LLM response referencing pseudonymised tokens."""
    return (
        "CLINICAL SUMMARY:\n"
        "Patient [PATIENT_1] (DOB: [DATE_1], MRN: [MRN_1]) was evaluated by [PROVIDER_1] "
        "at [HOSPITAL_1] on [DATE_2]. Follow-up appointment scheduled for [DATE_3]."
    )


@pytest.fixture
def eponym_test_pairs() -> List[Dict[str, str]]:
    """Authoritative test cases for medical eponym disambiguation."""
    return [
        {
            "eponym_text": "Patient was diagnosed with Parkinson's disease by Dr. Arthur Parkinson.",
            "protect_term": "Parkinson's disease",
            "mask_term": "Dr. Arthur Parkinson",
            "provider_token": "[PROVIDER_1]"
        },
        {
            "eponym_text": "Dr. Gregory Whipple successfully performed the Whipple procedure.",
            "protect_term": "Whipple procedure",
            "mask_term": "Dr. Gregory Whipple",
            "provider_token": "[PROVIDER_1]"
        },
        {
            "eponym_text": "Dr. Burrill Crohn evaluated the terminal ileum for Crohn's disease.",
            "protect_term": "Crohn's disease",
            "mask_term": "Dr. Burrill Crohn",
            "provider_token": "[PROVIDER_1]"
        },
        {
            "eponym_text": "Babinski reflex was tested by resident Dr. Joseph Babinski.",
            "protect_term": "Babinski reflex",
            "mask_term": "Dr. Joseph Babinski",
            "provider_token": "[PROVIDER_1]"
        }
    ]
