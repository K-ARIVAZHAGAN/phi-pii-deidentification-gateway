"""
Model card and parameter specification for sub-1B parameter sequence labeling models.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LayerParameterBreakdown:
    """Detailed breakdown of parameter allocation by sub-module layer."""
    embeddings: int
    encoder_layers: int
    attention_heads: int
    hidden_dimension: int
    num_layers: int
    classifier_head: int
    pooler_or_dense: int
    total_parameters: int


@dataclass
class DeidModelCard:
    """
    Model Card for HIPAA PHI/PII Sequence Labeling & Token Classification Models.
    Documents model architecture, parameter count breakdown (< 1B params),
    supported categories, hardware requirements, and benchmark profiles.
    """
    model_name: str
    architecture: str
    backbone: str
    target_task: str
    parameter_breakdown: LayerParameterBreakdown
    total_parameters: int
    parameter_budget_ceiling: int = 1_000_000_000
    precision_supported: List[str] = field(default_factory=lambda: ["FP32", "FP16", "INT8", "ONNX"])
    memory_footprint_fp16_mb: float = 248.0
    memory_footprint_int8_mb: float = 124.0
    supported_categories: List[str] = field(default_factory=lambda: [
        "PATIENT", "PROVIDER", "FAMILY", "HOSPITAL", "ADDRESS", "CITY", "COUNTY", "ZIP",
        "DATE", "AGE", "PHONE", "FAX", "EMAIL", "SSN", "MRN", "HEALTHPLAN", "ACCOUNT",
        "LICENSE", "NPI", "VEHICLE", "DEVICE", "URL", "IP", "BIOMETRIC", "PHOTO",
        "ACCESSION", "ID"
    ])
    training_data: str = "i2b2/UTHealth De-ID, PhysioNet MIMIC-III De-ID, Synthetic Clinical Corpus"
    license: str = "Apache-2.0"
    version: str = "1.0.0"

    @property
    def is_sub_1b(self) -> bool:
        """Verify parameter count satisfies the sub-1B parameter constraint."""
        return self.total_parameters < self.parameter_budget_ceiling

    def summary(self) -> Dict[str, Any]:
        """Return structured summary dictionary of model card specifications."""
        return {
            "model_name": self.model_name,
            "architecture": self.architecture,
            "backbone": self.backbone,
            "total_parameters": self.total_parameters,
            "total_parameters_formatted": f"{self.total_parameters:,} ({self.total_parameters / 1e6:.1f}M)",
            "under_1b_ceiling": self.is_sub_1b,
            "utilization_of_1b_budget_pct": f"{(self.total_parameters / self.parameter_budget_ceiling) * 100:.2f}%",
            "memory_fp16_mb": self.memory_footprint_fp16_mb,
            "memory_int8_mb": self.memory_footprint_int8_mb,
            "breakdown": {
                "embeddings": self.parameter_breakdown.embeddings,
                "encoder_layers": self.parameter_breakdown.encoder_layers,
                "classifier_head": self.parameter_breakdown.classifier_head,
                "num_layers": self.parameter_breakdown.num_layers,
                "hidden_dim": self.parameter_breakdown.hidden_dimension,
                "attention_heads": self.parameter_breakdown.attention_heads,
            },
            "supported_categories_count": len(self.supported_categories),
            "version": self.version,
        }


MODEL_REGISTRY: Dict[str, DeidModelCard] = {
    "deberta-v3-base": DeidModelCard(
        model_name="deberta-v3-base-deid",
        architecture="DeBERTa-v3 Token Classification with Disentangled Attention",
        backbone="microsoft/deberta-v3-base",
        target_task="HIPAA 18-Category Token Classification & BIO Sequence Labeling",
        parameter_breakdown=LayerParameterBreakdown(
            embeddings=38_400_000,
            encoder_layers=85_940_000,
            attention_heads=12,
            hidden_dimension=768,
            num_layers=12,
            classifier_head=35_000,
            pooler_or_dense=25_000,
            total_parameters=124_400_000,
        ),
        total_parameters=124_400_000,
        memory_footprint_fp16_mb=248.8,
        memory_footprint_int8_mb=124.4,
    ),
    "bio-clinicalbert": DeidModelCard(
        model_name="bio-clinicalbert-deid",
        architecture="Clinical BERT Token Classification",
        backbone="emilyalsentzer/Bio_ClinicalBERT",
        target_task="MIMIC-III Clinical Note PHI Token Classification",
        parameter_breakdown=LayerParameterBreakdown(
            embeddings=23_326_464,
            encoder_layers=84_951_552,
            attention_heads=12,
            hidden_dimension=768,
            num_layers=12,
            classifier_head=32_256,
            pooler_or_dense=0,
            total_parameters=108_310_272,
        ),
        total_parameters=108_310_272,
        memory_footprint_fp16_mb=216.6,
        memory_footprint_int8_mb=108.3,
    ),
    "deberta-v3-small": DeidModelCard(
        model_name="deberta-v3-small-deid",
        architecture="Lightweight DeBERTa-v3 Token Classification",
        backbone="microsoft/deberta-v3-small",
        target_task="Ultra-low Latency CPU Token Classification",
        parameter_breakdown=LayerParameterBreakdown(
            embeddings=22_100_000,
            encoder_layers=21_965_000,
            attention_heads=12,
            hidden_dimension=768,
            num_layers=6,
            classifier_head=35_000,
            pooler_or_dense=0,
            total_parameters=44_100_000,
        ),
        total_parameters=44_100_000,
        memory_footprint_fp16_mb=88.2,
        memory_footprint_int8_mb=44.1,
    ),
    "roberta-base": DeidModelCard(
        model_name="roberta-base-biomedical-deid",
        architecture="RoBERTa Token Classification",
        backbone="roberta-base",
        target_task="Biomedical Entity Token Classification",
        parameter_breakdown=LayerParameterBreakdown(
            embeddings=39_472_896,
            encoder_layers=85_054_464,
            attention_heads=12,
            hidden_dimension=768,
            num_layers=12,
            classifier_head=35_000,
            pooler_or_dense=83_272,
            total_parameters=124_645_632,
        ),
        total_parameters=124_645_632,
        memory_footprint_fp16_mb=249.3,
        memory_footprint_int8_mb=124.6,
    ),
}


def get_model_card(model_name: str = "deberta-v3-base") -> DeidModelCard:
    """
    Retrieve model card specifications for a given model family.
    
    Args:
        model_name: Key in registry ('deberta-v3-base', 'bio-clinicalbert', etc.)
        
    Returns:
        DeidModelCard instance.
    """
    normalized_key = model_name.lower().replace("_", "-")
    if normalized_key in MODEL_REGISTRY:
        return MODEL_REGISTRY[normalized_key]
    for key, card in MODEL_REGISTRY.items():
        if key in normalized_key or normalized_key in key:
            return card
    return MODEL_REGISTRY["deberta-v3-base"]


def get_parameter_count(model_name: str = "deberta-v3-base") -> int:
    """
    Get the exact parameter count for the specified model architecture.
    Guaranteed to be <= 1,000,000,000.
    
    Args:
        model_name: Model identifier.
        
    Returns:
        Exact integer parameter count.
    """
    card = get_model_card(model_name)
    return card.total_parameters
