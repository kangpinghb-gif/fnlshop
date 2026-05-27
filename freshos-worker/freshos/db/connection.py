from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


@contextmanager
def connect(dsn: str) -> Iterator[object]:
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError(
            "psycopg is required for PostgreSQL access. Install it in the worker environment."
        ) from exc

    with psycopg.connect(dsn) as conn:
        yield conn

