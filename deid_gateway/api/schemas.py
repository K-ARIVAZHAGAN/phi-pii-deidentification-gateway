"""
Pydantic Request and Response Schemas for De-Identification Gateway API.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Health check and capability disclosure response."""
    model_config = ConfigDict(protected_namespaces=())

    status: str = Field("ok", description="Service health status")
    version: str = Field("1.0.0", description="API and service version")
    model_parameter_count: int = Field(..., description="Active token classification model parameter count (<= 1B)")
    supported_adapters: List[str] = Field(
        default_factory=lambda: ["mock", "openai", "anthropic", "gemini"],
        description="Supported foundation LLM adapter providers",
    )


class DeidentifyRequest(BaseModel):
    """Request payload for de-identifying raw clinical text."""
    model_config = ConfigDict(protected_namespaces=())

    text: str = Field(..., description="Raw clinical text containing potential PHI/PII")
    patient_id: Optional[str] = Field(None, description="Optional patient identifier for deterministic salt/offset")
    date_shift_days: Optional[int] = Field(None, description="Optional explicit signed day offset for date shifting")
    masking_mode: str = Field("surrogate_token", description="Masking mode: 'surrogate_token' or 'synthetic_replacement'")
    preserve_eponyms: bool = Field(True, description="Whether to protect medical eponyms (e.g. Parkinson's disease)")
    preserve_relative_dates: bool = Field(True, description="Whether to leave relative clinical durations unmasked")
    extra_config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration parameters")


class DeidentifyResponse(BaseModel):
    """Response payload containing de-identified text and cryptographic session mapping."""
    model_config = ConfigDict(protected_namespaces=())

    masked_text: str = Field(..., description="De-identified text with pseudonymised surrogate tokens")
    mapping: Dict[str, Any] = Field(..., description="Isolated cryptographic mapping dictionary for rehydration")
    entity_count: int = Field(..., description="Total number of PHI/PII entity occurrences detected and masked")
    date_shift_days: Optional[int] = Field(None, description="Applied relative day offset")


class RehydrateRequest(BaseModel):
    """Request payload for rehydrating LLM response with original clinical entities."""
    model_config = ConfigDict(protected_namespaces=())

    response: str = Field(..., description="Foundation LLM response containing surrogate tokens")
    mapping: Dict[str, Any] = Field(..., description="The session mapping dictionary returned by /deidentify")
    strict_mode: bool = Field(False, description="Strict rehydration validation mode")


class RehydrateResponse(BaseModel):
    """Response payload containing rehydrated clinical response."""
    model_config = ConfigDict(protected_namespaces=())

    rehydrated_text: str = Field(..., description="Response text with original clinical entities restored")
    restored_entities_count: int = Field(..., description="Number of surrogate tokens restored")


class GatewayProcessRequest(BaseModel):
    """Request payload for full roundtrip gateway pipeline execution."""
    model_config = ConfigDict(protected_namespaces=())

    clinical_note: str = Field(..., description="Raw clinical note containing potential PHI/PII")
    task_prompt: str = Field(
        "Please provide a concise clinical assessment and discharge summary:\n\n{text}",
        description="Task prompt template containing '{text}' or task instructions",
    )
    adapter_provider: str = Field("mock", description="LLM provider: 'mock', 'openai', 'anthropic', or 'gemini'")
    model_name: Optional[str] = Field(None, description="Specific model name override for provider")
    system_prompt: Optional[str] = Field(None, description="Optional system instructions")
    patient_id: Optional[str] = Field(None, description="Optional patient ID")
    date_shift_days: Optional[int] = Field(None, description="Explicit date shift days")
    extra_options: Optional[Dict[str, Any]] = Field(None, description="Additional adapter/deid options")


class GatewaySummarizeRequest(BaseModel):
    """Convenience request payload for clinical summarization."""
    model_config = ConfigDict(protected_namespaces=())

    clinical_note: str = Field(..., description="Raw clinical note to summarize")
    adapter_provider: str = Field("mock", description="LLM provider: 'mock', 'openai', 'anthropic', or 'gemini'")
    model_name: Optional[str] = Field(None, description="Optional model name override")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt")


class GatewayProcessResponse(BaseModel):
    """Response payload of full roundtrip gateway execution."""
    model_config = ConfigDict(protected_namespaces=())

    final_text: str = Field(..., description="Rehydrated final response with clinical meaning intact")
    masked_input: str = Field(..., description="De-identified text delivered to foundation LLM")
    raw_llm_response: str = Field(..., description="Raw LLM completion containing surrogate tokens")
    mapping: Dict[str, Any] = Field(..., description="Cryptographic mapping dictionary")
    latency_ms: float = Field(..., description="Total round-trip latency in milliseconds")
    deid_latency_ms: float = Field(0.0, description="De-identification stage latency in milliseconds")
    llm_latency_ms: float = Field(0.0, description="Foundation LLM inference latency in milliseconds")
    rehydrate_latency_ms: float = Field(0.0, description="Rehydration stage latency in milliseconds")
    entity_count: int = Field(0, description="Total entity count detected")
    leak_check_passed: bool = Field(True, description="Zero-leak verification guard status")
