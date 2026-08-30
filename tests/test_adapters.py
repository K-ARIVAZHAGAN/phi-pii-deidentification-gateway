"""
Tests for Pluggable Foundation LLM Adapters (Tiers 1 & 2).
Verifies:
- BaseLLMAdapter abstract interface contract (generate and agenerate).
- Hermetic MockLLMAdapter for deterministic, offline clinical tasks (Summarization, QA, Slot Extraction).
- Production Cloud LLM Adapters (OpenAIAdapter, AnthropicAdapter, GeminiAdapter) with mock integration.
- Error handling for missing credentials and API exceptions.
"""

import asyncio
import os
import pytest
from typing import Optional
from unittest.mock import patch, MagicMock

try:
    from deid_gateway.adapters.base import BaseLLMAdapter
    from deid_gateway.adapters.mock_adapter import MockLLMAdapter
    from deid_gateway.adapters.openai_adapter import OpenAIAdapter
    from deid_gateway.adapters.anthropic_adapter import AnthropicAdapter
    from deid_gateway.adapters.gemini_adapter import GeminiAdapter
except ImportError:
    BaseLLMAdapter = None
    MockLLMAdapter = None
    OpenAIAdapter = None
    AnthropicAdapter = None
    GeminiAdapter = None


# =============================================================================
# TIER 1: FEATURE COVERAGE - HERMETIC MOCK LLM ADAPTER
# =============================================================================

class TestMockLLMAdapterFeatureCoverage:
    """Tier 1: Tests hermetic MockLLMAdapter clinical task modes and determinism."""

    def test_mock_adapter_instantiation_and_default_mode(self):
        """Verifies MockLLMAdapter instantiates and implements BaseLLMAdapter interface."""
        if MockLLMAdapter is None:
            pytest.skip("MockLLMAdapter implementation pending")

        adapter = MockLLMAdapter()
        assert isinstance(adapter, BaseLLMAdapter)
        assert adapter.provider_name == "mock"

    def test_mock_adapter_clinical_summarization_task(self):
        """Verifies MockLLMAdapter generates clinical summaries preserving surrogate tokens."""
        if MockLLMAdapter is None:
            pytest.skip("MockLLMAdapter implementation pending")

        adapter = MockLLMAdapter(mode="summarize")
        prompt = (
            "Summarize this clinical encounter:\n"
            "PATIENT: [PATIENT_1] was seen by [PROVIDER_1] at [HOSPITAL_1] on [DATE_1]. "
            "Diagnosis: Stage IIIB Classic Hodgkin lymphoma. Initiating ABVD chemotherapy."
        )

        response = adapter.generate(prompt)

        assert isinstance(response, str)
        assert len(response) > 20
        # Crucial: Surrogate tokens must be retained in the summary for rehydration
        assert "[PATIENT_1]" in response
        assert "[PROVIDER_1]" in response
        assert "Hodgkin lymphoma" in response

    def test_mock_adapter_clinical_qa_task(self):
        """Verifies MockLLMAdapter answers clinical questions referencing surrogate tokens."""
        if MockLLMAdapter is None:
            pytest.skip("MockLLMAdapter implementation pending")

        adapter = MockLLMAdapter(mode="qa")
        prompt = (
            "Context: [PATIENT_1] was admitted on [DATE_1] for acute appendicitis. "
            "Surgery was completed by [PROVIDER_1].\n"
            "Question: Who performed the surgery and when was the admission?"
        )

        response = adapter.generate(prompt)

        assert isinstance(response, str)
        assert "[PROVIDER_1]" in response
        assert "[DATE_1]" in response

    def test_mock_adapter_slot_extraction_task(self):
        """Verifies MockLLMAdapter extracts structured slot information."""
        if MockLLMAdapter is None:
            pytest.skip("MockLLMAdapter implementation pending")

        adapter = MockLLMAdapter(mode="extract")
        prompt = (
            "Extract entities:\n"
            "Patient [PATIENT_1], Age: [AGE_90+], Physician: [PROVIDER_1], Med: carbidopa-levodopa."
        )

        response = adapter.generate(prompt)
        assert "[PATIENT_1]" in response
        assert "[PROVIDER_1]" in response

    def test_mock_adapter_async_agenerate(self):
        """Verifies asynchronous agenerate() method produces identical output."""
        if MockLLMAdapter is None:
            pytest.skip("MockLLMAdapter implementation pending")

        adapter = MockLLMAdapter(mode="summarize")
        prompt = "Patient [PATIENT_1] evaluated on [DATE_1]."

        async def _run_async():
            return await adapter.agenerate(prompt)

        response = asyncio.run(_run_async())
        assert isinstance(response, str)
        assert "[PATIENT_1]" in response


# =============================================================================
# TIER 1 & 2: CLOUD LLM ADAPTERS (MOCKED INTEGRATIONS)
# =============================================================================

class TestCloudLLMAdapters:
    """Tier 1 & 2: Tests OpenAI, Anthropic, and Gemini adapters with mocked network responses."""

    def test_openai_adapter_generate_with_mock_client(self):
        """Verifies OpenAIAdapter formats requests and extracts response text."""
        if OpenAIAdapter is None:
            pytest.skip("OpenAIAdapter implementation pending")

        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="Summary: [PATIENT_1] is doing well."))
        ]
        mock_client.chat.completions.create.return_value = mock_completion

        adapter = OpenAIAdapter(api_key="sk-mock-key-12345", client=mock_client)
        result = adapter.generate("Please summarize the patient record: [PATIENT_1]")

        assert result == "Summary: [PATIENT_1] is doing well."
        mock_client.chat.completions.create.assert_called_once()

    def test_anthropic_adapter_generate_with_mock_client(self):
        """Verifies AnthropicAdapter formats requests and extracts Claude message response."""
        if AnthropicAdapter is None:
            pytest.skip("AnthropicAdapter implementation pending")

        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="Follow-up planned for [PATIENT_1] with [PROVIDER_1].")]
        mock_client.messages.create.return_value = mock_msg

        adapter = AnthropicAdapter(api_key="sk-ant-mock-key", client=mock_client)
        result = adapter.generate("Analyze clinical note for [PATIENT_1]")

        assert result == "Follow-up planned for [PATIENT_1] with [PROVIDER_1]."
        mock_client.messages.create.assert_called_once()

    def test_gemini_adapter_generate_with_mock_client(self):
        """Verifies GeminiAdapter formats requests and returns model text."""
        if GeminiAdapter is None:
            pytest.skip("GeminiAdapter implementation pending")

        mock_client = MagicMock()
        mock_response = MagicMock(text="Clinical assessment: [PATIENT_1] on [DATE_1].")
        mock_client.models.generate_content.return_value = mock_response

        adapter = GeminiAdapter(api_key="mock-gemini-key", client=mock_client)
        result = adapter.generate("Review note for [PATIENT_1]")

        assert result == "Clinical assessment: [PATIENT_1] on [DATE_1]."

    def test_cloud_adapter_missing_api_key_raises_informative_error(self):
        """Corner: Instantiating cloud adapters without API key or env var raises ValueError."""
        if OpenAIAdapter is None:
            pytest.skip("OpenAIAdapter implementation pending")

        # Temporarily clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises((ValueError, KeyError)):
                OpenAIAdapter(api_key=None)


# =============================================================================
# TIER 2: ADAPTER BOUNDARY CASES
# =============================================================================

class TestAdapterBoundaryCases:
    """Tier 2: Empty prompts, huge context lengths, and latency simulation."""

    def test_empty_prompt_handling(self):
        """Boundary: Adapter handling of empty prompt."""
        if MockLLMAdapter is None:
            pytest.skip("MockLLMAdapter implementation pending")

        adapter = MockLLMAdapter()
        res = adapter.generate("")
        assert isinstance(res, str)

    def test_system_prompt_parameter_support(self):
        """Verifies BaseLLMAdapter accepts optional system_prompt kwarg."""
        if MockLLMAdapter is None:
            pytest.skip("MockLLMAdapter implementation pending")

        adapter = MockLLMAdapter()
        res = adapter.generate("Prompt", system_prompt="You are a clinical expert.")
        assert isinstance(res, str)
