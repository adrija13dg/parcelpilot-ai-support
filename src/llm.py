"""LLM provider configuration — switch via LLM_PROVIDER in .env."""

from __future__ import annotations

import os

from openai import OpenAI

# Provider presets (all use OpenAI-compatible chat completions API)
PROVIDERS: dict[str, dict] = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "openai/gpt-oss-20b",
        "key_env": "GROQ_API_KEY",
        "label": "Groq (free tier, rate-limited)",
    },
    "gemini": {
        # Free key: https://aistudio.google.com/apikey
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-2.0-flash",
        "key_env": "GEMINI_API_KEY",
        "label": "Google Gemini (generous free tier)",
    },
    "ollama": {
        # Local, unlimited — install from https://ollama.com then: ollama pull llama3.1:8b
        "base_url": "http://localhost:11434/v1",
        "model": "llama3.1:8b",
        "key_env": None,
        "label": "Ollama (local, free, no API limits)",
    },
}


def get_provider_name() -> str:
    return os.getenv("LLM_PROVIDER", "groq").lower().strip()


def get_llm_config() -> dict:
    name = get_provider_name()
    if name not in PROVIDERS:
        names = ", ".join(PROVIDERS)
        raise RuntimeError(f"Unknown LLM_PROVIDER '{name}'. Use one of: {names}")
    return {"name": name, **PROVIDERS[name]}


def get_llm_client() -> OpenAI:
    cfg = get_llm_config()
    api_key = "ollama"
    if cfg.get("key_env"):
        api_key = os.getenv(cfg["key_env"], "")
        if not api_key:
            raise RuntimeError(
                f"{cfg['key_env']} not set. Add it to .env or switch LLM_PROVIDER."
            )
    return OpenAI(api_key=api_key, base_url=cfg["base_url"])


def get_llm_model() -> str:
    return os.getenv("LLM_MODEL") or get_llm_config()["model"]
