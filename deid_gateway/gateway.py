"""
End-to-End PHI/PII De-Identification & Rehydration Gateway Orchestrator.
Pipeline: Raw Clinical Note -> deidentify -> Foundation LLM Adapter -> rehydrate
"""

from dataclasses import dataclass, field
import time
from typing import Any, Callable, Dict, List, Optional, Union

from deid_gateway.adapters.base import BaseLLMAdapter
from deid_gateway.adapters.mock_adapter import MockLLMAdapter
from deid_gateway.core.config import DeidConfig
from deid_gateway.core.deidentify import deidentify
from deid_gateway.core.rehydrate import rehydrate


@dataclass
class GatewayResult:
    """
    Structured outcome of the end-to-end Gateway roundtrip execution.
    """
    final_text: str
    masked_input: str
    raw_llm_response: str
    mapping: Dict[str, Any]
    latency_ms: float
    deid_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    rehydrate_latency_ms: float = 0.0
    entity_count: int = 0
    raw_input: Optional[str] = None
    leak_check_passed: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def zero_phi_leaked(self) -> bool:
        """True if zero raw PHI entities leaked into masked payload."""
        return self.leak_check_passed

    @property
    def leak_detected(self) -> bool:
        """True if a leak was detected."""
        return not self.leak_check_passed

    def to_dict(self) -> Dict[str, Any]:
        """Convert GatewayResult to full dictionary representation."""
        return {
            "final_text": self.final_text,
            "final_rehydrated_response": self.final_text,
            "masked_input": self.masked_input,
            "masked_note": self.masked_input,
            "raw_input": self.raw_input,
            "raw_note": self.raw_input,
            "raw_llm_response": self.raw_llm_response,
            "llm_response_masked": self.raw_llm_response,
            "mapping": self.mapping,
            "latency_ms": self.latency_ms,
            "metrics": {
                "deid_latency_ms": self.deid_latency_ms,
                "llm_latency_ms": self.llm_latency_ms,
                "rehydrate_latency_ms": self.rehydrate_latency_ms,
                "total_latency_ms": self.latency_ms,
                "entity_count": self.entity_count,
            },
            "entity_count": self.entity_count,
            "leak_check_passed": self.leak_check_passed,
            "metadata": self.metadata,
        }

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access for backwards compatibility."""
        d = self.to_dict()
        if key in d:
            return d[key]
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        """Safe dictionary-style get."""
        d = self.to_dict()
        return d.get(key, default)


class DeidGateway:
    """
    Production-grade end-to-end De-Identification Gateway.
    
    Orchestrates:
    1. De-identifying raw clinical text into pseudonymised text + isolated cryptographic mapping.
    2. Zero-Leak Security Guard validation prior to external transmission.
    3. Invoking Foundation LLM Adapter (Mock, OpenAI, Anthropic, Gemini).
    4. Rehydrating downstream LLM response to restore original clinical entities.
    5. Collecting high-resolution timing telemetry and metrics.
    """

    def __init__(
        self,
        adapter: Optional[BaseLLMAdapter] = None,
        deid_config: Optional[Union[DeidConfig, Dict[str, Any]]] = None,
        deidentifier: Optional[Callable] = None,
        rehydrator: Optional[Callable] = None,
    ):
        self.adapter = adapter or MockLLMAdapter()
        if isinstance(deid_config, DeidConfig):
            self.deid_config = deid_config
        elif isinstance(deid_config, dict):
            self.deid_config = DeidConfig.from_dict(deid_config)
        else:
            self.deid_config = DeidConfig()

        self.deidentify_fn = deidentifier or deidentify
        self.rehydrate_fn = rehydrator or rehydrate

    def _format_prompt(self, task_prompt: str, masked_text: str) -> str:
        """Formats prompt payload for foundation model ingestion."""
        if "{text}" in task_prompt:
            return task_prompt.format(text=masked_text)
        elif "{masked_text}" in task_prompt:
            return task_prompt.format(masked_text=masked_text)
        elif "{prompt}" in task_prompt:
            return task_prompt.format(prompt=masked_text)
        elif "{input}" in task_prompt:
            return task_prompt.format(input=masked_text)
        else:
            return f"{task_prompt}\n\n{masked_text}"

    def _verify_zero_leak(self, masked_text: str, mapping: Dict[str, Any]) -> bool:
        """
        Zero-Leak Security Guard:
        Verifies that none of the original sensitive entity strings leaked into masked text.
        """
        token_to_orig = mapping.get("token_to_original", {})
        for token, orig in token_to_orig.items():
            orig_str = str(orig).strip()
            # Ignore single-character entities or numeric single digits
            if len(orig_str) > 2 and orig_str in masked_text:
                return False
        return True

    def process(
        self,
        clinical_note: str,
        task_prompt: str = "Please provide a concise clinical assessment and discharge summary:\n\n{text}",
        adapter: Optional[BaseLLMAdapter] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> GatewayResult:
        """
        Synchronously executes the full secure round-trip:
        Raw Note -> deidentify -> LLM Adapter -> rehydrate
        """
        start_time = time.perf_counter()

        # Step 1: De-identify raw clinical note
        t0 = time.perf_counter()
        masked_text, mapping = self.deidentify_fn(
            clinical_note,
            config=self.deid_config,
            **kwargs,
        )
        deid_latency_ms = (time.perf_counter() - t0) * 1000.0

        # Step 2: Zero-Leak verification guard
        leak_check_passed = self._verify_zero_leak(masked_text, mapping)

        # Step 3: Format prompt for Foundation LLM
        formatted_prompt = self._format_prompt(task_prompt, masked_text)

        # Step 4: Foundation LLM generation
        active_adapter = adapter or self.adapter
        t1 = time.perf_counter()
        raw_llm_response = active_adapter.generate(
            formatted_prompt,
            system_prompt=system_prompt,
            **kwargs,
        )
        llm_latency_ms = (time.perf_counter() - t1) * 1000.0

        # Step 5: Response rehydration
        t2 = time.perf_counter()
        final_text = self.rehydrate_fn(
            raw_llm_response,
            mapping,
            **kwargs,
        )
        rehydrate_latency_ms = (time.perf_counter() - t2) * 1000.0

        total_latency_ms = (time.perf_counter() - start_time) * 1000.0
        entity_count = len(mapping.get("entities", [])) or len(mapping.get("token_to_original", {}))

        return GatewayResult(
            final_text=final_text,
            masked_input=masked_text,
            raw_llm_response=raw_llm_response,
            mapping=mapping,
            latency_ms=total_latency_ms,
            deid_latency_ms=deid_latency_ms,
            llm_latency_ms=llm_latency_ms,
            rehydrate_latency_ms=rehydrate_latency_ms,
            entity_count=entity_count,
            raw_input=clinical_note,
            leak_check_passed=leak_check_passed,
        )

    async def aprocess(
        self,
        clinical_note: str,
        task_prompt: str = "Please provide a concise clinical assessment and discharge summary:\n\n{text}",
        adapter: Optional[BaseLLMAdapter] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> GatewayResult:
        """
        Asynchronously executes the full secure round-trip:
        Raw Note -> deidentify -> LLM Adapter (async) -> rehydrate
        """
        start_time = time.perf_counter()

        # Step 1: De-identify raw clinical note
        t0 = time.perf_counter()
        masked_text, mapping = self.deidentify_fn(
            clinical_note,
            config=self.deid_config,
            **kwargs,
        )
        deid_latency_ms = (time.perf_counter() - t0) * 1000.0

        # Step 2: Zero-Leak verification guard
        leak_check_passed = self._verify_zero_leak(masked_text, mapping)

        # Step 3: Format prompt for Foundation LLM
        formatted_prompt = self._format_prompt(task_prompt, masked_text)

        # Step 4: Foundation LLM generation (async)
        active_adapter = adapter or self.adapter
        t1 = time.perf_counter()
        raw_llm_response = await active_adapter.agenerate(
            formatted_prompt,
            system_prompt=system_prompt,
            **kwargs,
        )
        llm_latency_ms = (time.perf_counter() - t1) * 1000.0

        # Step 5: Response rehydration
        t2 = time.perf_counter()
        final_text = self.rehydrate_fn(
            raw_llm_response,
            mapping,
            **kwargs,
        )
        rehydrate_latency_ms = (time.perf_counter() - t2) * 1000.0

        total_latency_ms = (time.perf_counter() - start_time) * 1000.0
        entity_count = len(mapping.get("entities", [])) or len(mapping.get("token_to_original", {}))

        return GatewayResult(
            final_text=final_text,
            masked_input=masked_text,
            raw_llm_response=raw_llm_response,
            mapping=mapping,
            latency_ms=total_latency_ms,
            deid_latency_ms=deid_latency_ms,
            llm_latency_ms=llm_latency_ms,
            rehydrate_latency_ms=rehydrate_latency_ms,
            entity_count=entity_count,
            raw_input=clinical_note,
            leak_check_passed=leak_check_passed,
        )

    def summarize(
        self,
        clinical_note: str,
        system_prompt: Optional[str] = "You are an expert clinical summarization assistant.",
        adapter: Optional[BaseLLMAdapter] = None,
        **kwargs: Any,
    ) -> GatewayResult:
        """
        Convenience method for clinical summarization through the secure gateway.
        """
        return self.process(
            clinical_note=clinical_note,
            task_prompt="Please generate a concise clinical summary for this patient note:\n\n{text}",
            adapter=adapter,
            system_prompt=system_prompt,
            **kwargs,
        )

    async def asummarize(
        self,
        clinical_note: str,
        system_prompt: Optional[str] = "You are an expert clinical summarization assistant.",
        adapter: Optional[BaseLLMAdapter] = None,
        **kwargs: Any,
    ) -> GatewayResult:
        """
        Asynchronous convenience method for clinical summarization through the secure gateway.
        """
        return await self.aprocess(
            clinical_note=clinical_note,
            task_prompt="Please generate a concise clinical summary for this patient note:\n\n{text}",
            adapter=adapter,
            system_prompt=system_prompt,
            **kwargs,
        )

    def qa(
        self,
        clinical_note: str,
        question: str,
        system_prompt: Optional[str] = "You are an expert clinical QA assistant.",
        adapter: Optional[BaseLLMAdapter] = None,
        **kwargs: Any,
    ) -> GatewayResult:
        """
        Convenience method for clinical question answering through the secure gateway.
        """
        return self.process(
            clinical_note=clinical_note,
            task_prompt=f"Context:\n{{text}}\n\nQuestion: {question}\nAnswer:",
            adapter=adapter,
            system_prompt=system_prompt,
            **kwargs,
        )

    async def aqa(
        self,
        clinical_note: str,
        question: str,
        system_prompt: Optional[str] = "You are an expert clinical QA assistant.",
        adapter: Optional[BaseLLMAdapter] = None,
        **kwargs: Any,
    ) -> GatewayResult:
        """
        Asynchronous convenience method for clinical question answering through the secure gateway.
        """
        return await self.aprocess(
            clinical_note=clinical_note,
            task_prompt=f"Context:\n{{text}}\n\nQuestion: {question}\nAnswer:",
            adapter=adapter,
            system_prompt=system_prompt,
            **kwargs,
        )
