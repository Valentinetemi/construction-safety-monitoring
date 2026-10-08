"""Polygon geometry and hazard-zone incident state management."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Point, TrackedWorker


def _on_segment(point: Point, start: Point, end: Point) -> bool:
    px, py = point
    x1, y1 = start
    x2, y2 = end
    cross = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)
    if cross != 0:
        return False
    return min(x1, x2) <= px <= max(x1, x2) and min(y1, y2) <= py <= max(y1, y2)


def point_in_polygon(point: Point, polygon: tuple[Point, ...] | list[Point]) -> bool:
    """Boundary-inclusive ray-casting test without requiring OpenCV."""
    if len(polygon) < 3:
        return False
    inside = False
    px, py = point
    previous = polygon[-1]
    for current in polygon:
        if _on_segment(point, previous, current):
            return True
        x1, y1 = previous
        x2, y2 = current
        crosses = (y1 > py) != (y2 > py)
        if crosses:
            intersection_x = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if px < intersection_x:
                inside = not inside
        previous = current
    return inside


@dataclass(frozen=True)
class HazardZone:
    name: str
    polygon: tuple[Point, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("A hazard zone requires a name")
        if len(self.polygon) < 3:
            raise ValueError("A hazard zone requires at least three points")


@dataclass(frozen=True)
class ZoneTransition:
    transition: str
    worker_id: int
    zone_name: str
    frame_number: int
    timestamp: float
    duration_seconds: float
    confidence: float | None
    reason: str = "observed"


@dataclass
class _ZoneIncident:
    entered_at: float
    entered_frame: int
    last_seen_at: float
    last_seen_frame: int
    confidence: float


class ZoneMonitor:
    """Emit one entry and one exit for each continuous worker-zone incident."""

    def __init__(
        self, zones: list[HazardZone], missing_tolerance_frames: int = 15
    ) -> None:
        self.zones = zones
        self.missing_tolerance_frames = missing_tolerance_frames
        self._inside: dict[tuple[int, str], _ZoneIncident] = {}

    def update(
        self,
        workers: list[TrackedWorker],
        frame_number: int,
        timestamp: float,
    ) -> list[ZoneTransition]:
        transitions: list[ZoneTransition] = []
        seen_workers = {worker.track_id for worker in workers}
        for worker in workers:
            for zone in self.zones:
                key = (worker.track_id, zone.name)
                inside = point_in_polygon(worker.ground_point, zone.polygon)
                incident = self._inside.get(key)
                if inside and incident is None:
                    self._inside[key] = _ZoneIncident(
                        timestamp,
                        frame_number,
                        timestamp,
                        frame_number,
                        worker.confidence,
                    )
                    transitions.append(
                        ZoneTransition(
                            "ENTRY",
                            worker.track_id,
                            zone.name,
                            frame_number,
                            timestamp,
                            0.0,
                            worker.confidence,
                        )
                    )
                elif inside and incident is not None:
                    incident.last_seen_at = timestamp
                    incident.last_seen_frame = frame_number
                    incident.confidence = worker.confidence
                elif not inside and incident is not None:
                    transitions.append(
                        self._close(key, frame_number, timestamp, "observed")
                    )

        for key, incident in list(self._inside.items()):
            if key[0] in seen_workers:
                continue
            if frame_number - incident.last_seen_frame > self.missing_tolerance_frames:
                transitions.append(
                    self._close(
                        key,
                        incident.last_seen_frame,
                        incident.last_seen_at,
                        "track_lost",
                    )
                )
        return transitions

    def _close(
        self, key: tuple[int, str], frame_number: int, timestamp: float, reason: str
    ) -> ZoneTransition:
        incident = self._inside.pop(key)
        return ZoneTransition(
            "EXIT",
            key[0],
            key[1],
            frame_number,
            timestamp,
            max(0.0, timestamp - incident.entered_at),
            incident.confidence,
            reason,
        )

    def finalize(self, frame_number: int, timestamp: float) -> list[ZoneTransition]:
        return [
            self._close(key, frame_number, timestamp, "stream_end")
            for key in list(self._inside)
        ]
