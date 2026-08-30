"""
FastAPI Service module for PHI/PII De-Identification Gateway.
"""

from deid_gateway.api.server import app, create_app

__all__ = ["app", "create_app"]
