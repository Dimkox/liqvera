"""Apply or remove only the A2 PostgreSQL migration."""

from __future__ import annotations

import os
from pathlib import Path
import sys


def main(arguments: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if arguments is None else arguments)
    if len(args) != 1 or args[0] not in {"up", "down"}:
        print("usage: a2-migrate.py {up|down}", file=sys.stderr)
        return 2
    dsn = os.environ.get("A2_DATABASE_URL")
    if not dsn:
        print("A2_DATABASE_URL is required", file=sys.stderr)
        return 2

    migration = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / f"000002_a2_raw_capture.{args[0]}.sql"
    )
    sql = migration.read_text(encoding="utf-8")
    try:
        import psycopg

        with psycopg.connect(dsn, autocommit=True) as connection:
            connection.execute(sql, prepare=False)
    except BaseException:
        print("A2 migration failed", file=sys.stderr)
        return 1
    print(f"A2 migration {args[0]} complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
