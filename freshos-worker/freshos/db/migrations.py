from __future__ import annotations

from pathlib import Path

from freshos.db.connection import connect


def apply_migrations(dsn: str, migrations_dir: str | Path = "migrations") -> list[Path]:
    applied: list[Path] = []
    for sql_path in sorted(Path(migrations_dir).glob("*.sql")):
        sql = sql_path.read_text(encoding="utf-8")
        with connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
        applied.append(sql_path)
    return applied

