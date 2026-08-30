"""
Core PHI/PII De-Identification & Rehydration Engine.
"""

from deid_gateway.core.collision_guard import CollisionGuard
from deid_gateway.core.config import DeidConfig
from deid_gateway.core.date_shifter import DateShifter, DateShiftResult
from deid_gateway.core.deidentify import deidentify
from deid_gateway.core.eponyms import EponymDisambiguator
from deid_gateway.core.models.classifier import EntitySpan, HybridTokenClassifier
from deid_gateway.core.models.model_card import (
    DeidModelCard,
    get_model_card,
    get_parameter_count,
)
from deid_gateway.core.pseudonymizer import Pseudonymizer
from deid_gateway.core.rehydrate import rehydrate

__all__ = [
    "deidentify",
    "rehydrate",
    "DeidConfig",
    "Pseudonymizer",
    "DateShifter",
    "DateShiftResult",
    "EponymDisambiguator",
    "CollisionGuard",
    "HybridTokenClassifier",
    "EntitySpan",
    "DeidModelCard",
    "get_model_card",
    "get_parameter_count",
]
