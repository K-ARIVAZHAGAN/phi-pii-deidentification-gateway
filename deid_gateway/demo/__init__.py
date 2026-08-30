"""
Demonstration and CLI package for PHI/PII De-Identification Gateway.
"""

from deid_gateway.demo.demo_cli import run_cli
from deid_gateway.demo.demo_roundtrip import run_roundtrip_demo

__all__ = ["run_cli", "run_roundtrip_demo"]
