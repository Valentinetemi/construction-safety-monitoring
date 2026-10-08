"""Deterministic JSON/CSV exports and an accuracy-neutral analysis summary."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from .models import SafetyEvent, VideoMetadata

BASE_LIMITATIONS = [
    "This is a decision-support prototype, not a certified safety system.",
    "Hazard polygons are user-configured image regions, not automatically inferred hazards.",
    "Worker IDs can change after occlusion, crowd overlap, or camera cuts.",
    "Ground contact is approximated by the bottom-centre of each person box.",
    "PPE association is geometric and can be incorrect when people overlap.",
    "No accuracy metric is implied by this report; real footage requires human review.",
]


def build_summary(
    metadata: VideoMetadata,
    events: Iterable[SafetyEvent],
    worker_ids: set[int],
    frames_processed: int,
    ppe_available: bool,
    ppe_reason: str | None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    event_list = list(events)
    limitations = list(BASE_LIMITATIONS)
    if not ppe_available:
        limitations.append(
            f"PPE inference was unavailable; all PPE states were UNKNOWN. {ppe_reason or ''}".strip()
        )
    limitations.extend(warnings or [])
    return {
        "video_metadata": metadata.to_dict(),
        "frames_processed": frames_processed,
        "unique_tracking_ids": len(worker_ids),
        "worker_tracking_ids": sorted(worker_ids),
        "possible_ppe_violations": sum(
            event.event_type == "PPE_POSSIBLE_VIOLATION" for event in event_list
        ),
        "hazard_zone_entries": sum(
            event.event_type == "HAZARD_ZONE_ENTRY" for event in event_list
        ),
        "hazard_zone_exits": sum(
            event.event_type == "HAZARD_ZONE_EXIT" for event in event_list
        ),
        "total_events": len(event_list),
        "ppe_model_available": ppe_available,
        "limitations": limitations,
    }


def write_reports(
    output_dir: str | Path,
    events: Iterable[SafetyEvent],
    summary: dict[str, Any],
) -> tuple[Path, Path, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    event_list = list(events)
    events_json = directory / "events.json"
    events_csv = directory / "events.csv"
    summary_json = directory / "summary.json"

    events_json.write_text(
        json.dumps([event.to_dict() for event in event_list], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    summary_json.write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )

    fieldnames = [
        "event_id",
        "event_type",
        "worker_tracking_id",
        "video_filename",
        "source_timestamp",
        "frame_number",
        "confidence",
        "supporting_evidence",
        "description",
        "evidence_frame_path",
        "created_at",
    ]
    with events_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for event in event_list:
            record = event.to_dict()
            record["supporting_evidence"] = json.dumps(
                record["supporting_evidence"], sort_keys=True
            )
            writer.writerow(record)
    return events_json, events_csv, summary_json
