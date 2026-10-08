"""Persistent worker tracking through Ultralytics' ByteTrack integration."""

from __future__ import annotations

from typing import Any

from .detection import PersonDetector
from .models import TrackedWorker


class ByteTrackPersonTracker:
    """Keeps ByteTrack state inside one detector for one consecutive video."""

    def __init__(self, detector: PersonDetector) -> None:
        self.detector = detector

    def update(self, frame: Any) -> list[TrackedWorker]:
        return self.detector.track(frame)
