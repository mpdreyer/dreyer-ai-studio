"""
EPAi — SQLite metadata-wrapper
Spårar ingested filer med hash-baserad duplikatdetektion.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class IngestedFile:
    customer_id:  str
    file_name:    str
    document_type: str
    data_source:  str          # "manuell_upload" | "scheduled_job"
    time_stamp:   str          # ISO 8601
    hash_value:   str          # SHA-256
    chroma_ids:   str          # kommaseparerade chunk-IDs
    ocr_used:     int          # 0 eller 1


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ingested_files (
    hash_value      TEXT PRIMARY KEY,
    customer_id     TEXT NOT NULL,
    file_name       TEXT NOT NULL,
    document_type   TEXT,
    data_source     TEXT,
    time_stamp      TEXT,
    chroma_ids      TEXT,
    ocr_used        INTEGER DEFAULT 0
);
"""


class MetadataDB:
    def __init__(self, db_path: Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(CREATE_TABLE_SQL)
        self._conn.commit()

    # ── Skrivoperationer ───────────────────────────────────────────────────────

    def record(self, f: IngestedFile) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO ingested_files
               (hash_value, customer_id, file_name, document_type,
                data_source, time_stamp, chroma_ids, ocr_used)
               VALUES (?,?,?,?,?,?,?,?)""",
            (f.hash_value, f.customer_id, f.file_name, f.document_type,
             f.data_source, f.time_stamp, f.chroma_ids, f.ocr_used),
        )
        self._conn.commit()

    # ── Läsoperationer ─────────────────────────────────────────────────────────

    def already_ingested(self, hash_value: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM ingested_files WHERE hash_value = ?", (hash_value,)
        ).fetchone()
        return row is not None

    def count_by_customer(self, customer_id: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM ingested_files WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()
        return row[0] if row else 0

    def types_by_customer(self, customer_id: str) -> dict[str, int]:
        """Returnerar {documentType: count} för given anläggning."""
        rows = self._conn.execute(
            """SELECT document_type, COUNT(*) as n
               FROM ingested_files
               WHERE customer_id = ?
               GROUP BY document_type""",
            (customer_id,),
        ).fetchall()
        return {r["document_type"]: r["n"] for r in rows}

    def all_files(self, customer_id: Optional[str] = None) -> list[dict]:
        if customer_id:
            rows = self._conn.execute(
                "SELECT * FROM ingested_files WHERE customer_id = ?",
                (customer_id,),
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM ingested_files").fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
