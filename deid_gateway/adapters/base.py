"""
Abstract Base Class for Foundation LLM Adapters.
Defines the universal contract for pluggable LLM integrations across mock,
local open-weights, and production cloud providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseLLMAdapter(ABC):
    """
    Universal abstract interface for foundation LLM backends.
    
    Supports offline deterministic mocks, local models, and cloud API providers
    (OpenAI, Anthropic, Gemini).
    """

    def __init__(
        self,
        model_name: str = "base-model",
        provider_name: str = "base",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs: Any,
    ):
        self.model_name = model_name
        self.provider_name = provider_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_config: Dict[str, Any] = kwargs

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Synchronously generate a response from the foundation model.

        Args:
            prompt: Input user prompt containing the de-identified clinical text.
            system_prompt: Optional system instructions guiding clinical summarization,
                           extraction, or Q&A.
            **kwargs: Provider-specific inference overrides.

        Returns:
            str: Generated completion containing surrogate tokens.
        """
        pass

    @abstractmethod
    async def agenerate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Asynchronously generate a response from the foundation model.

        Args:
            prompt: Input user prompt containing the de-identified clinical text.
            system_prompt: Optional system instructions guiding clinical summarization,
                           extraction, or Q&A.
            **kwargs: Provider-specific inference overrides.

        Returns:
            str: Generated completion containing surrogate tokens.
        """
        pass
