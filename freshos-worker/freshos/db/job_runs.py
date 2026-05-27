from __future__ import annotations

from contextlib import contextmanager
from datetime import date
import json
from typing import Iterator

from freshos.config import Settings
from freshos.db.connection import connect


@contextmanager
def job_run(
    settings: Settings,
    *,
    job_name: str,
    business_date: str,
    metadata: dict[str, object] | None = None,
) -> Iterator[None]:
    if not settings.database.enabled:
        print(f"[job_runs] disabled job_name={job_name} business_date={business_date}")
        yield
        return

    run_id = _start_job_run(settings, job_name, business_date, metadata or {})
    try:
        yield
    except Exception as exc:
        _finish_job_run(settings, run_id, "failed", str(exc))
        raise
    else:
        _finish_job_run(settings, run_id, "success", None)


def _start_job_run(
    settings: Settings,
    job_name: str,
    business_date: str,
    metadata: dict[str, object],
) -> str:
    sql = """
        INSERT INTO job_runs (job_name, business_date, status, metadata)
        VALUES (%s, %s, 'running', %s::jsonb)
        RETURNING id
    """
    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (job_name, _parse_date(business_date), json.dumps(metadata, ensure_ascii=False)))
            row = cur.fetchone()
            return str(row[0])


def _finish_job_run(settings: Settings, run_id: str, status: str, error_message: str | None) -> None:
    sql = """
        UPDATE job_runs
        SET status = %s,
            finished_at = now(),
            error_message = %s
        WHERE id = %s
    """
    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (status, error_message, run_id))


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)

