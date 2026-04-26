from __future__ import annotations

from dataclasses import dataclass
from re import findall

from app.models import MemoryChannel, MemoryType


@dataclass(frozen=True)
class MemoryCandidate:
    channel: MemoryChannel
    memory_type: MemoryType
    salience: int
    content: str


def _normalize_turn_text(turns: list[dict[str, str]]) -> str:
    return " ".join(turn.get("content", "") for turn in turns)


CONCISE_HINTS = (
    "concise",
    "brief",
    "short",
    "简短",
    "简洁",
    "简要",
    "简明",
)


def extract_memory_candidates(
    *,
    session_goal: str,
    turns: list[dict[str, str]],
    selected_resource_paths: list[str] | None = None,
) -> list[MemoryCandidate]:
    candidates: list[MemoryCandidate] = []
    goal_text = session_goal.strip()
    all_turn_text = _normalize_turn_text(turns)
    lowered_turn_text = all_turn_text.lower()

    if goal_text:
        candidates.append(
            MemoryCandidate(
                channel=MemoryChannel.USER,
                memory_type=MemoryType.USER_GOAL,
                salience=85,
                content=f"User goal: {goal_text}",
            )
        )

    if any(hint in lowered_turn_text or hint in all_turn_text for hint in CONCISE_HINTS):
        preference_bits: list[str] = []
        if any(hint in lowered_turn_text or hint in all_turn_text for hint in CONCISE_HINTS):
            preference_bits.append("concise")
        if "java" in lowered_turn_text:
            preference_bits.append("Java-focused")
        preference_text = " and ".join(preference_bits) if preference_bits else "concise"
        candidates.append(
            MemoryCandidate(
                channel=MemoryChannel.USER,
                memory_type=MemoryType.EXPLANATION_PREFERENCE,
                salience=80,
                content=f"User prefers {preference_text} explanations.",
            )
        )

    for node_path in selected_resource_paths or []:
        candidates.append(
            MemoryCandidate(
                channel=MemoryChannel.TASK_EXPERIENCE,
                memory_type=MemoryType.SUCCESSFUL_RESOURCE,
                salience=70,
                content=f"Helpful resource: {node_path}",
            )
        )

    return candidates


def summarize_session(*, session_goal: str, turns: list[dict[str, str]]) -> str:
    goal_text = session_goal.strip()
    goal_keywords = {token.lower() for token in findall(r"[A-Za-z0-9]+", goal_text) if len(token) > 2}
    relevant_lines: list[str] = []

    for turn in turns:
        content = turn.get("content", "").strip()
        if not content:
            continue
        lowered = content.lower()
        if any(keyword in lowered for keyword in goal_keywords):
            relevant_lines.append(content)

    if not relevant_lines:
        fallback_turn = next(
            (
                turn.get("content", "").strip()
                for turn in reversed(turns)
                if turn.get("role") == "user" and turn.get("content", "").strip()
            ),
            "",
        )
        if fallback_turn:
            return f"{goal_text} Key context: {fallback_turn}".strip()
        return goal_text

    return f"{goal_text} Key context: {' '.join(relevant_lines)}"
