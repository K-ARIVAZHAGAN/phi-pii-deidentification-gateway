"""
Sub-1B parameter sequence labeling and token classification models package.
"""

from deid_gateway.core.models.classifier import EntitySpan, HybridTokenClassifier
from deid_gateway.core.models.model_card import (
    DeidModelCard,
    LayerParameterBreakdown,
    get_model_card,
    get_parameter_count,
)

__all__ = [
    "EntitySpan",
    "HybridTokenClassifier",
    "DeidModelCard",
    "LayerParameterBreakdown",
    "get_model_card",
    "get_parameter_count",
]
