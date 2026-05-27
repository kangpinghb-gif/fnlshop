from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from freshos.config import load_settings
from freshos.db.connection import connect


def apply_seed_file(dsn: str, seed_path: str | Path) -> Path:
    path = Path(seed_path)
    sql = path.read_text(encoding="utf-8")
    with connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply FreshOS PostgreSQL seed data.")
    parser.add_argument("--config", default="config/settings.example.toml")
    parser.add_argument("--seed", default="seeds/001_minimal_closure.sql")
    parser.add_argument("--dsn", default="")
    args = parser.parse_args()

    settings = load_settings(args.config)
    dsn = args.dsn or settings.database.dsn
    if not dsn:
        raise SystemExit("Database DSN is required.")

    path = apply_seed_file(dsn, args.seed)
    print(f"[apply_seed_data] applied {path}")


if __name__ == "__main__":
    main()
