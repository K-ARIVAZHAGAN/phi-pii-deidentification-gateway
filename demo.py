#!/usr/bin/env python3
"""
Root entry point to run the PHI/PII De-Identification Gateway Demo.
Usage:
    python demo.py
    python demo.py --help
    python demo.py --interactive
"""

import sys
from deid_gateway.demo.demo_cli import run_cli

if __name__ == "__main__":
    run_cli(sys.argv[1:])
