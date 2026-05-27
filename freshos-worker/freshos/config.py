from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9 compatibility for the server/system Python.
    tomllib = None


@dataclass(frozen=True)
class DatabaseSettings:
    enabled: bool
    dsn: str


@dataclass(frozen=True)
class PathSettings:
    data_dir: Path
    report_dir: Path


@dataclass(frozen=True)
class NotifySettings:
    provider: str
    webhook_url: str


@dataclass(frozen=True)
class JobSettings:
    default_business_date: str


@dataclass(frozen=True)
class Settings:
    database: DatabaseSettings
    paths: PathSettings
    notify: NotifySettings
    jobs: JobSettings


def load_settings(path: str | Path = "config/settings.example.toml") -> Settings:
    config_path = Path(path)
    raw = _load_toml(config_path)

    return Settings(
        database=DatabaseSettings(
            enabled=bool(raw.get("database", {}).get("enabled", False)),
            dsn=raw.get("database", {}).get("dsn", ""),
        ),
        paths=PathSettings(
            data_dir=Path(raw.get("paths", {}).get("data_dir", "./data")),
            report_dir=Path(raw.get("paths", {}).get("report_dir", "./reports")),
        ),
        notify=NotifySettings(
            provider=raw.get("notify", {}).get("provider", "none"),
            webhook_url=raw.get("notify", {}).get("webhook_url", ""),
        ),
        jobs=JobSettings(
            default_business_date=raw.get("jobs", {}).get("default_business_date", ""),
        ),
    )


def _load_toml(path: Path) -> dict[str, Any]:
    if tomllib is not None:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    return _load_simple_toml(path)


def _load_simple_toml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current: dict[str, Any] | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            current = data.setdefault(section, {})
            continue
        if "=" not in line or current is None:
            continue
        key, value = line.split("=", 1)
        current[key.strip()] = _parse_simple_toml_value(value.strip())

    return data


def _parse_simple_toml_value(value: str) -> Any:
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value
