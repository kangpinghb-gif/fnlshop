from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchResult:
    matched_id: str | None
    status: str
    reason: str = ""


def normalize_name(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().replace(" ", "").replace("　", "")


def match_by_code_or_name(
    *,
    code: str | None,
    name: str | None,
    code_index: dict[str, str],
    name_index: dict[str, str],
    prefer_name: bool = False,
) -> MatchResult:
    normalized_name = normalize_name(name)

    if prefer_name and normalized_name in name_index:
        return MatchResult(name_index[normalized_name], "matched", "matched_by_name")

    if code and code in code_index:
        return MatchResult(code_index[code], "matched", "matched_by_code")

    if normalized_name in name_index:
        return MatchResult(name_index[normalized_name], "matched", "matched_by_name")

    return MatchResult(None, "failed", "no_code_or_name_match")

