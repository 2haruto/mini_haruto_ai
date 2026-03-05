from __future__ import annotations

from pathlib import Path

from app.config import load_settings
from app.db import ChatRepository
from app.rag import KnowledgeBase
from app.server import run_server
from app.service import ChatService, build_provider, health_payload


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    settings = load_settings(base_dir)

    repo = ChatRepository(settings.db_path)
    kb = KnowledgeBase(settings.knowledge_path)
    provider = build_provider(settings)

    service = ChatService(
        repo=repo,
        kb=kb,
        provider=provider,
        model=settings.model,
        top_k=settings.top_k,
    )

    try:
        run_server(
            host=settings.host,
            port=settings.port,
            service=service,
            web_root=base_dir / "web",
            health=health_payload(settings),
        )
    except KeyboardInterrupt:
        print("\nMiniHarutoAI stopped.")


if __name__ == "__main__":
    main()
