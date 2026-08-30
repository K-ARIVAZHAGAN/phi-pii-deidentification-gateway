"""
Interactive Command-Line Interface for PHI/PII De-Identification Gateway.
Supports single-note processing, file ingestion, adapter selection, and interactive REPL mode.
"""

import argparse
import json
import os
import sys
from typing import Optional

from deid_gateway.adapters.anthropic_adapter import AnthropicAdapter
from deid_gateway.adapters.base import BaseLLMAdapter
from deid_gateway.adapters.gemini_adapter import GeminiAdapter
from deid_gateway.adapters.mock_adapter import MockLLMAdapter
from deid_gateway.adapters.openai_adapter import OpenAIAdapter
from deid_gateway.core.config import DeidConfig
from deid_gateway.core.models.model_card import get_parameter_count
from deid_gateway.gateway import DeidGateway, GatewayResult


class CLIColors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


def build_adapter(provider: str, mode: str = "summarize", api_key: Optional[str] = None) -> BaseLLMAdapter:
    """Instantiate selected adapter with fallback."""
    provider_clean = (provider or "mock").lower()
    if provider_clean == "mock":
        return MockLLMAdapter(mode=mode)
    elif provider_clean == "openai":
        return OpenAIAdapter(api_key=api_key)
    elif provider_clean == "anthropic":
        return AnthropicAdapter(api_key=api_key)
    elif provider_clean in ("gemini", "google"):
        return GeminiAdapter(api_key=api_key)
    else:
        print(f"{CLIColors.YELLOW}Warning: Unknown provider '{provider}', defaulting to Mock adapter.{CLIColors.END}")
        return MockLLMAdapter(mode=mode)


def process_and_display_note(
    raw_note: str,
    gateway: DeidGateway,
    task_prompt: str = "Please summarize this clinical note:\n\n{text}",
    as_json: bool = False,
) -> GatewayResult:
    """Executes gateway and renders formatted output."""
    result = gateway.process(clinical_note=raw_note, task_prompt=task_prompt)

    if as_json:
        print(json.dumps(result.to_dict(), indent=2))
        return result

    print(f"\n{CLIColors.BOLD}{CLIColors.CYAN}{'='*75}")
    print("  DE-IDENTIFICATION GATEWAY PIPELINE EXECUTION")
    print(f"{'='*75}{CLIColors.END}\n")

    print(f"{CLIColors.BOLD}[1] RAW INPUT NOTE:{CLIColors.END}")
    print(f"{CLIColors.YELLOW}{raw_note.strip()}{CLIColors.END}\n")

    print(f"{CLIColors.BOLD}[2] DE-IDENTIFIED TEXT (Delivered to Foundation LLM):{CLIColors.END}")
    print(f"{CLIColors.CYAN}{result.masked_input.strip()}{CLIColors.END}\n")

    print(f"{CLIColors.BOLD}[3] ISOLATED SESSION MAPPINGS ({result.entity_count} entities):{CLIColors.END}")
    token_map = result.mapping.get("token_to_original", {})
    if token_map:
        for tok, orig in sorted(token_map.items()):
            print(f"    {tok:<16} ->  {orig}")
    else:
        print("    (No PHI detected)")
    print()

    print(f"{CLIColors.BOLD}[4] FOUNDATION LLM COMPLETION:{CLIColors.END}")
    print(f"{CLIColors.BLUE}{result.raw_llm_response.strip()}{CLIColors.END}\n")

    print(f"{CLIColors.BOLD}[5] FINAL REHYDRATED RESPONSE:{CLIColors.END}")
    print(f"{CLIColors.GREEN}{result.final_text.strip()}{CLIColors.END}\n")

    print(f"{CLIColors.BOLD}[6] TELEMETRY:{CLIColors.END}")
    print(f"    - De-ID Latency : {result.deid_latency_ms:.2f} ms")
    print(f"    - LLM Latency   : {result.llm_latency_ms:.2f} ms")
    print(f"    - Rehydrate Time: {result.rehydrate_latency_ms:.2f} ms")
    print(f"    - Total Latency : {result.latency_ms:.2f} ms")
    print(f"    - Zero-Leak     : {'PASS' if result.leak_check_passed else 'FAIL'}")
    print(f"{CLIColors.CYAN}{'='*75}{CLIColors.END}\n")

    return result


def interactive_repl(gateway: DeidGateway) -> None:
    """Runs an interactive REPL session."""
    print(f"\n{CLIColors.BOLD}{CLIColors.GREEN}=== De-Identification Gateway Interactive REPL ==={CLIColors.END}")
    print("Paste clinical notes to de-identify and rehydrate in real time.")
    print("Type 'exit' or 'quit' to terminate.\n")

    while True:
        try:
            print(f"{CLIColors.BOLD}Enter clinical note (end with blank line):{CLIColors.END}")
            lines = []
            while True:
                line = input()
                if line.strip() in ("exit", "quit") and not lines:
                    print("Exiting interactive REPL.")
                    return
                if not line.strip() and lines:
                    break
                if line.strip() or lines:
                    lines.append(line)

            if not lines:
                continue

            raw_note = "\n".join(lines)
            process_and_display_note(raw_note, gateway)

        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break


def run_cli(args: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(
        description="HIPAA Safe Harbor PHI/PII De-Identification & Rehydration Gateway CLI"
    )
    parser.add_argument("--note", "-n", type=str, help="Direct clinical note text string")
    parser.add_argument("--file", "-f", type=str, help="Path to clinical note text file")
    parser.add_argument(
        "--adapter", "-a", type=str, default="mock",
        choices=["mock", "openai", "anthropic", "gemini"],
        help="Foundation LLM adapter provider (default: mock)"
    )
    parser.add_argument("--mode", "-m", type=str, default="summarize", help="Mock task mode: summarize, qa, extract")
    parser.add_argument("--prompt", "-p", type=str, default="Please summarize this clinical note:\n\n{text}", help="Task prompt template")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive terminal REPL")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--api-key", type=str, help="API key for cloud adapter if not set in environment")

    parsed = parser.parse_args(args)

    adapter = build_adapter(parsed.adapter, mode=parsed.mode, api_key=parsed.api_key)
    gateway = DeidGateway(adapter=adapter)

    if parsed.interactive:
        interactive_repl(gateway)
    elif parsed.file:
        if not os.path.exists(parsed.file):
            print(f"{CLIColors.RED}Error: File not found: {parsed.file}{CLIColors.END}", file=sys.stderr)
            sys.exit(1)
        with open(parsed.file, "r", encoding="utf-8") as f:
            note_content = f.read()
        process_and_display_note(note_content, gateway, task_prompt=parsed.prompt, as_json=parsed.json)
    elif parsed.note:
        process_and_display_note(parsed.note, gateway, task_prompt=parsed.prompt, as_json=parsed.json)
    else:
        # If no arguments provided, execute default roundtrip demo
        from deid_gateway.demo.demo_roundtrip import run_roundtrip_demo
        run_roundtrip_demo()


def main() -> None:
    run_cli()


if __name__ == "__main__":
    main()
