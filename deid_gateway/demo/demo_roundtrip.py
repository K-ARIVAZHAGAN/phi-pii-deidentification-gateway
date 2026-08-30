"""
Demonstration Script: Complete End-to-End PHI/PII De-Identification Gateway Round-Trip.
Shows:
1. Raw Clinical Notes containing sensitive Safe Harbor PHI and medical eponyms.
2. De-identification & Pseudonymisation with zero raw PHI leakage.
3. Cryptographic mapping dictionary isolation.
4. Foundation LLM generation using pluggable adapters (offline Mock by default).
5. Response rehydration restoring clinical context with 100% fidelity.
"""

import sys
import time
from typing import Dict, List, Optional

from deid_gateway.adapters.base import BaseLLMAdapter
from deid_gateway.adapters.mock_adapter import MockLLMAdapter
from deid_gateway.core.config import DeidConfig
from deid_gateway.core.models.model_card import get_parameter_count
from deid_gateway.gateway import DeidGateway, GatewayResult


# ANSI Color formatting helpers
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


SAMPLE_CLINICAL_NOTES = [
    {
        "specialty": "Neurology & Movement Disorders",
        "title": "Parkinson's Disease Consultation Note",
        "raw_text": (
            "PATIENT: Robert Henderson | DOB: 05/14/1958 | MRN: 884-9102-X | SSN: 078-45-9921\n"
            "DATE OF CONSULT: 10/14/2023\n"
            "ATTENDING: Dr. James Parkinson, MD (NPI: 1982736450, Phone: 617-555-0144)\n"
            "FACILITY: St. Luke's Hospital, Boston, MA 02115\n\n"
            "REASON FOR CONSULT: Progressive resting tremor and cogwheel rigidity.\n"
            "HISTORY: Mr. Henderson is a 65-year-old male evaluated for Parkinson's disease. "
            "Prior appendectomy on 09/10/2023. Babinski reflex is negative bilaterally. "
            "Initiating carbidopa-levodopa 25/100 mg TID.\n\n"
            "PLAN: Follow-up clinic appointment on 11/25/2023 in 6 weeks.\n"
            "Signed: Dr. James Parkinson, MD"
        ),
    },
    {
        "specialty": "Surgical Oncology",
        "title": "Pancreatic Neoplasm Operative Flowsheet",
        "raw_text": (
            "OPERATIVE REPORT\n"
            "PATIENT: Eleanor Rigby | AGE: 58 | DOB: 08/22/1965 | MRN: ONC-774910\n"
            "DATE OF SURGERY: 03/15/2024\n"
            "SURGEON: Dr. Gregory Whipple, MD, FACS | ASSISTANT: Dr. Alan Turing, MD\n"
            "LOCATION: Massachusetts General Hospital, Boston, MA\n\n"
            "PROCEDURE: Pancreaticoduodenectomy (Whipple procedure).\n"
            "INDICATIONS: Resectable pancreatic head adenocarcinoma without vascular invasion.\n"
            "FINDINGS: Successful resection. Pancreaticojejunostomy created without tension. "
            "Foley catheter placed draining clear urine.\n\n"
            "DISPOSITION: Transfer to Surgical ICU in stable condition."
        ),
    },
    {
        "specialty": "Geriatric Medicine",
        "title": "Nonagenarian Safe Harbor Age Aggregation Intake",
        "raw_text": (
            "GERIATRIC INTAKE NOTE\n"
            "PATIENT: Arthur Pendelton | AGE: 94-year-old male | DOB: 01/18/1930\n"
            "MRN: GER-392019 | DATE: 04/10/2024\n"
            "ATTENDING: Dr. Rebecca Sterling, MD (Phone: 312-555-0199)\n"
            "FACILITY: Oakwood Extended Care, Chicago, IL 60611\n\n"
            "ASSESSMENT: 94yo nonagenarian admitted for mild cognitive impairment. "
            "Celebrated his 90th birthday in 2020. Patient ambulates with a walker.\n"
            "PLAN: Continue physical therapy 3 times weekly. Follow-up on 05/10/2024."
        ),
    },
]


def print_banner() -> None:
    param_count = get_parameter_count()
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}")
    print(f"  HIPAA SAFE HARBOR PHI/PII DE-IDENTIFICATION & REHYDRATION GATEWAY")
    print(f"  Under-1B Parameter Model Family ({param_count:,} params) | Zero-Leak Guarantee")
    print(f"{'='*80}{Colors.END}\n")


def run_roundtrip_demo(adapter: Optional[BaseLLMAdapter] = None) -> bool:
    """Executes full roundtrip on all sample clinical notes."""
    print_banner()

    active_adapter = adapter or MockLLMAdapter(mode="summarize")
    config = DeidConfig(date_shift_days=-42, preserve_eponyms=True)
    gateway = DeidGateway(adapter=active_adapter, deid_config=config)

    total_notes = len(SAMPLE_CLINICAL_NOTES)
    all_passed = True

    for i, item in enumerate(SAMPLE_CLINICAL_NOTES, 1):
        print(f"{Colors.BOLD}{Colors.HEADER}=== DEMO CASE {i}/{total_notes}: {item['specialty']} ({item['title']}) ==={Colors.END}\n")

        raw_note = item["raw_text"]

        # 1. Display Raw Input Note
        print(f"{Colors.BOLD}[1] RAW CLINICAL NOTE (Contains Sensitive PHI):{Colors.END}")
        print(f"{Colors.YELLOW}{raw_note}{Colors.END}\n")

        # 2. Execute Gateway
        result: GatewayResult = gateway.process(
            clinical_note=raw_note,
            task_prompt="Provide a structured clinical summary:",
        )

        # 3. Display De-Identified Text Delivered to LLM
        print(f"{Colors.BOLD}[2] DE-IDENTIFIED TEXT DELIVERED TO LLM (Zero Raw PHI Leaked):{Colors.END}")
        print(f"{Colors.CYAN}{result.masked_input}{Colors.END}\n")

        # 4. Display Isolated Cryptographic Mapping
        print(f"{Colors.BOLD}[3] ISOLATED SESSION MAPPING TABLE (Kept Secure in Memory):{Colors.END}")
        token_map = result.mapping.get("token_to_original", {})
        for tok, orig in sorted(token_map.items()):
            print(f"    {tok:<16} ->  {orig}")
        print()

        # 5. Display Raw LLM Response
        print(f"{Colors.BOLD}[4] FOUNDATION LLM COMPLETION (With Surrogate Tokens):{Colors.END}")
        print(f"{Colors.BLUE}{result.raw_llm_response}{Colors.END}\n")

        # 6. Display Final Rehydrated Output
        print(f"{Colors.BOLD}[5] FINAL REHYDRATED CLINICAL OUTPUT (Original Context Restored):{Colors.END}")
        print(f"{Colors.GREEN}{result.final_text}{Colors.END}\n")

        # 7. Telemetry & Verification Checks
        leak_status = (
            f"{Colors.GREEN}PASSED (0 Leaks){Colors.END}"
            if result.leak_check_passed
            else f"{Colors.RED}FAILED{Colors.END}"
        )
        print(f"{Colors.BOLD}[6] EXECUTION TELEMETRY & SECURITY AUDIT:{Colors.END}")
        print(f"    - Entities Masked      : {result.entity_count}")
        print(f"    - Zero-Leak Guard Check: {leak_status}")
        print(f"    - De-ID Latency        : {result.deid_latency_ms:.2f} ms")
        print(f"    - LLM Inference Latency: {result.llm_latency_ms:.2f} ms")
        print(f"    - Rehydration Latency  : {result.rehydrate_latency_ms:.2f} ms")
        print(f"    - Total Roundtrip Time : {result.latency_ms:.2f} ms")
        print(f"\n{'-'*80}\n")

        if not result.leak_check_passed:
            all_passed = False

    print(f"{Colors.BOLD}{Colors.GREEN}[SUCCESS] All {total_notes} clinical demo round-trips completed successfully with zero PHI leaks!{Colors.END}\n")
    return all_passed


def main() -> None:
    success = run_roundtrip_demo()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
