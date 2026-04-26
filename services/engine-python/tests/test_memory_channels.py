from app.models import MemoryChannel, MemoryType
from app.services.memory import extract_memory_candidates, summarize_session


def test_extract_memory_candidates_emits_user_and_task_experience_channels() -> None:
    candidates = extract_memory_candidates(
        session_goal="Draft a reply to Zhiguang about Java cache design.",
        turns=[
            {
                "role": "user",
                "content": "Please keep the explanation concise and focused on Java implementation details.",
            },
            {
                "role": "assistant",
                "content": "I can draft a concise Java-focused reply.",
            },
        ],
        selected_resource_paths=["resource://zhiguang-java-cache-playbook/l2/s000/000"],
    )

    assert any(
        candidate.channel == MemoryChannel.USER
        and candidate.memory_type == MemoryType.EXPLANATION_PREFERENCE
        and "concise" in candidate.content.lower()
        and "java" in candidate.content.lower()
        for candidate in candidates
    )
    assert any(
        candidate.channel == MemoryChannel.USER
        and candidate.memory_type == MemoryType.USER_GOAL
        and "zhiguang" in candidate.content.lower()
        for candidate in candidates
    )
    assert any(
        candidate.channel == MemoryChannel.TASK_EXPERIENCE
        and candidate.memory_type == MemoryType.SUCCESSFUL_RESOURCE
        and candidate.salience == 70
        and candidate.content == "Helpful resource: resource://zhiguang-java-cache-playbook/l2/s000/000"
        for candidate in candidates
    )


def test_summarize_session_keeps_goal_relevant_turns_and_drops_chatter() -> None:
    summary = summarize_session(
        session_goal="Draft a reply to Zhiguang with a concise Java explanation.",
        turns=[
            {"role": "user", "content": "Need a reply to Zhiguang with a concise Java explanation."},
            {"role": "assistant", "content": "I'll keep it concise and Java-focused."},
            {"role": "user", "content": "By the way, the weather is nice today."},
            {"role": "assistant", "content": "Yes, sunny afternoons are pleasant."},
        ],
    )

    assert "Zhiguang" in summary
    assert "concise Java" in summary
    assert "weather" not in summary.lower()
    assert "sunny" not in summary.lower()


def test_extract_memory_candidates_detects_chinese_concise_preference() -> None:
    candidates = extract_memory_candidates(
        session_goal="写一条关于 Redis cache-aside 的 Zhiguang 回复",
        turns=[
            {
                "role": "user",
                "content": "我在知广项目上回复，请简短一点解释 Redis cache-aside。",
            },
        ],
        selected_resource_paths=[],
    )

    assert any(
        candidate.channel == MemoryChannel.USER
        and candidate.memory_type == MemoryType.EXPLANATION_PREFERENCE
        and candidate.content == "User prefers concise explanations."
        for candidate in candidates
    )


def test_summarize_session_falls_back_to_latest_user_turn_when_goal_terms_do_not_overlap() -> None:
    summary = summarize_session(
        session_goal="写一条关于观测性的 Zhiguang 回复",
        turns=[
            {"role": "user", "content": "我只想解释采样和日志关联，不展开 trace 或 span。"},
            {"role": "assistant", "content": "可以，我会聚焦在采样和日志关联。"},
        ],
    )

    assert "观测性" in summary
    assert "采样和日志关联" in summary
    assert "trace 或 span" in summary
