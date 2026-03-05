from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import Settings
from .db import ChatRepository
from .providers import ChatProvider, GeminiProvider, LLMRequest, MockProvider, OpenAIProvider
from .rag import KnowledgeBase


SYSTEM_PROMPT = (
    "You are MiniHarutoAI. "
    "Be concise, factual, and transparent about uncertainty. "
    "If context is provided, prioritize it and cite doc ids like [doc_id]."
)


@dataclass(frozen=True)
class ChatResult:
    session_id: str
    answer: str
    citations: list[str]


class ChatService:
    def __init__(
        self,
        repo: ChatRepository,
        kb: KnowledgeBase,
        provider: ChatProvider,
        model: str,
        top_k: int,
    ) -> None:
        self.repo = repo
        self.kb = kb
        self.provider = provider
        self.model = model
        self.top_k = top_k

    def ensure_session(self, session_id: str | None) -> str:
        if session_id and self.repo.session_exists(session_id):
            return session_id
        return self.repo.create_session()

    def list_sessions(self) -> list[dict[str, str]]:
        return self.repo.list_sessions()

    def list_messages(self, session_id: str) -> list[dict[str, str]]:
        messages = self.repo.get_messages(session_id, limit=40)
        return [
            {"role": msg.role, "content": msg.content, "created_at": msg.created_at}
            for msg in messages
        ]

    def chat(self, session_id: str | None, user_message: str) -> ChatResult:
        sid = self.ensure_session(session_id)
        self.repo.add_message(sid, "user", user_message)

        history_messages = self.repo.get_messages(sid, limit=12)
        history_turns = [
            {"role": item.role, "content": item.content}
            for item in history_messages
            if item.role in {"user", "assistant"}
        ]

        # The current user message is passed separately via user_prompt.
        if history_turns and history_turns[-1]["role"] == "user":
            history = history_turns[:-1]
        else:
            history = history_turns

        docs = self.kb.search(user_message, top_k=self.top_k)
        context = self.kb.format_context(docs)
        citations = [doc.doc_id for doc in docs]

        payload = LLMRequest(
            model=self.model,
            system_prompt=SYSTEM_PROMPT,
            history=history,
            user_prompt=user_message,
            context=context,
        )
        answer = self.provider.generate(payload)

        self.repo.add_message(sid, "assistant", answer)
        return ChatResult(session_id=sid, answer=answer, citations=citations)


def build_provider(settings: Settings) -> ChatProvider:
    if settings.provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return OpenAIProvider(settings.openai_api_key)

    if settings.provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        return GeminiProvider(settings.gemini_api_key)

    return MockProvider()


def health_payload(settings: Settings) -> dict[str, Any]:
    return {
        "provider": settings.provider,
        "model": settings.model,
        "status": "ok",
    }
