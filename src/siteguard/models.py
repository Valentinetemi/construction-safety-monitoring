"""Shared, dependency-light domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

BBox = tuple[int, int, int, int]
Point = tuple[int, int]


class PPEStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    POSSIBLE_VIOLATION = "POSSIBLE_VIOLATION"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Detection:
    bbox: BBox
    confidence: float
    label: str = "person"


@dataclass(frozen=True)
class TrackedWorker:
    track_id: int
    bbox: BBox
    confidence: float

    @property
    def ground_point(self) -> Point:
        x1, _y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, y2)


@dataclass(frozen=True)
class PPEDetection:
    bbox: BBox
    confidence: float
    label: str


@dataclass(frozen=True)
class PPEObservation:
    worker_id: int
    helmet: PPEStatus
    vest: PPEStatus
    status: PPEStatus
    confidence: float | None
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VideoMetadata:
    fps: float
    frame_count: int
    width: int
    height: int
    duration_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SafetyEvent:
    event_type: str
    worker_tracking_id: int
    video_filename: str
    source_timestamp: float
    frame_number: int
    description: str
    confidence: float | None = None
    supporting_evidence: dict[str, Any] = field(default_factory=dict)
    evidence_frame_path: str | None = None
    event_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AnalysisResult:
    output_dir: Path
    annotated_video: Path
    events_json: Path
    events_csv: Path
    summary_json: Path
    database_path: Path
    events: tuple[SafetyEvent, ...]
    summary: dict[str, Any]
