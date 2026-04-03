"""
LLM Router for Relay.

USE_LOCAL_LLM=true  → Ollama (free, OpenAI-compatible API)
USE_LOCAL_LLM=false → OpenAI (gpt-5.4-nano for gap detection, gpt-5.4-mini for generation)

Ollama exposes an OpenAI-compatible endpoint, so the same client works for both —
only the base_url, api_key, and model name differ.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import openai
import config

DEFAULT_LOCAL_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
NANO_MODEL  = config.NANO_MODEL
MINI_MODEL  = config.MINI_MODEL
HQ_MODEL    = config.HQ_MODEL
GAP_MODEL   = "claude-haiku-4-5-20251001"  # Anthropic; used for gap detection on API


def _ollama_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def is_local() -> bool:
    return os.getenv("USE_LOCAL_LLM", "false").lower() == "true"


def get_client() -> openai.OpenAI:
    """Return an OpenAI-compatible client for whichever provider is active."""
    if is_local():
        return openai.OpenAI(
            base_url=f"{_ollama_url()}/v1",
            api_key="ollama",
        )
    return openai.OpenAI(api_key=config.OPENAI_API_KEY)


def gap_model() -> str:
    return DEFAULT_LOCAL_MODEL if is_local() else GAP_MODEL


def use_hq_gen() -> bool:
    return os.getenv("USE_HIGH_QUALITY_GEN", "false").lower() == "true"


def gen_model() -> str:
    if is_local():
        return DEFAULT_LOCAL_MODEL
    return HQ_MODEL if use_hq_gen() else MINI_MODEL


def provider_label() -> str:
    if is_local():
        return f"Ollama · {DEFAULT_LOCAL_MODEL}"
    return "OpenAI API"
