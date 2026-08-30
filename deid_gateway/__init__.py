"""
HIPAA Safe Harbor PHI/PII De-Identification & Rehydration Gateway.
"""

from deid_gateway.adapters.anthropic_adapter import AnthropicAdapter
from deid_gateway.adapters.base import BaseLLMAdapter
from deid_gateway.adapters.gemini_adapter import GeminiAdapter
from deid_gateway.adapters.mock_adapter import MockLLMAdapter
from deid_gateway.adapters.openai_adapter import OpenAIAdapter
from deid_gateway.core.config import DeidConfig
from deid_gateway.core.deidentify import deidentify
from deid_gateway.core.rehydrate import rehydrate
from deid_gateway.gateway import DeidGateway, GatewayResult

__version__ = "1.0.0"

__all__ = [
    "deidentify",
    "rehydrate",
    "DeidConfig",
    "DeidGateway",
    "GatewayResult",
    "BaseLLMAdapter",
    "MockLLMAdapter",
    "OpenAIAdapter",
    "AnthropicAdapter",
    "GeminiAdapter",
    "__version__",
]
