from __future__ import annotations

from dataclasses import dataclass
import re

from freshos.matching.rules import normalize_name


PRODUCT_PREFIX_RE = re.compile(r"^(?:C|Z|JPZ|R)-", re.IGNORECASE)


@dataclass(frozen=True)
class EntityRecord:
    id: str
    code: str
    name: str


@dataclass(frozen=True)
class OrderMatch:
    store_id: str | None
    product_id: str | None
    match_status: str
    exception_types: tuple[str, ...]


def match_order_row(
    *,
    store_name_raw: str,
    product_name_raw: str,
    stores: list[EntityRecord],
    products: list[EntityRecord],
) -> OrderMatch:
    store_id = _match_name(store_name_raw, stores, clean_product_prefix=False)
    product_id = _match_name(product_name_raw, products, clean_product_prefix=True)

    exception_types: list[str] = []
    if not store_id:
        exception_types.append("unmatched_store")
    if not product_id:
        exception_types.append("unmatched_product")

    return OrderMatch(
        store_id=store_id,
        product_id=product_id,
        match_status="matched" if not exception_types else "failed",
        exception_types=tuple(exception_types),
    )


def _match_name(raw_name: str, records: list[EntityRecord], *, clean_product_prefix: bool) -> str | None:
    indexes = _build_name_indexes(records, clean_product_prefix=clean_product_prefix)
    candidates = _candidate_names(raw_name, clean_product_prefix=clean_product_prefix)
    for candidate in candidates:
        matched = indexes.get(candidate)
        if matched:
            return matched
    return None


def _build_name_indexes(records: list[EntityRecord], *, clean_product_prefix: bool) -> dict[str, str]:
    index: dict[str, str] = {}
    for record in records:
        for name in _candidate_names(record.name, clean_product_prefix=clean_product_prefix):
            index.setdefault(name, record.id)
    return index


def _candidate_names(value: str, *, clean_product_prefix: bool) -> list[str]:
    normalized = normalize_name(value)
    candidates = [normalized]
    if clean_product_prefix:
        cleaned = normalize_name(PRODUCT_PREFIX_RE.sub("", value.strip()))
        if cleaned and cleaned not in candidates:
            candidates.append(cleaned)
    return candidates

