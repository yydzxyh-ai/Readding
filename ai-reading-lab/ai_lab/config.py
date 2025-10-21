from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass
class Settings:
    model: str = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    api_key: str | None = os.environ.get("OPENAI_API_KEY")
    max_tokens: int = int(os.environ.get("MAX_TOKENS", "6000"))
    temperature: float = float(os.environ.get("TEMPERATURE", "0.2"))

def get_settings() -> Settings:
    return Settings()

def get_llm_client():
    from openai import OpenAI
    s = get_settings()
    if not s.api_key:
        raise RuntimeError("OPENAI_API_KEY is required in env.")
    return OpenAI(api_key=s.api_key)
