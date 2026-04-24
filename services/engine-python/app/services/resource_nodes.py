from __future__ import annotations

from dataclasses import asdict, dataclass
from re import sub
from collections import defaultdict


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


def _parse_section_number(stable_key: str) -> int | None:
    if not stable_key.startswith("l1:s"):
        return None
    try:
        return int(stable_key.split(":s", maxsplit=1)[1])
    except ValueError:
        return None


def _parse_paragraph_number(stable_key: str) -> tuple[str, int] | None:
    if not stable_key.startswith("l2:s"):
        return None
    parts = stable_key.split(":")
    if len(parts) != 3:
        return None
    try:
        return parts[1], int(parts[2])
    except ValueError:
        return None


def _next_section_number(previous_nodes: list[ResourceNode]) -> int:
    section_numbers = [
        section_number
        for node in previous_nodes
        if node.level == "l1"
        for section_number in [_parse_section_number(node.stable_key)]
        if section_number is not None
    ]
    return (max(section_numbers) + 1) if section_numbers else 0


def _next_paragraph_number(previous_nodes: list[ResourceNode], section_slot: str) -> int:
    paragraph_numbers = [
        paragraph_number
        for node in previous_nodes
        if node.level == "l2"
        for parsed in [_parse_paragraph_number(node.stable_key)]
        if parsed is not None and parsed[0] == section_slot
        for paragraph_number in [parsed[1]]
    ]
    return (max(paragraph_numbers) + 1) if paragraph_numbers else 0


def _find_matching_previous_section(
    *,
    previous_sections: list[ResourceNode],
    used_section_keys: set[str],
    section_slug: str,
    section_content: str,
    section_index: int,
    total_sections: int,
) -> ResourceNode | None:
    for previous_section in previous_sections:
        if previous_section.stable_key in used_section_keys:
            continue
        if previous_section.content == section_content:
            return previous_section

    current_paragraphs = set(_split_paragraphs(section_content))
    best_match: ResourceNode | None = None
    best_overlap = 0
    for previous_section in previous_sections:
        if previous_section.stable_key in used_section_keys:
            continue
        if previous_section.section_slug != section_slug:
            continue
        overlap = len(current_paragraphs.intersection(_split_paragraphs(previous_section.content)))
        if overlap > best_overlap:
            best_match = previous_section
            best_overlap = overlap

    if best_overlap > 0:
        return best_match

    if len(previous_sections) == total_sections:
        for previous_section in previous_sections:
            if previous_section.stable_key in used_section_keys:
                continue
            if previous_section.section_slug == section_slug and previous_section.ordinal == section_index:
                return previous_section

    return None


def build_resource_nodes(
    *,
    resource_slug: str,
    markdown: str,
    previous_path_map: dict[str, str] | None = None,
    previous_nodes: list[ResourceNode] | None = None,
) -> list[ResourceNode]:
    prior_nodes = previous_nodes or []
    path_map = {node.stable_key: node.node_path for node in prior_nodes}
    path_map.update(previous_path_map or {})
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

    previous_sections: list[ResourceNode] = []
    previous_l2_by_parent: dict[str, dict[str, list[ResourceNode]]] = defaultdict(lambda: defaultdict(list))
    for node in prior_nodes:
        if node.level == "l1":
            previous_sections.append(node)
        elif node.level == "l2" and node.parent_stable_key is not None:
            previous_l2_by_parent[node.parent_stable_key][node.content].append(node)

    next_section_number = _next_section_number(prior_nodes)
    used_section_keys: set[str] = set()

    for section_index, (section_title, section_lines) in enumerate(sections):
        section_slug = _slugify(section_title)
        section_content = "\n".join(section_lines).strip()
        matching_previous_section = _find_matching_previous_section(
            previous_sections=previous_sections,
            used_section_keys=used_section_keys,
            section_slug=section_slug,
            section_content=section_content,
            section_index=section_index,
            total_sections=len(sections),
        )

        if matching_previous_section is not None:
            used_section_keys.add(matching_previous_section.stable_key)
            l1_stable_key = matching_previous_section.stable_key
            l1_path = matching_previous_section.node_path
            section_slot = l1_stable_key.split(":")[1]
        else:
            section_slot = f"s{next_section_number:03d}"
            next_section_number += 1
            l1_stable_key = f"l1:{section_slot}"
            l1_path = _build_node_path(
                resource_slug=resource_slug,
                level="l1",
                stable_key=l1_stable_key,
                default_suffix=section_slot,
                previous_path_map=path_map,
            )
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

        available_previous_paragraphs = previous_l2_by_parent.get(l1_stable_key, defaultdict(list))
        previous_paragraph_nodes = [
            prior_node
            for prior_node in prior_nodes
            if prior_node.level == "l2" and prior_node.parent_stable_key == l1_stable_key
        ]
        next_paragraph_number = _next_paragraph_number(prior_nodes, section_slot)
        current_paragraphs = _split_paragraphs(section_content)
        used_previous_paragraph_keys: set[str] = set()
        for paragraph_index, paragraph in enumerate(current_paragraphs):
            matching_previous_paragraph = None
            if available_previous_paragraphs[paragraph]:
                matching_previous_paragraph = available_previous_paragraphs[paragraph].pop(0)

            if matching_previous_paragraph is None and len(previous_paragraph_nodes) == len(current_paragraphs):
                for previous_paragraph in previous_paragraph_nodes:
                    if previous_paragraph.stable_key in used_previous_paragraph_keys:
                        continue
                    if previous_paragraph.ordinal == paragraph_index:
                        matching_previous_paragraph = previous_paragraph
                        break

            if matching_previous_paragraph is not None:
                used_previous_paragraph_keys.add(matching_previous_paragraph.stable_key)
                l2_stable_key = matching_previous_paragraph.stable_key
                l2_path = matching_previous_paragraph.node_path
            else:
                paragraph_number = next_paragraph_number
                next_paragraph_number += 1
                l2_stable_key = f"l2:{section_slot}:{paragraph_number:03d}"
                l2_path = _build_node_path(
                    resource_slug=resource_slug,
                    level="l2",
                    stable_key=l2_stable_key,
                    default_suffix=f"{section_slot}/{paragraph_number:03d}",
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
