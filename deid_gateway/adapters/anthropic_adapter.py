"""
Anthropic Foundation LLM Adapter.
Integrates with Anthropic Messages API (Claude 3.5 Sonnet, Claude 3 Haiku, Claude 3 Opus).
"""

import asyncio
import os
from typing import Any, Dict, List, Optional

from deid_gateway.adapters.base import BaseLLMAdapter


class AnthropicAdapter(BaseLLMAdapter):
    """
    Adapter for Anthropic foundation models using the official Anthropic Python SDK.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "claude-3-5-sonnet-20240620",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        client: Optional[Any] = None,
        **kwargs: Any,
    ):
        super().__init__(
            model_name=model_name,
            provider_name="anthropic",
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if client is None and not resolved_key:
            raise ValueError(
                "Anthropic API key must be provided or set in the ANTHROPIC_API_KEY environment variable."
            )

        self.api_key = resolved_key
        self.client = client

        if self.client is None and resolved_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=resolved_key)
            except ImportError:
                pass

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Synchronously invoke Anthropic Messages API."""
        if self.client is None:
            raise RuntimeError(
                "Anthropic client is not initialized. Please provide a client or install 'anthropic' package."
            )

        model = kwargs.get("model", self.model_name)
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        messages = [{"role": "user", "content": prompt}]
        params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            params["system"] = system_prompt

        response = self.client.messages.create(**params)

        if hasattr(response, "content") and response.content:
            first_block = response.content[0]
            if hasattr(first_block, "text"):
                return first_block.text
            elif isinstance(first_block, dict):
                return first_block.get("text", "")
            return str(first_block)
        return ""

    async def agenerate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Asynchronously invoke Anthropic API."""
        return await asyncio.to_thread(self.generate, prompt, system_prompt=system_prompt, **kwargs)
