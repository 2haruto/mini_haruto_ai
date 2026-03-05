from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str
    host: str
    port: int
    db_path: Path
    knowledge_path: Path
    top_k: int
    openai_api_key: str | None
    gemini_api_key: str | None


def load_settings(base_dir: Path) -> Settings:
    return Settings(
        provider=os.getenv("LLM_PROVIDER", "mock").strip().lower(),
        model=os.getenv("LLM_MODEL", "gpt-4.1-mini").strip(),
        host=os.getenv("APP_HOST", "127.0.0.1").strip(),
        port=int(os.getenv("APP_PORT", "8080")),
        db_path=base_dir / "chat.db",
        knowledge_path=base_dir / "knowledge",
        top_k=int(os.getenv("RAG_TOP_K", "3")),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
    )
