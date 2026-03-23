"""Shared utility functions for ClawDone."""

from __future__ import annotations


def extract_json_object(text: str, start_index: int = 0) -> tuple[str, int] | None:
    """Find the first balanced JSON object in *text* at or after *start_index*.

    Returns ``(json_string, end_index)`` where *end_index* is the position
    immediately after the closing ``}``, or ``None`` if no balanced object
    is found.
    """
    start = text.find("{", start_index)
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1], index + 1
    return None
