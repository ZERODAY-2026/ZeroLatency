"""Diagnostic script to verify local Ollama connectivity and model inference.

Priority 0 of Antigravity Implementation Plan.
Usage:
    python -m scripts.ollama_check [--model gemma3n:e2b]
"""

import argparse
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.config import SUPPORTED_MODELS, settings
from src.errors import OllamaUnavailable, UnsupportedModel
from src.gemma_client import OllamaClient
from src.models import validate_model


def run_diagnostic(model_name: str | None = None) -> int:
    target_model = model_name or settings.model
    print("=" * 60)
    print("OLLAMA LOCAL CONNECTION DIAGNOSTIC")
    print("=" * 60)
    print(f"Target Loopback URL : {settings.ollama_url}")
    print(f"Target Model        : {target_model}")
    print("-" * 60)

    try:
        validated = validate_model(target_model)
    except UnsupportedModel as err:
        print(f"[FAIL] Unsupported model: {err}")
        return 1

    client = OllamaClient(settings, model=validated)

    # 1. Reachability & Version
    print("[1/3] Checking Ollama service reachability...", end=" ", flush=True)
    try:
        version = client.version()
        print(f"PASS (v{version})")
    except OllamaUnavailable:
        print("FAIL")
        print("\n[RESULT] FAIL - OLLAMA NOT REACHABLE")
        print("Action required: Start Ollama by running 'ollama serve' in your terminal.")
        return 1
    except Exception as exc:
        print(f"FAIL ({exc})")
        return 1

    # 2. Installed models check
    print("[2/3] Checking installed models...", end=" ", flush=True)
    try:
        installed = client.installed_models()
        print(f"PASS ({len(installed)} installed: {', '.join(installed) if installed else 'None'})")
    except Exception as exc:
        print(f"FAIL ({exc})")
        return 1

    installed_set = set(installed)
    model_matches = {target_model, f"{target_model}:latest"} & installed_set
    if not model_matches:
        print("\n[RESULT] PARTIAL - OLLAMA REACHABLE, SELECTED MODEL MISSING")
        print(f"Target model '{target_model}' is not installed.")
        print(f"Action required: Run 'ollama pull {target_model}'")
        return 1

    # 3. Non-sensitive test inference
    print(f"[3/3] Testing inference with '{target_model}'...", end=" ", flush=True)
    prompt = "Reply with exactly: LOCAL_MODEL_OK"
    started = time.perf_counter()
    try:
        _ = client.chat_json(
            system="You are a helpful assistant.",
            user=prompt,
            schema={"type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"]},
        )
        duration = round(time.perf_counter() - started, 3)
        print(f"PASS ({duration}s)")
    except Exception as exc:
        print(f"FAIL ({exc})")
        print(f"\n[RESULT] FAIL - Model failed to generate output: {exc}")
        return 1

    print("-" * 60)
    print("[RESULT] PASS - LOCAL OLLAMA REACHABLE AND SELECTED MODEL INFERRED")
    print(f"Model ID : {target_model}")
    print(f"Latency  : {duration}s")
    print("=" * 60)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ollama connectivity and model diagnostic")
    parser.add_argument("--model", choices=list(SUPPORTED_MODELS), default=None, help="Model to test")
    args = parser.parse_args(argv)
    return run_diagnostic(args.model)


if __name__ == "__main__":
    raise SystemExit(main())
