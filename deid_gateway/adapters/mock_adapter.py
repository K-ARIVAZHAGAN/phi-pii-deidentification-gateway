"""
Offline Deterministic Mock Foundation LLM Adapter.
Provides hermetic clinical summarization, clinical question answering,
and structured entity/slot extraction while faithfully preserving surrogate tokens.
"""

import asyncio
import re
from typing import Any, Dict, List, Optional

from deid_gateway.adapters.base import BaseLLMAdapter


class MockLLMAdapter(BaseLLMAdapter):
    """
    Offline deterministic mock adapter for testing, benchmarking, and CI without external API calls.
    
    Supports modes:
    - 'summarize': Clinical assessment and discharge summary preserving pseudonymised tokens.
    - 'qa': Clinical question answering referencing surrogate entities.
    - 'extract' / 'extract_entities': Structured slot extraction of surrogate tokens and findings.
    - 'echo': Verbatim prompt echo for round-trip baseline verification.
    """

    def __init__(
        self,
        mode: str = "summarize",
        default_response: Optional[str] = None,
        model_name: str = "mock-clinical-llm-v1",
        **kwargs: Any,
    ):
        super().__init__(
            model_name=model_name,
            provider_name="mock",
            temperature=kwargs.get("temperature", 0.0),
            max_tokens=kwargs.get("max_tokens", 1024),
            **kwargs,
        )
        self.mode = mode
        self.default_response = default_response

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Synchronous mock generation."""
        if not prompt or not isinstance(prompt, str):
            return "CLINICAL SUMMARY: No clinical data provided."

        if self.default_response is not None:
            return self.default_response

        active_mode = kwargs.get("mode", self.mode)

        if active_mode == "summarize":
            return self._mock_summarize(prompt)
        elif active_mode == "qa":
            return self._mock_qa(prompt)
        elif active_mode in ("extract", "extract_entities"):
            return self._mock_extract(prompt)
        elif active_mode == "echo":
            return prompt
        else:
            return self._mock_summarize(prompt)

    async def agenerate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Asynchronous mock generation (non-blocking)."""
        await asyncio.sleep(0)  # Yield control loop
        return self.generate(prompt, system_prompt=system_prompt, **kwargs)

    def _mock_summarize(self, prompt: str) -> str:
        """Generates a structured clinical summary retaining all surrogate tokens."""
        # Extract all surrogate tokens in order of appearance
        tokens: List[str] = []
        for match in re.findall(r"\[[A-Z0-9_+]+\]", prompt):
            if match not in tokens:
                tokens.append(match)

        # Extract lines that carry clinical weight
        lines = [line.strip() for line in prompt.split("\n") if line.strip()]
        clinical_findings: List[str] = []
        for line in lines:
            lower = line.lower()
            if any(
                k in lower
                for k in [
                    "diagnos", "assess", "plan", "history", "reason", "chemotherapy",
                    "admit", "prescrib", "evaluat", "seen by", "consult", "procedure",
                    "exam", "findings", "discharge", "treatment", "stage", "biopsy",
                    "impression", "recommend", "initiating", "surgery"
                ]
            ):
                clinical_findings.append(line)

        summary_parts: List[str] = ["CLINICAL SUMMARY & ASSESSMENT:"]

        # Build lead encounter line with primary surrogate tokens
        patient_tok = next((t for t in tokens if "PATIENT" in t), None)
        provider_tok = next((t for t in tokens if "PROVIDER" in t or "DOCTOR" in t), None)
        hosp_tok = next((t for t in tokens if "HOSPITAL" in t or "FACILITY" in t or "CLINIC" in t), None)
        date_tok = next((t for t in tokens if "DATE" in t), None)

        lead_parts: List[str] = []
        if patient_tok:
            lead_parts.append(f"Patient {patient_tok}")
        else:
            lead_parts.append("Patient")

        if provider_tok:
            lead_parts.append(f"was evaluated by {provider_tok}")
        if hosp_tok:
            lead_parts.append(f"at {hosp_tok}")
        if date_tok:
            lead_parts.append(f"on {date_tok}")

        lead_line = " ".join(lead_parts) + "."
        summary_parts.append(lead_line)

        # Add clinical findings
        if clinical_findings:
            for item in clinical_findings[:6]:
                # Format as clean bullet point if not already
                bullet = item if item.startswith("-") else f"- {item}"
                summary_parts.append(bullet)
        else:
            for item in lines[:4]:
                bullet = item if item.startswith("-") else f"- {item}"
                summary_parts.append(bullet)

        # Ensure all detected surrogate tokens are present in summary for rehydration
        summary_text = "\n".join(summary_parts)
        missing_tokens = [t for t in tokens if t not in summary_text]
        if missing_tokens:
            summary_parts.append(f"Reference Tokens: {', '.join(missing_tokens)}")
            summary_text = "\n".join(summary_parts)

        return summary_text

    def _mock_qa(self, prompt: str) -> str:
        """Answers clinical Q&A prompts referencing surrogate tokens."""
        tokens = re.findall(r"\[[A-Z0-9_+]+\]", prompt)
        provider = next((t for t in tokens if "PROVIDER" in t or "DOCTOR" in t), "[PROVIDER_1]")
        date = next((t for t in tokens if "DATE" in t), "[DATE_1]")
        patient = next((t for t in tokens if "PATIENT" in t), "[PATIENT_1]")

        return (
            f"CLINICAL QA ANSWER:\n"
            f"The procedure was performed by {provider} on {date} for patient {patient}. "
            f"All post-operative monitoring is within normal limits."
        )

    def _mock_extract(self, prompt: str) -> str:
        """Extracts structured slot and surrogate token mappings."""
        tokens = re.findall(r"\[[A-Z0-9_+]+\]", prompt)
        extracted: List[str] = []
        for tok in tokens:
            extracted.append(f"- Identified Entity: {tok}")

        if not extracted:
            extracted = ["- No surrogate entities identified in prompt."]

        return "STRUCTURED CLINICAL EXTRACTION:\n" + "\n".join(extracted)
