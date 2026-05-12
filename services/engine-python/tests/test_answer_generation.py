from app.services.answer_generation import AnswerGenerationError
from app.services.answer_generation import build_answer_messages
from app.services.answer_generation import generate_answer_with_fallback
from app.services.answer_generation import pack_context
from app.services.query import build_query_result
from app.services.resource_nodes import build_resource_nodes


class FakeAnswerGenerator:
    def generate(self, **kwargs: object) -> str:
        return "LLM grounded answer [1]"


class FailingAnswerGenerator:
    def generate(self, **kwargs: object) -> str:
        raise AnswerGenerationError("boom")


def test_pack_context_includes_node_paths_and_respects_budget() -> None:
    nodes = build_resource_nodes(
        resource_slug="zhiguang-answer-doc",
        markdown="# Answer Doc\n## First\n" + ("A" * 120),
    )
    l2_node = next(node for node in nodes if node.level == "l2")

    packed = pack_context(selected_nodes=[l2_node], max_chars=90)

    assert "resource://zhiguang-answer-doc/l2/s000/000" in packed.prompt_context
    assert len(packed.prompt_context) <= 90
    assert packed.included_chars == len(packed.prompt_context)


def test_build_answer_messages_ground_the_model_in_evidence_and_memory() -> None:
    nodes = build_resource_nodes(
        resource_slug="zhiguang-answer-doc",
        markdown="# Answer Doc\n## Cache\nRedis cache-aside keeps the database authoritative.",
    )
    l2_node = next(node for node in nodes if node.level == "l2")

    messages = build_answer_messages(
        question="How should I explain cache-aside?",
        session_summary="Write a concise Zhiguang answer.",
        memory_items=["User prefers concise answers."],
        selected_nodes=[l2_node],
    )

    assert messages[0]["role"] == "system"
    assert "Use only the provided evidence" in messages[0]["content"]
    assert "User prefers concise answers." in messages[1]["content"]
    assert "Redis cache-aside keeps the database authoritative." in messages[1]["content"]
    assert "resource://zhiguang-answer-doc/l2/s000/000" in messages[1]["content"]


def test_build_query_result_uses_answer_generator_when_available() -> None:
    nodes = build_resource_nodes(
        resource_slug="zhiguang-answer-doc",
        markdown="# Answer Doc\n## Cache\nRedis cache-aside keeps DB authoritative.",
    )
    l2_node = next(node for node in nodes if node.level == "l2")

    result = build_query_result(
        question="How should I explain cache-aside?",
        session_summary="Write a Zhiguang answer.",
        memory_items=[],
        selected_nodes=[l2_node],
        trace_id="trace-answer-001",
        answer_generator=FakeAnswerGenerator(),
    )

    assert result.answer == "LLM grounded answer [1]"
    assert result.used_contexts["resources"][0]["nodePath"] == "resource://zhiguang-answer-doc/l2/s000/000"


def test_generate_answer_with_fallback_returns_deterministic_answer_on_llm_failure() -> None:
    nodes = build_resource_nodes(
        resource_slug="zhiguang-answer-doc",
        markdown="# Answer Doc\n## Cache\nRedis cache-aside keeps DB authoritative.",
    )
    l2_node = next(node for node in nodes if node.level == "l2")

    answer = generate_answer_with_fallback(
        question="How should I explain cache-aside?",
        session_summary="Write a Zhiguang answer.",
        memory_items=[],
        selected_nodes=[l2_node],
        fallback_answer="fallback answer",
        answer_generator=FailingAnswerGenerator(),
    )

    assert answer == "fallback answer"
