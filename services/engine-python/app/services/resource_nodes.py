from __future__ import annotations

from dataclasses import asdict, dataclass
from re import sub


@dataclass(frozen=True)
class ResourceNode:
    resource_slug: str
    level: str
    stable_key: str
    node_path: str
    parent_stable_key: str | None
    parent_node_path: str | None
    title: str
    content: str
    ordinal: int
    section_slug: str
    ancestry: list[dict[str, str]]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _slugify(value: str) -> str:
    normalized = sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "untitled"


def _build_node_path(
    *,
    resource_slug: str,
    level: str,
    stable_key: str,
    default_suffix: str,
    previous_path_map: dict[str, str],
) -> str:
    return previous_path_map.get(stable_key, f"resource://{resource_slug}/{level}/{default_suffix}")


def _split_paragraphs(text: str) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            current.append(stripped)
            continue
        if current:
            paragraphs.append(" ".join(current))
            current = []

    if current:
        paragraphs.append(" ".join(current))

    return paragraphs


def build_resource_nodes(
    *,
    resource_slug: str,
    markdown: str,
    previous_path_map: dict[str, str] | None = None,
) -> list[ResourceNode]:
    path_map = previous_path_map or {}
    lines = markdown.splitlines()

    document_title = resource_slug
    sections: list[tuple[str, list[str]]] = []
    current_section_title = "overview"
    current_section_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            document_title = stripped[2:].strip() or document_title
            continue
        if stripped.startswith("## "):
            if current_section_lines:
                sections.append((current_section_title, current_section_lines))
            current_section_title = stripped[3:].strip() or "overview"
            current_section_lines = []
            continue
        current_section_lines.append(line)

    if current_section_lines:
        sections.append((current_section_title, current_section_lines))

    l0_stable_key = "l0:root"
    l0_path = _build_node_path(
        resource_slug=resource_slug,
        level="l0",
        stable_key=l0_stable_key,
        default_suffix="root",
        previous_path_map=path_map,
    )
    nodes = [
        ResourceNode(
            resource_slug=resource_slug,
            level="l0",
            stable_key=l0_stable_key,
            node_path=l0_path,
            parent_stable_key=None,
            parent_node_path=None,
            title=document_title,
            content=document_title,
            ordinal=0,
            section_slug="root",
            ancestry=[],
        )
    ]

    for section_index, (section_title, section_lines) in enumerate(sections):
        section_slug = _slugify(section_title)
        section_slot = f"s{section_index:03d}"
        l1_stable_key = f"l1:{section_slot}"
        l1_path = _build_node_path(
            resource_slug=resource_slug,
            level="l1",
            stable_key=l1_stable_key,
            default_suffix=section_slot,
            previous_path_map=path_map,
        )
        section_content = "\n".join(section_lines).strip()
        l1_ancestry = [{"level": "l0", "stable_key": l0_stable_key, "node_path": l0_path}]
        nodes.append(
            ResourceNode(
                resource_slug=resource_slug,
                level="l1",
                stable_key=l1_stable_key,
                node_path=l1_path,
                parent_stable_key=l0_stable_key,
                parent_node_path=l0_path,
                title=section_title,
                content=section_content,
                ordinal=section_index,
                section_slug=section_slug,
                ancestry=l1_ancestry,
            )
        )

        for paragraph_index, paragraph in enumerate(_split_paragraphs(section_content)):
            l2_stable_key = f"l2:{section_slot}:{paragraph_index:03d}"
            l2_path = _build_node_path(
                resource_slug=resource_slug,
                level="l2",
                stable_key=l2_stable_key,
                default_suffix=f"{section_slot}/{paragraph_index:03d}",
                previous_path_map=path_map,
            )
            nodes.append(
                ResourceNode(
                    resource_slug=resource_slug,
                    level="l2",
                    stable_key=l2_stable_key,
                    node_path=l2_path,
                    parent_stable_key=l1_stable_key,
                    parent_node_path=l1_path,
                    title=f"{section_title} #{paragraph_index + 1}",
                    content=paragraph,
                    ordinal=paragraph_index,
                    section_slug=section_slug,
                    ancestry=[
                        {"level": "l0", "stable_key": l0_stable_key, "node_path": l0_path},
                        {"level": "l1", "stable_key": l1_stable_key, "node_path": l1_path},
                    ],
                )
            )

    return nodes
