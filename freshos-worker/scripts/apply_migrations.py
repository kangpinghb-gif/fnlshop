from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from freshos.config import load_settings
from freshos.db.migrations import apply_migrations


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply FreshOS PostgreSQL migrations.")
    parser.add_argument("--config", default="config/settings.example.toml")
    parser.add_argument("--migrations-dir", default="migrations")
    parser.add_argument("--dsn", default="")
    args = parser.parse_args()

    settings = load_settings(args.config)
    dsn = args.dsn or settings.database.dsn
    if not dsn:
        raise SystemExit("Database DSN is required.")

    applied = apply_migrations(dsn, args.migrations_dir)
    for path in applied:
        print(f"[apply_migrations] applied {path}")


if __name__ == "__main__":
    main()

