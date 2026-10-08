"""Event construction and incident-level duplicate suppression."""

from __future__ import annotations

from .models import PPEObservation, SafetyEvent
from .ppe import PPETransition
from .zones import ZoneTransition


class EventDeduplicator:
    """Track active incident keys so repeated frames do not create new alerts."""

    def __init__(self) -> None:
        self._active: set[tuple[str, int, str]] = set()

    def activate(self, event_type: str, worker_id: int, context: str = "") -> bool:
        key = (event_type, worker_id, context)
        if key in self._active:
            return False
        self._active.add(key)
        return True

    def deactivate(self, event_type: str, worker_id: int, context: str = "") -> None:
        self._active.discard((event_type, worker_id, context))


def zone_event(transition: ZoneTransition, video_filename: str) -> SafetyEvent:
    event_type = f"HAZARD_ZONE_{transition.transition}"
    if transition.transition == "ENTRY":
        description = (
            f"Worker {transition.worker_id} entered user-configured hazard zone "
            f"'{transition.zone_name}'."
        )
    else:
        description = (
            f"Worker {transition.worker_id} left user-configured hazard zone "
            f"'{transition.zone_name}' after {transition.duration_seconds:.2f} seconds."
        )
        if transition.reason != "observed":
            description += f" Exit was closed because of {transition.reason.replace('_', ' ')}."
    return SafetyEvent(
        event_type=event_type,
        worker_tracking_id=transition.worker_id,
        video_filename=video_filename,
        source_timestamp=round(transition.timestamp, 6),
        frame_number=transition.frame_number,
        confidence=transition.confidence,
        description=description,
        supporting_evidence={
            "zone_name": transition.zone_name,
            "duration_seconds": round(transition.duration_seconds, 6),
            "exit_reason": transition.reason if transition.transition == "EXIT" else None,
            "zone_is_user_configured": True,
        },
    )


def ppe_event(
    observation: PPEObservation,
    transition: PPETransition,
    video_filename: str,
    frame_number: int,
    timestamp: float,
) -> SafetyEvent:
    return SafetyEvent(
        event_type="PPE_POSSIBLE_VIOLATION",
        worker_tracking_id=observation.worker_id,
        video_filename=video_filename,
        source_timestamp=round(timestamp, 6),
        frame_number=frame_number,
        confidence=observation.confidence,
        description=(
            f"Worker {observation.worker_id} had repeated explicit negative PPE "
            "detections. Human review is required."
        ),
        supporting_evidence={
            "helmet_status": observation.helmet.value,
            "vest_status": observation.vest.value,
            "observations_in_window": transition.violation_observations,
            "window_size": transition.window_size,
            "detections": observation.evidence,
            "absence_was_not_used_as_violation_evidence": True,
        },
    )
