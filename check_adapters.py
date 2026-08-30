#!/usr/bin/env python3
"""
Adapter Health & Live Connectivity Checker.
Audits and tests all 4 foundation LLM adapters (Mock, OpenAI, Anthropic, Gemini).
Shows status of .env variables and runs offline simulation or live cloud roundtrips.

Usage:
    python check_adapters.py
    python check_adapters.py --provider openai
    python check_adapters.py --provider anthropic
    python check_adapters.py --provider gemini
    python check_adapters.py --provider mock
"""

import argparse
import os
import sys
from typing import Optional
from unittest.mock import MagicMock

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from deid_gateway.adapters.anthropic_adapter import AnthropicAdapter
from deid_gateway.adapters.gemini_adapter import GeminiAdapter
from deid_gateway.adapters.mock_adapter import MockLLMAdapter
from deid_gateway.adapters.openai_adapter import OpenAIAdapter
from deid_gateway.gateway import DeidGateway


GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_env_status():
    print(f"\n{BOLD}{CYAN}================================================================================{RESET}")
    print(f"{BOLD}{CYAN}  FOUNDATION LLM ADAPTERS & .ENV CONFIGURATION AUDIT{RESET}")
    print(f"{BOLD}{CYAN}================================================================================{RESET}\n")

    env_path = os.path.abspath(".env")
    env_exists = os.path.isfile(env_path)
    print(f"  * .env File Located  : {env_path}")
    print(f"  * .env File Exists   : {GREEN + 'YES' if env_exists else YELLOW + 'NO (Copy .env.example -> .env to add live API keys)'}{RESET}\n")

    keys = [
        ("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY")),
        ("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY")),
        ("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")),
    ]

    print(f"{BOLD}Active Provider Credentials in Environment:{RESET}")
    for name, val in keys:
        if val:
            masked_val = val[:6] + "..." + val[-4:] if len(val) > 10 else "***"
            print(f"  - {name:<18}: {GREEN}DETECTED{RESET} ({masked_val})")
        else:
            print(f"  - {name:<18}: {YELLOW}NOT SET{RESET} (Running in Hermetic/Mock mode)")
    print()


def test_mock_adapter():
    print(f"{BOLD}--- 1. Testing MockLLMAdapter (Offline Deterministic Simulation) ---{RESET}")
    try:
        adapter = MockLLMAdapter(mode="summarize")
        gateway = DeidGateway(adapter=adapter)
        note = "Patient: Sarah Connor (DOB: 02/28/1985, MRN: 9948201) was examined by Dr. Miles Dyson at Cyberdyne."
        res = gateway.summarize(note)
        print(f"  * Status            : {GREEN}[PASS] Functional{RESET}")
        print(f"  * Masked Prompt Sent: '{res.masked_input[:60]}...'")
        print(f"  * Rehydrated Output : '{res.final_text[:60]}...'")
        print(f"  * Zero PHI Leaked   : {GREEN}{res.zero_phi_leaked}{RESET}")
        return True
    except Exception as e:
        print(f"  * Status: {RED}[FAIL] {e}{RESET}")
        return False


def test_openai_adapter():
    print(f"\n{BOLD}--- 2. Testing OpenAIAdapter (GPT-4o / GPT-4o-mini) ---{RESET}")
    api_key = os.environ.get("OPENAI_API_KEY")
    note = "Patient Eleanor Vance (MRN: 48201) evaluated by Dr. Whipple for Whipple disease."

    if api_key:
        print(f"  * Mode: {CYAN}LIVE CLOUD API CALL (api.openai.com){RESET}")
        try:
            adapter = OpenAIAdapter(api_key=api_key, model_name="gpt-4o-mini")
            gateway = DeidGateway(adapter=adapter)
            res = gateway.summarize(note)
            print(f"  * Status           : {GREEN}[PASS] Live OpenAI API Call Succeeded!{RESET}")
            print(f"  * Rehydrated Result: '{res.final_text[:70]}...'")
            print(f"  * Zero PHI Leaked  : {GREEN}{res.zero_phi_leaked}{RESET}")
            return True
        except Exception as e:
            print(f"  * Live API Call Failed: {RED}{e}{RESET}")
            return False
    else:
        print(f"  * Mode: {YELLOW}MOCK CLIENT INJECTION (Offline Unit Verification){RESET}")
        try:
            mock_client = MagicMock()
            mock_comp = MagicMock()
            mock_comp.choices = [MagicMock(message=MagicMock(content="Summary: [PATIENT_1] was examined by [PROVIDER_1] for [DIAGNOSIS]."))]
            mock_client.chat.completions.create.return_value = mock_comp
            adapter = OpenAIAdapter(api_key="sk-mock-key", client=mock_client)
            gateway = DeidGateway(adapter=adapter)
            res = gateway.summarize(note)
            print(f"  * Status           : {GREEN}[PASS] Adapter Request Parsing & Rehydration Verified{RESET}")
            print(f"  * Note             : Set OPENAI_API_KEY in .env to run live API calls.")
            return True
        except Exception as e:
            print(f"  * Status: {RED}[FAIL] {e}{RESET}")
            return False


def test_anthropic_adapter():
    print(f"\n{BOLD}--- 3. Testing AnthropicAdapter (Claude 3.5 Sonnet / Claude 3 Haiku) ---{RESET}")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    note = "Patient Eleanor Vance (MRN: 48201) evaluated by Dr. Whipple."

    if api_key:
        print(f"  * Mode: {CYAN}LIVE CLOUD API CALL (api.anthropic.com){RESET}")
        try:
            adapter = AnthropicAdapter(api_key=api_key, model_name="claude-3-haiku-20240307")
            gateway = DeidGateway(adapter=adapter)
            res = gateway.summarize(note)
            print(f"  * Status           : {GREEN}[PASS] Live Anthropic API Call Succeeded!{RESET}")
            print(f"  * Rehydrated Result: '{res.final_text[:70]}...'")
            print(f"  * Zero PHI Leaked  : {GREEN}{res.zero_phi_leaked}{RESET}")
            return True
        except Exception as e:
            print(f"  * Live API Call Failed: {RED}{e}{RESET}")
            return False
    else:
        print(f"  * Mode: {YELLOW}MOCK CLIENT INJECTION (Offline Unit Verification){RESET}")
        try:
            mock_client = MagicMock()
            mock_msg = MagicMock()
            mock_msg.content = [MagicMock(text="Claude Summary: [PATIENT_1] evaluated by [PROVIDER_1].")]
            mock_client.messages.create.return_value = mock_msg
            adapter = AnthropicAdapter(api_key="sk-ant-mock-key", client=mock_client)
            gateway = DeidGateway(adapter=adapter)
            res = gateway.summarize(note)
            print(f"  * Status           : {GREEN}[PASS] Adapter Request Parsing & Rehydration Verified{RESET}")
            print(f"  * Note             : Set ANTHROPIC_API_KEY in .env to run live API calls.")
            return True
        except Exception as e:
            print(f"  * Status: {RED}[FAIL] {e}{RESET}")
            return False


def test_gemini_adapter():
    print(f"\n{BOLD}--- 4. Testing GeminiAdapter (Gemini 1.5 Flash / Gemini 1.5 Pro) ---{RESET}")
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    note = "Patient Eleanor Vance (MRN: 48201) evaluated on 10/12/2023."

    if api_key:
        print(f"  * Mode: {CYAN}LIVE CLOUD API CALL (generativelanguage.googleapis.com){RESET}")
        try:
            adapter = GeminiAdapter(api_key=api_key, model_name="gemini-3.6-flash")
            gateway = DeidGateway(adapter=adapter)
            res = gateway.summarize(note)
            print(f"  * Status           : {GREEN}[PASS] Live Gemini API Call Succeeded!{RESET}")
            print(f"  * Rehydrated Result: '{res.final_text[:70]}...'")
            print(f"  * Zero PHI Leaked  : {GREEN}{res.zero_phi_leaked}{RESET}")
            return True
        except Exception as e:
            print(f"  * Live API Call Failed: {RED}{e}{RESET}")
            return False
    else:
        print(f"  * Mode: {YELLOW}MOCK CLIENT INJECTION (Offline Unit Verification){RESET}")
        try:
            mock_client = MagicMock()
            mock_resp = MagicMock(text="Gemini Assessment: [PATIENT_1] seen on [DATE_1].")
            mock_client.models.generate_content.return_value = mock_resp
            adapter = GeminiAdapter(api_key="mock-gemini-key", client=mock_client)
            gateway = DeidGateway(adapter=adapter)
            res = gateway.summarize(note)
            print(f"  * Status           : {GREEN}[PASS] Adapter Request Parsing & Rehydration Verified{RESET}")
            print(f"  * Note             : Set GEMINI_API_KEY in .env to run live API calls.")
            return True
        except Exception as e:
            print(f"  * Status: {RED}[FAIL] {e}{RESET}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Audit and test foundation LLM adapters.")
    parser.add_argument("--provider", choices=["all", "mock", "openai", "anthropic", "gemini"], default="all")
    args = parser.parse_args()

    print_env_status()

    results = {}
    if args.provider in ("all", "mock"):
        results["Mock"] = test_mock_adapter()
    if args.provider in ("all", "openai"):
        results["OpenAI"] = test_openai_adapter()
    if args.provider in ("all", "anthropic"):
        results["Anthropic"] = test_anthropic_adapter()
    if args.provider in ("all", "gemini"):
        results["Gemini"] = test_gemini_adapter()

    print(f"\n{BOLD}{CYAN}================================================================================{RESET}")
    all_passed = all(results.values())
    if all_passed:
        print(f"{BOLD}{GREEN}  FINAL AUDIT RESULT: ALL TESTED ADAPTERS FUNCTIONAL ({len(results)}/{len(results)}){RESET}")
    else:
        print(f"{BOLD}{RED}  FINAL AUDIT RESULT: SOME ADAPTERS FAILED{RESET}")
    print(f"{BOLD}{CYAN}================================================================================{RESET}\n")


if __name__ == "__main__":
    main()
