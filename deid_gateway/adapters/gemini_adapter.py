"""
Google Gemini Foundation LLM Adapter.
Integrates with Google GenAI SDK (Gemini 1.5 Pro, Gemini 1.5 Flash).
"""

import asyncio
import os
from typing import Any, Dict, Optional

from deid_gateway.adapters.base import BaseLLMAdapter


class GeminiAdapter(BaseLLMAdapter):
    """
    Adapter for Google Gemini foundation models using the google-genai or google-generativeai SDK.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-flash",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        client: Optional[Any] = None,
        **kwargs: Any,
    ):
        super().__init__(
            model_name=model_name,
            provider_name="gemini",
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        resolved_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )
        if client is None and not resolved_key:
            raise ValueError(
                "Gemini API key must be provided or set in GEMINI_API_KEY / GOOGLE_API_KEY environment variable."
            )

        self.api_key = resolved_key
        self.client = client

        if self.client is None and resolved_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=resolved_key)
            except ImportError:
                try:
                    import google.generativeai as genai_legacy
                    genai_legacy.configure(api_key=resolved_key)
                    self.client = genai_legacy.GenerativeModel(model_name=self.model_name)
                except ImportError:
                    pass

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Synchronously invoke Google Gemini API."""
        if self.client is None:
            raise RuntimeError(
                "Gemini client is not initialized. Please provide a client or install 'google-genai' package."
            )

        model = kwargs.get("model", self.model_name)
        contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        if hasattr(self.client, "models") and hasattr(self.client.models, "generate_content"):
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
            )
            return response.text if hasattr(response, "text") else str(response)
        elif hasattr(self.client, "generate_content"):
            response = self.client.generate_content(contents)
            return response.text if hasattr(response, "text") else str(response)
        else:
            raise RuntimeError("Unsupported Gemini client interface.")

    async def agenerate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Asynchronously invoke Google Gemini API."""
        return await asyncio.to_thread(self.generate, prompt, system_prompt=system_prompt, **kwargs)
