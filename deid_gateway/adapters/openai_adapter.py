"""
OpenAI Foundation LLM Adapter.
Integrates with OpenAI Chat Completions API (GPT-4o, GPT-4o-mini) and Azure OpenAI.
"""

import asyncio
import os
from typing import Any, Dict, List, Optional

from deid_gateway.adapters.base import BaseLLMAdapter


class OpenAIAdapter(BaseLLMAdapter):
    """
    Adapter for OpenAI foundation models using the official OpenAI Python SDK.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        client: Optional[Any] = None,
        **kwargs: Any,
    ):
        super().__init__(
            model_name=model_name,
            provider_name="openai",
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
        if client is None and not resolved_key:
            raise ValueError(
                "OpenAI API key must be provided or set in the OPENAI_API_KEY environment variable."
            )

        self.api_key = resolved_key
        self.client = client

        if self.client is None and resolved_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=resolved_key)
            except ImportError:
                # Client remains None until openai package is installed or client is injected
                pass

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Synchronously invoke OpenAI Chat Completions API."""
        if self.client is None:
            raise RuntimeError(
                "OpenAI client is not initialized. Please provide a client or install 'openai' package."
            )

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        model = kwargs.get("model", self.model_name)
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choice = response.choices[0]
        content = choice.message.content if hasattr(choice, "message") else choice.get("message", {}).get("content", "")
        return content or ""

    async def agenerate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Asynchronously invoke OpenAI API."""
        return await asyncio.to_thread(self.generate, prompt, system_prompt=system_prompt, **kwargs)
