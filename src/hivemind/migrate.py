from __future__ import annotations

import os
from pathlib import Path

import psycopg


MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def run_migrations(database_url: str, migrations_dir: Path = MIGRATIONS_DIR) -> None:
    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        raise RuntimeError(f"no migrations found in {migrations_dir}")

    with psycopg.connect(database_url) as connection:
        with connection.transaction():
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    filename text PRIMARY KEY,
                    applied_at timestamptz NOT NULL DEFAULT now()
                )
                """
            )
        for migration_file in migration_files:
            with connection.transaction():
                applied = connection.execute(
                    "SELECT 1 FROM schema_migrations WHERE filename = %s",
                    (migration_file.name,),
                ).fetchone()
                if applied:
                    continue
                connection.execute(migration_file.read_text(encoding="utf-8"))
                connection.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s)",
                    (migration_file.name,),
                )


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for migrations")
    run_migrations(database_url)


if __name__ == "__main__":
    main()
