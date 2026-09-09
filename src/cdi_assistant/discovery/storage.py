from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import JobDiscovery


class JobDiscoveryStore:
    """Small SQLite store for normalized job discoveries."""

    def __init__(self, database_path: str | Path = "data/jobs.db") -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    deduplication_key TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    source_id TEXT,
                    url TEXT NOT NULL,
                    canonical_url TEXT,
                    apply_url TEXT,
                    title TEXT NOT NULL,
                    company TEXT,
                    location TEXT,
                    published_at TEXT,
                    updated_at TEXT,
                    discovered_at TEXT NOT NULL,
                    snippet TEXT NOT NULL,
                    description TEXT NOT NULL,
                    contract TEXT,
                    remote TEXT,
                    salary TEXT,
                    experience TEXT,
                    skills_json TEXT NOT NULL,
                    search_query TEXT,
                    raw_data_json TEXT NOT NULL
                )
                """
            )

    def upsert(self, job: JobDiscovery) -> None:
        data = job.to_dict()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO jobs (
                    deduplication_key, source, source_id, url, canonical_url,
                    apply_url, title, company, location, published_at,
                    updated_at, discovered_at, snippet, description, contract,
                    remote, salary, experience, skills_json, search_query,
                    raw_data_json
                ) VALUES (
                    :deduplication_key, :source, :source_id, :url, :canonical_url,
                    :apply_url, :title, :company, :location, :published_at,
                    :updated_at, :discovered_at, :snippet, :description, :contract,
                    :remote, :salary, :experience, :skills_json, :search_query,
                    :raw_data_json
                )
                ON CONFLICT(deduplication_key) DO UPDATE SET
                    url=excluded.url,
                    canonical_url=excluded.canonical_url,
                    apply_url=excluded.apply_url,
                    title=excluded.title,
                    company=excluded.company,
                    location=excluded.location,
                    published_at=excluded.published_at,
                    updated_at=excluded.updated_at,
                    snippet=excluded.snippet,
                    description=excluded.description,
                    contract=excluded.contract,
                    remote=excluded.remote,
                    salary=excluded.salary,
                    experience=excluded.experience,
                    skills_json=excluded.skills_json,
                    search_query=excluded.search_query,
                    raw_data_json=excluded.raw_data_json
                """,
                {
                    "deduplication_key": job.deduplication_key,
                    **data,
                    "skills_json": json.dumps(data["skills"], ensure_ascii=False),
                    "raw_data_json": json.dumps(data["raw_data"], ensure_ascii=False),
                },
            )

    def upsert_many(self, jobs: list[JobDiscovery]) -> int:
        for job in jobs:
            self.upsert(job)
        return len(jobs)

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM jobs").fetchone()
        return int(row["count"])

    def list_recent(self, limit: int = 50) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM jobs ORDER BY COALESCE(updated_at, published_at, discovered_at) DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
