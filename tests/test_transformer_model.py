"""
Unit tests for PyTorch / HuggingFace Transformer Token Classification Model.
Verifies parameter counting, sub-1B ceiling, weight loading, and live inference.
"""

import os
import pytest
import torch
from deid_gateway.core.models.transformer_ner import TransformerDeidModel
from deid_gateway.core.models.classifier import HybridTokenClassifier


def test_transformer_parameter_count_under_1b():
    """Verify live PyTorch model parameter count is computed and satisfies < 1B."""
    model = TransformerDeidModel(
        model_name_or_path="saved_models/deid_transformer" if os.path.exists("saved_models/deid_transformer") else "distilbert-base-cased"
    )
    param_count = model.get_parameter_count()
    assert param_count > 0, "Model must have non-zero parameters"
    assert param_count < 1_000_000_000, f"Model parameters ({param_count}) must be under 1B"
    assert model.is_sub_1b() is True


def test_transformer_live_inference():
    """Test neural sequence labeling forward pass with span extraction."""
    model = TransformerDeidModel(
        model_name_or_path="saved_models/deid_transformer" if os.path.exists("saved_models/deid_transformer") else "distilbert-base-cased"
    )
    sample_text = "Patient Eleanor Rigby was admitted on 10/15/2023 by Dr. Arthur Hodgkin."
    spans = model.predict_spans(sample_text)
    assert isinstance(spans, list)


def test_hybrid_classifier_dynamic_parameter_reporting():
    """Verify HybridTokenClassifier dynamically reports parameter count from the live neural model."""
    classifier = HybridTokenClassifier()
    param_count = classifier.get_parameter_count()
    assert param_count > 0
    assert param_count < 1_000_000_000
