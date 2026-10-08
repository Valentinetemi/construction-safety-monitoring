"""SQLite persistence for confirmed safety events."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import SafetyEvent


class SQLiteEventStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS safety_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                worker_tracking_id INTEGER NOT NULL,
                video_filename TEXT NOT NULL,
                source_timestamp REAL NOT NULL,
                frame_number INTEGER NOT NULL,
                confidence REAL,
                supporting_evidence_json TEXT NOT NULL,
                description TEXT NOT NULL,
                evidence_frame_path TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_video ON safety_events(video_filename)"
        )
        self.connection.commit()

    def insert(self, event: SafetyEvent) -> None:
        self.connection.execute(
            """
            INSERT OR IGNORE INTO safety_events (
                event_id, event_type, worker_tracking_id, video_filename,
                source_timestamp, frame_number, confidence,
                supporting_evidence_json, description, evidence_frame_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.event_type,
                event.worker_tracking_id,
                event.video_filename,
                event.source_timestamp,
                event.frame_number,
                event.confidence,
                json.dumps(event.supporting_evidence, sort_keys=True),
                event.description,
                event.evidence_frame_path,
                event.created_at,
            ),
        )
        self.connection.commit()

    def list_events(self, video_filename: str | None = None) -> list[SafetyEvent]:
        query = "SELECT * FROM safety_events"
        parameters: tuple[str, ...] = ()
        if video_filename is not None:
            query += " WHERE video_filename = ?"
            parameters = (video_filename,)
        query += " ORDER BY source_timestamp, frame_number, created_at"
        rows = self.connection.execute(query, parameters).fetchall()
        return [
            SafetyEvent(
                event_id=row["event_id"],
                event_type=row["event_type"],
                worker_tracking_id=row["worker_tracking_id"],
                video_filename=row["video_filename"],
                source_timestamp=row["source_timestamp"],
                frame_number=row["frame_number"],
                confidence=row["confidence"],
                supporting_evidence=json.loads(row["supporting_evidence_json"]),
                description=row["description"],
                evidence_frame_path=row["evidence_frame_path"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "SQLiteEventStore":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
