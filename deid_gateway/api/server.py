"""
FastAPI REST Service for HIPAA Safe Harbor De-Identification & Rehydration Gateway.
"""

from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from deid_gateway.adapters.anthropic_adapter import AnthropicAdapter
from deid_gateway.adapters.base import BaseLLMAdapter
from deid_gateway.adapters.gemini_adapter import GeminiAdapter
from deid_gateway.adapters.mock_adapter import MockLLMAdapter
from deid_gateway.adapters.openai_adapter import OpenAIAdapter
from deid_gateway.api.schemas import (
    DeidentifyRequest,
    DeidentifyResponse,
    GatewayProcessRequest,
    GatewayProcessResponse,
    GatewaySummarizeRequest,
    HealthResponse,
    RehydrateRequest,
    RehydrateResponse,
)
from deid_gateway.core.config import DeidConfig
from deid_gateway.core.deidentify import deidentify
from deid_gateway.core.models.model_card import get_parameter_count
from deid_gateway.core.rehydrate import rehydrate
from deid_gateway.gateway import DeidGateway


def _resolve_adapter(
    provider: str,
    model_name: Optional[str] = None,
    extra_options: Optional[Dict[str, Any]] = None,
) -> BaseLLMAdapter:
    """Helper to instantiate the appropriate LLM adapter."""
    opts = extra_options or {}
    provider_lower = (provider or "mock").lower()

    if provider_lower == "mock":
        mode = opts.get("mode", "summarize")
        return MockLLMAdapter(
            mode=mode,
            model_name=model_name or "mock-clinical-llm-v1",
            **opts,
        )
    elif provider_lower == "openai":
        return OpenAIAdapter(
            model_name=model_name or "gpt-4o",
            api_key=opts.get("api_key"),
            **opts,
        )
    elif provider_lower == "anthropic":
        return AnthropicAdapter(
            model_name=model_name or "claude-3-5-sonnet-20240620",
            api_key=opts.get("api_key"),
            **opts,
        )
    elif provider_lower in ("gemini", "google"):
        return GeminiAdapter(
            model_name=model_name or "gemini-1.5-flash",
            api_key=opts.get("api_key"),
            **opts,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported adapter provider: '{provider}'. Supported: mock, openai, anthropic, gemini",
        )


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application instance."""
    app = FastAPI(
        title="HIPAA Safe Harbor PHI/PII De-Identification Gateway",
        description=(
            "Production-grade gateway service stripping patient identifiers before text reaches "
            "foundation LLMs and restoring clinical context on responses without leaking protected data."
        ),
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health_check() -> HealthResponse:
        """Health check, version metadata, and parameter verification."""
        param_count = get_parameter_count()
        return HealthResponse(
            status="ok",
            version="1.0.0",
            model_parameter_count=param_count,
            supported_adapters=["mock", "openai", "anthropic", "gemini"],
        )

    @app.post("/deidentify", response_model=DeidentifyResponse, tags=["De-Identification"])
    async def deidentify_endpoint(req: DeidentifyRequest) -> DeidentifyResponse:
        """
        De-identify clinical text according to HIPAA Safe Harbor 18 categories.
        Returns masked text with pseudonymised surrogate tokens and isolated mapping dict.
        """
        try:
            cfg = DeidConfig(
                masking_mode=req.masking_mode,
                preserve_eponyms=req.preserve_eponyms,
                preserve_relative_dates=req.preserve_relative_dates,
                patient_id=req.patient_id,
                date_shift_days=req.date_shift_days,
            )
            masked_text, mapping = deidentify(req.text, config=cfg)
            entity_count = len(mapping.get("entities", [])) or len(mapping.get("token_to_original", {}))
            return DeidentifyResponse(
                masked_text=masked_text,
                mapping=mapping,
                entity_count=entity_count,
                date_shift_days=mapping.get("date_shift_days"),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"De-identification error: {str(e)}",
            )

    @app.post("/rehydrate", response_model=RehydrateResponse, tags=["Rehydration"])
    async def rehydrate_endpoint(req: RehydrateRequest) -> RehydrateResponse:
        """
        Rehydrate foundation LLM response by substituting surrogate tokens with original entities.
        """
        try:
            rehydrated = rehydrate(req.response, req.mapping, strict_mode=req.strict_mode)
            restored_count = len(req.mapping.get("token_to_original", {}))
            return RehydrateResponse(
                rehydrated_text=rehydrated,
                restored_entities_count=restored_count,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Rehydration error: {str(e)}",
            )

    @app.post("/gateway/process", response_model=GatewayProcessResponse, tags=["Gateway"])
    async def gateway_process_endpoint(req: GatewayProcessRequest) -> GatewayProcessResponse:
        """
        Full end-to-end roundtrip: Raw Note -> De-identify -> LLM Generation -> Rehydrate.
        """
        try:
            adapter = _resolve_adapter(
                provider=req.adapter_provider,
                model_name=req.model_name,
                extra_options=req.extra_options,
            )
            cfg = DeidConfig(
                patient_id=req.patient_id,
                date_shift_days=req.date_shift_days,
            )
            gateway = DeidGateway(adapter=adapter, deid_config=cfg)

            result = await gateway.aprocess(
                clinical_note=req.clinical_note,
                task_prompt=req.task_prompt,
                system_prompt=req.system_prompt,
            )

            return GatewayProcessResponse(
                final_text=result.final_text,
                masked_input=result.masked_input,
                raw_llm_response=result.raw_llm_response,
                mapping=result.mapping,
                latency_ms=result.latency_ms,
                deid_latency_ms=result.deid_latency_ms,
                llm_latency_ms=result.llm_latency_ms,
                rehydrate_latency_ms=result.rehydrate_latency_ms,
                entity_count=result.entity_count,
                leak_check_passed=result.leak_check_passed,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gateway pipeline error: {str(e)}",
            )

    @app.post("/gateway/summarize", response_model=GatewayProcessResponse, tags=["Gateway"])
    async def gateway_summarize_endpoint(req: GatewaySummarizeRequest) -> GatewayProcessResponse:
        """
        Convenience endpoint for clinical summarization through the secure gateway.
        """
        process_req = GatewayProcessRequest(
            clinical_note=req.clinical_note,
            task_prompt="Please generate a concise clinical summary for this patient note:\n\n{text}",
            adapter_provider=req.adapter_provider,
            model_name=req.model_name,
            system_prompt=req.system_prompt or "You are an expert clinical summarization assistant.",
        )
        return await gateway_process_endpoint(process_req)

    return app


# Module-level default application instance
app = create_app()
