# Enterprise Development & Automation Makefile for HIPAA De-ID Gateway

.PHONY: help install test verify demo train benchmark api clean docker-build docker-up

help:
	@echo "HIPAA Safe Harbor PHI/PII De-Identification Gateway"
	@echo "Available commands:"
	@echo "  make install      - Install package and dependencies"
	@echo "  make test         - Run full pytest test suite (189 tests)"
	@echo "  make verify       - Run 9-Agent automated verification suite"
	@echo "  make demo         - Run interactive end-to-end clinical demo"
	@echo "  make train        - Train/fine-tune PyTorch transformer model"
	@echo "  make benchmark    - Run baseline comparative benchmark evaluation"
	@echo "  make api          - Launch FastAPI REST server on port 8000"
	@echo "  make docker-build - Build production Docker image"
	@echo "  make docker-up    - Run container via docker-compose"
	@echo "  make clean        - Remove caches and build artifacts"

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/ -v

verify:
	python verify_all.py

demo:
	python demo.py

train:
	python train.py --epochs 3 --batch-size 4 --lr 3e-5

benchmark:
	python -m deid_gateway.benchmarks.run_benchmarks --dataset tests/data/annotated_clinical_notes_55.json --render-markdown

api:
	python -m uvicorn deid_gateway.api.server:app --host 0.0.0.0 --port 8000 --reload

docker-build:
	docker build -t deid-gateway:1.0.0 .

docker-up:
	docker compose up -d

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
