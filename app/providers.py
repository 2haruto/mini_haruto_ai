from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Protocol
from urllib import error, request


@dataclass(frozen=True)
class LLMRequest:
    model: str
    system_prompt: str
    history: list[dict[str, str]]
    user_prompt: str
    context: str


class ChatProvider(Protocol):
    def generate(self, payload: LLMRequest) -> str:
        ...


class MockProvider:
    def generate(self, payload: LLMRequest) -> str:
        context_line = "No external context found."
        if payload.context:
            first_line = payload.context.splitlines()[0]
            context_line = f"Using context: {first_line}"

        return (
            "[mock-mode] This is a local reply. "
            f"You asked: '{payload.user_prompt}'. "
            f"{context_line}"
        )


class OpenAIProvider:
    def __init__(self, api_key: str, timeout_sec: int = 30) -> None:
        self.api_key = api_key
        self.timeout_sec = timeout_sec

    def generate(self, payload: LLMRequest) -> str:
        messages = [{"role": "system", "content": payload.system_prompt}]
        messages.extend(payload.history)

        user_content = payload.user_prompt
        if payload.context:
            user_content += "\n\nContext:\n" + payload.context
        messages.append({"role": "user", "content": user_content})

        body = {
            "model": payload.model,
            "messages": messages,
            "temperature": 0.2,
        }

        req = request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_sec) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            return f"OpenAI API error: {exc.code} {detail}"
        except Exception as exc:  # pragma: no cover
            return f"OpenAI API error: {exc}"

        try:
            return raw["choices"][0]["message"]["content"].strip()
        except Exception:
            return "OpenAI API returned an unexpected response format."


class GeminiProvider:
    def __init__(self, api_key: str, timeout_sec: int = 30) -> None:
        self.api_key = api_key
        self.timeout_sec = timeout_sec

    def generate(self, payload: LLMRequest) -> str:
        turns = []
        for item in payload.history:
            turns.append(
                {
                    "role": "model" if item["role"] == "assistant" else "user",
                    "parts": [{"text": item["content"]}],
                }
            )

        user_text = payload.user_prompt
        if payload.context:
            user_text += "\n\nContext:\n" + payload.context

        turns.append({"role": "user", "parts": [{"text": user_text}]})

        body = {
            "systemInstruction": {"parts": [{"text": payload.system_prompt}]},
            "contents": turns,
            "generationConfig": {"temperature": 0.2},
        }

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{payload.model}:"
            f"generateContent?key={self.api_key}"
        )

        req = request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_sec) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            return f"Gemini API error: {exc.code} {detail}"
        except Exception as exc:  # pragma: no cover
            return f"Gemini API error: {exc}"

        try:
            return raw["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            return "Gemini API returned an unexpected response format."
