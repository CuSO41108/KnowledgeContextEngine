from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Protocol

import httpx

from app.services.resource_nodes import ResourceNode
from app.settings import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PackedContext:
    prompt_context: str
    included_chars: int


class AnswerGenerator(Protocol):
    def generate(
        self,
        *,
        question: str,
        session_summary: str,
        memory_items: list[str],
        selected_nodes: list[ResourceNode],
    ) -> str:
        ...


class AnswerGenerationError(RuntimeError):
    pass


def pack_context(
    *,
    selected_nodes: list[ResourceNode],
    max_chars: int | None = None,
) -> PackedContext:
    budget = max_chars if max_chars is not None else settings.answer_context_max_chars
    remaining = max(0, budget)
    chunks: list[str] = []

    for index, node in enumerate(selected_nodes, start=1):
        header = f"[{index}] {node.node_path}\nTitle: {node.title}\nContent:\n"
        content = node.content.strip()
        if remaining <= len(header):
            break
        content_budget = remaining - len(header)
        clipped_content = content[:content_budget].rstrip()
        if not clipped_content:
            continue
        chunk = f"{header}{clipped_content}"
        chunks.append(chunk)
        remaining -= len(chunk)

    prompt_context = "\n\n---\n\n".join(chunks)
    return PackedContext(
        prompt_context=prompt_context,
        included_chars=len(prompt_context),
    )


def build_answer_messages(
    *,
    question: str,
    session_summary: str,
    memory_items: list[str],
    selected_nodes: list[ResourceNode],
) -> list[dict[str, str]]:
    packed_context = pack_context(selected_nodes=selected_nodes)
    memory_context = "\n".join(f"- {item}" for item in memory_items if item.strip())
    if not memory_context:
        memory_context = "- none"

    system = (
        "You are a grounded knowledge-context answer generator. "
        "Answer in the user's language. Use only the provided evidence and memory. "
        "If the evidence is too thin, say what is missing instead of inventing facts. "
        "When possible, cite evidence with bracket numbers like [1]."
    )
    user = (
        f"Session summary:\n{session_summary.strip() or 'none'}\n\n"
        f"Relevant memory:\n{memory_context}\n\n"
        f"Evidence nodes:\n{packed_context.prompt_context or 'none'}\n\n"
        f"Question:\n{question.strip()}\n\n"
        "Return a concise, useful answer grounded in the evidence."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


class OpenAICompatibleAnswerGenerator:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_tokens: int,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_tokens = max_tokens

    def generate(
        self,
        *,
        question: str,
        session_summary: str,
        memory_items: list[str],
        selected_nodes: list[ResourceNode],
    ) -> str:
        if not self._base_url or not self._api_key or self._api_key == "replace-me":
            raise AnswerGenerationError("answer LLM is not configured")

        messages = build_answer_messages(
            question=question,
            session_summary=session_summary,
            memory_items=memory_items,
            selected_nodes=selected_nodes,
        )
        try:
            response = httpx.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": self._max_tokens,
                },
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except Exception as error:
            raise AnswerGenerationError("answer LLM request failed") from error

        if not isinstance(content, str) or not content.strip():
            raise AnswerGenerationError("answer LLM returned empty content")
        return content.strip()


def get_default_answer_generator() -> AnswerGenerator | None:
    if not settings.answer_llm_enabled:
        return None
    return OpenAICompatibleAnswerGenerator(
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
        model=settings.openai_chat_model,
        timeout_seconds=settings.answer_llm_timeout_seconds,
        max_tokens=settings.answer_max_tokens,
    )


def generate_answer_with_fallback(
    *,
    question: str,
    session_summary: str,
    memory_items: list[str],
    selected_nodes: list[ResourceNode],
    fallback_answer: str,
    answer_generator: AnswerGenerator | None = None,
) -> str:
    generator = answer_generator if answer_generator is not None else get_default_answer_generator()
    if generator is None:
        return fallback_answer

    try:
        return generator.generate(
            question=question,
            session_summary=session_summary,
            memory_items=memory_items,
            selected_nodes=selected_nodes,
        )
    except Exception as error:
        logger.warning("Answer generation failed; falling back to deterministic answer: %s", error)
        return fallback_answer
