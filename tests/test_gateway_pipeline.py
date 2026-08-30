"""
Tests for End-to-End De-Identification Gateway Pipeline (Tier 3).
Verifies:
- Complete roundtrip workflow: Raw Clinical Note -> deidentify -> LLM Adapter -> rehydrate.
- Zero Raw PHI Transmission Guard: Verifies prompt received by foundation LLM contains NO raw PHI.
- Rehydration restoration of clinical meaning on downstream LLM responses.
- GatewayResult data structure, timing telemetry, and multi-specialty notes integration.
"""

import pytest
from typing import Dict, Any
from unittest.mock import MagicMock

try:
    from deid_gateway.gateway import DeidGateway, GatewayResult
    from deid_gateway.adapters.mock_adapter import MockLLMAdapter
    from deid_gateway.core.config import DeidConfig
except ImportError:
    DeidGateway = None
    GatewayResult = None
    MockLLMAdapter = None
    DeidConfig = None


# =============================================================================
# TIER 3: CROSS-FEATURE INTEGRATION - END-TO-END GATEWAY ROUNDTRIP
# =============================================================================

class TestGatewayPipelineIntegration:
    """Tier 3: End-to-end integration tests connecting de-id, adapters, and rehydration."""

    def test_complete_roundtrip_with_mock_llm(self, sample_clinical_note: str):
        """
        Tier 3: Verifies full execution cycle:
        1. Clinical note is de-identified.
        2. Foundation LLM processes masked note.
        3. LLM response is rehydrated with original entities.
        """
        if DeidGateway is None or MockLLMAdapter is None:
            pytest.skip("DeidGateway or MockLLMAdapter implementation pending")

        adapter = MockLLMAdapter(mode="summarize")
        gateway = DeidGateway(adapter=adapter)

        result = gateway.process(
            clinical_note=sample_clinical_note,
            task_prompt="Provide a concise clinical assessment and treatment plan:"
        )

        assert isinstance(result, GatewayResult)
        assert isinstance(result.final_text, str)
        assert len(result.final_text) > 0

        # Verify restored entities appear in final text
        assert "Robert Henderson" in result.final_text or "Dr. James Parkinson" in result.final_text

        # Verify surrogate tokens were eliminated during rehydration
        assert "[PATIENT_1]" not in result.final_text
        assert "[PROVIDER_1]" not in result.final_text

    def test_zero_raw_phi_leaked_to_foundation_llm_adapter(self, sample_clinical_note: str):
        """
        CRITICAL SECURITY INVARIANCE TEST:
        Inspects the exact text payload delivered to the foundation LLM adapter
        and asserts that NO raw PHI (patient name, SSN, MRN, phone, address) is transmitted.
        """
        if DeidGateway is None:
            pytest.skip("DeidGateway implementation pending")

        # Create spy adapter to inspect payload received by LLM
        spy_adapter = MagicMock()
        spy_adapter.generate.return_value = "Summary for [PATIENT_1] on [DATE_1]."

        gateway = DeidGateway(adapter=spy_adapter)
        gateway.process(
            clinical_note=sample_clinical_note,
            task_prompt="Summarize note:"
        )

        # Retrieve the exact prompt string sent to adapter.generate()
        spy_adapter.generate.assert_called_once()
        prompt_received_by_llm = spy_adapter.generate.call_args[0][0]

        # PHI that MUST NOT be present in prompt received by LLM
        forbidden_phi = [
            "Robert Henderson",
            "078-45-9921",
            "884-9102-X",
            "617-555-0144",
            "1982736450",
            "05/14/1958"
        ]

        for phi in forbidden_phi:
            assert phi not in prompt_received_by_llm, (
                f"SECURITY BREACH: Raw PHI '{phi}' was leaked in prompt delivered to foundation LLM!\n"
                f"Prompt payload:\n{prompt_received_by_llm}"
            )

        # Medical eponyms SHOULD remain intact in the prompt
        assert "Parkinson's disease" in prompt_received_by_llm, (
            "Medical eponym 'Parkinson's disease' was incorrectly stripped before reaching LLM!"
        )

    def test_gateway_result_metadata_and_telemetry(self, sample_clinical_note: str):
        """Tier 3: Verifies GatewayResult contains latency, token count, and mapping audit metadata."""
        if DeidGateway is None or MockLLMAdapter is None:
            pytest.skip("DeidGateway or MockLLMAdapter implementation pending")

        adapter = MockLLMAdapter(mode="summarize")
        gateway = DeidGateway(adapter=adapter)

        result = gateway.process(
            clinical_note=sample_clinical_note,
            task_prompt="Summarize:"
        )

        assert result.masked_input is not None
        assert result.raw_llm_response is not None
        assert result.mapping is not None
        assert isinstance(result.latency_ms, (int, float))
        assert result.latency_ms >= 0.0

    def test_multi_specialty_note_processing(self, annotated_notes_55: list):
        """Tier 3: Executes gateway pipeline across sample notes from 5 diverse specialties."""
        if DeidGateway is None or MockLLMAdapter is None:
            pytest.skip("DeidGateway or MockLLMAdapter implementation pending")

        adapter = MockLLMAdapter(mode="summarize")
        gateway = DeidGateway(adapter=adapter)

        # Test first 5 notes (Oncology, Cardiology, etc.)
        for note in annotated_notes_55[:5]:
            result = gateway.process(
                clinical_note=note["raw_text"],
                task_prompt="Summarize clinical findings:"
            )
            assert result.final_text is not None
            assert len(result.final_text) > 0


# =============================================================================
# TIER 3: REST API ENDPOINTS (FASTAPI SERVICE INTEGRATION)
# =============================================================================

class TestFastAPIGatewayEndpoints:
    """Tier 3: Verifies FastAPI REST endpoints (/health, /deidentify, /rehydrate, /gateway/*)."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Verifies GET /health returns status, version, and verified model parameter count."""
        try:
            import httpx
            from deid_gateway.api.server import app
        except ImportError:
            pytest.skip("FastAPI/httpx or app implementation pending")

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["version"] == "1.0.0"
            assert isinstance(data["model_parameter_count"], int)
            assert data["model_parameter_count"] <= 1_000_000_000
            assert "mock" in data["supported_adapters"]

    @pytest.mark.asyncio
    async def test_deidentify_and_rehydrate_endpoints(self, sample_clinical_note: str):
        """Verifies POST /deidentify and POST /rehydrate roundtrip over HTTP."""
        try:
            import httpx
            from deid_gateway.api.server import app
        except ImportError:
            pytest.skip("FastAPI/httpx or app implementation pending")

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. Test /deidentify
            deid_resp = await client.post("/deidentify", json={"text": sample_clinical_note})
            assert deid_resp.status_code == 200
            deid_data = deid_resp.json()
            assert "masked_text" in deid_data
            assert "mapping" in deid_data
            assert deid_data["entity_count"] > 0
            assert "Robert Henderson" not in deid_data["masked_text"]

            # 2. Test /rehydrate
            mock_completion = "Patient [PATIENT_2] was seen by [PROVIDER_1] at [HOSPITAL_2]."
            rehydrate_resp = await client.post(
                "/rehydrate",
                json={"response": mock_completion, "mapping": deid_data["mapping"]}
            )
            assert rehydrate_resp.status_code == 200
            rehydrate_data = rehydrate_resp.json()
            assert "Parkinson" in rehydrate_data["rehydrated_text"] or "Henderson" in rehydrate_data["rehydrated_text"]

    @pytest.mark.asyncio
    async def test_gateway_process_and_summarize_endpoints(self, sample_clinical_note: str):
        """Verifies POST /gateway/process and POST /gateway/summarize endpoints."""
        try:
            import httpx
            from deid_gateway.api.server import app
        except ImportError:
            pytest.skip("FastAPI/httpx or app implementation pending")

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Test /gateway/process
            resp = await client.post(
                "/gateway/process",
                json={
                    "clinical_note": sample_clinical_note,
                    "task_prompt": "Please summarize:\n\n{text}",
                    "adapter_provider": "mock"
                }
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "final_text" in data
            assert "masked_input" in data
            assert data["latency_ms"] >= 0.0
            assert data["leak_check_passed"] is True

            # Test /gateway/summarize
            sum_resp = await client.post(
                "/gateway/summarize",
                json={
                    "clinical_note": sample_clinical_note,
                    "adapter_provider": "mock"
                }
            )
            assert sum_resp.status_code == 200
            sum_data = sum_resp.json()
            assert "final_text" in sum_data
            assert len(sum_data["final_text"]) > 0
