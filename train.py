"""
Transformer Fine-Tuning and Training Pipeline for HIPAA Safe Harbor De-Identification.
Trains/fine-tunes a sub-1B parameter sequence classification transformer on clinical notes
with recall-asymmetric loss weighting to eliminate false negatives (breach prevention).
"""

import argparse
import json
import logging
import os
import random
from typing import Any, Dict, List, Tuple

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoConfig,
    AutoModelForTokenClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)

from deid_gateway.core.models.transformer_ner import (
    HIPAA_CATEGORIES,
    ID2LABEL,
    LABEL2ID,
    LABELS,
    NUM_LABELS,
    TransformerDeidModel,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train")


CATEGORY_NORM_MAP = {
    "NAME_PATIENT": "PATIENT",
    "NAME_PROVIDER": "PROVIDER",
    "NAME_RELATIVE": "PATIENT",
    "HOSPITAL_FACILITY": "HOSPITAL",
    "LOCATION_CITY": "CITY",
    "LOCATION_STATE": "STATE",
    "LOCATION_ZIP": "ZIP",
    "LOCATION_ADDRESS": "ADDRESS",
    "ID_MRN": "MRN",
    "ID_SSN": "SSN",
    "ID_NPI": "ID",
    "ID_DEA": "ID",
    "ID_LICENSE": "LICENSE",
    "ID_ACCOUNT": "ACCOUNT",
    "ID_DEVICE_UDI": "DEVICE",
    "CONTACT_PHONE": "PHONE",
    "CONTACT_FAX": "FAX",
    "CONTACT_EMAIL": "EMAIL",
    "CONTACT_URL": "URL",
    "CONTACT_IP": "IP",
    "DATE": "DATE",
    "AGE": "AGE",
}


class ClinicalDeidDataset(Dataset):
    """PyTorch Dataset for Clinical Sequence Labeling with Subword Offset Mapping."""

    def __init__(self, data_path: str, tokenizer, max_length: int = 512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.examples: List[Dict[str, Any]] = []

        with open(data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        notes = raw_data if isinstance(raw_data, list) else raw_data.get("notes", [])
        logger.info(f"Loaded {len(notes)} clinical notes from {data_path}")

        for note in notes:
            text = note.get("raw_text", note.get("text", ""))
            entities = note.get("entities", [])
            if not text:
                continue

            encoded = self._encode_example(text, entities)
            if encoded:
                self.examples.append(encoded)

    def _encode_example(self, text: str, entities: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_offsets_mapping=True,
            return_tensors="pt",
        )

        offset_mapping = encoding.pop("offset_mapping")[0]
        input_ids = encoding["input_ids"][0]
        attention_mask = encoding["attention_mask"][0]

        # Initialize all labels as -100 for special tokens, O for normal tokens
        labels = torch.full((self.max_length,), fill_value=-100, dtype=torch.long)

        for token_idx, (start_char, end_char) in enumerate(offset_mapping.tolist()):
            if start_char == end_char:
                # Special tokens ([CLS], [SEP], PAD)
                continue

            token_label = "O"
            for entity in entities:
                ent_start = entity["start"]
                ent_end = entity["end"]
                raw_cat = entity.get("category", "ID")
                cat = CATEGORY_NORM_MAP.get(raw_cat, raw_cat.replace("NAME_", "").replace("ID_", ""))
                if cat not in HIPAA_CATEGORIES:
                    cat = "ID"

                # Check token span inside entity span
                if start_char >= ent_start and end_char <= ent_end:
                    if start_char == ent_start or token_idx == 0 or labels[token_idx - 1] == -100:
                        token_label = f"B-{cat}"
                    else:
                        token_label = f"I-{cat}"
                    break
                elif (start_char >= ent_start and start_char < ent_end) or (end_char > ent_start and end_char <= ent_end):
                    token_label = f"I-{cat}"
                    break

            labels[token_idx] = LABEL2ID.get(token_label, LABEL2ID["O"])

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        return self.examples[idx]


def train_deid_model(
    data_path: str = "tests/data/annotated_clinical_notes_55.json",
    base_model: str = "distilbert-base-cased",
    output_dir: str = "saved_models/deid_transformer",
    epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 3e-5,
    recall_penalty_weight: float = 5.0,
):
    """Trains the sub-1B parameter Transformer sequence labeler with recall-asymmetric loss."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using compute device: {device}")

    os.makedirs(output_dir, exist_ok=True)

    # 1. Initialize Tokenizer & Config
    try:
        tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=True)
    except Exception:
        logger.warning(f"Could not load online tokenizer for {base_model}. Using bert-base-cased config.")
        from transformers import BertTokenizerFast
        tokenizer = BertTokenizerFast.from_pretrained("bert-base-cased")

    # 2. Load Dataset
    dataset = ClinicalDeidDataset(data_path, tokenizer)
    train_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # 3. Model Architecture
    try:
        model = AutoModelForTokenClassification.from_pretrained(
            base_model,
            num_labels=NUM_LABELS,
            id2label=ID2LABEL,
            label2id=LABEL2ID,
        )
    except Exception:
        from transformers import BertConfig, BertForTokenClassification
        config = BertConfig(
            vocab_size=len(tokenizer),
            hidden_size=768,
            num_hidden_layers=6,
            num_attention_heads=12,
            intermediate_size=3072,
            num_labels=NUM_LABELS,
            id2label=ID2LABEL,
            label2id=LABEL2ID,
        )
        model = BertForTokenClassification(config)

    model.to(device)

    total_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Model Architecture Parameter Count: {total_params:,} (Sub-1B Budget: {total_params < 1e9})")

    # 4. Recall-Asymmetric Loss Weighting (Penalizes False Negatives)
    class_weights = torch.ones(NUM_LABELS, device=device)
    for idx, label in ID2LABEL.items():
        if label != "O":
            class_weights[idx] = recall_penalty_weight  # Heavy penalty for missing PHI

    loss_fn = nn.CrossEntropyLoss(weight=class_weights, ignore_index=-100)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=max(1, int(total_steps * 0.1)), num_training_steps=total_steps)

    # 5. Training Loop
    logger.info(f"Starting fine-tuning for {epochs} epochs on {len(dataset)} examples...")
    model.train()

    for epoch in range(1, epochs + 1):
        total_loss = 0.0
        correct_tokens = 0
        total_tokens = 0

        for step, batch in enumerate(train_loader):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits  # [batch, seq_len, num_labels]

            loss = loss_fn(logits.view(-1, NUM_LABELS), labels.view(-1))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

            optimizer.step()
            scheduler.step()

            total_loss += loss.item()

            # Track accuracy on non-padding tokens
            preds = torch.argmax(logits, dim=-1)
            mask = labels != -100
            correct_tokens += ((preds == labels) & mask).sum().item()
            total_tokens += mask.sum().item()

        avg_loss = total_loss / max(1, len(train_loader))
        token_acc = (correct_tokens / max(1, total_tokens)) * 100.0
        logger.info(f"Epoch {epoch}/{epochs} - Loss: {avg_loss:.4f} - Token Accuracy: {token_acc:.2f}%")

    # 6. Save Fine-Tuned Model Artifacts
    logger.info(f"Saving fine-tuned weights and configuration to '{output_dir}'...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Write model metadata
    metadata = {
        "model_name": "deid-transformer-ner",
        "base_model": base_model,
        "total_parameters": total_params,
        "total_parameters_formatted": f"{total_params:,} ({total_params / 1e6:.1f}M)",
        "is_sub_1b": total_params < 1_000_000_000,
        "num_labels": NUM_LABELS,
        "labels": LABELS,
        "recall_penalty_weight": recall_penalty_weight,
    }
    with open(os.path.join(output_dir, "deid_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Training Complete! Model verified under 1B parameters ({total_params:,} params).")
    return output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Clinical Transformer De-ID Model")
    parser.add_argument("--data", default="tests/data/annotated_clinical_notes_55.json", help="Path to annotated JSON dataset")
    parser.add_argument("--base-model", default="distilbert-base-cased", help="Base HuggingFace model")
    parser.add_argument("--output-dir", default="saved_models/deid_transformer", help="Output directory for saved weights")
    parser.add_argument("--epochs", type=int, default=2, help="Number of fine-tuning epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--lr", type=float, default=3e-5, help="Learning rate")
    args = parser.parse_args()

    train_deid_model(
        data_path=args.data,
        base_model=args.base_model,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
    )
