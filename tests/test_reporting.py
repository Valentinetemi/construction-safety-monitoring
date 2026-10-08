import csv
import json

from siteguard.models import SafetyEvent, VideoMetadata
from siteguard.reporting import build_summary, write_reports


def test_report_generation_uses_observed_counts_only(tmp_path) -> None:
    events = [
        SafetyEvent(
            event_type="PPE_POSSIBLE_VIOLATION",
            worker_tracking_id=1,
            video_filename="demo.mp4",
            source_timestamp=2.0,
            frame_number=50,
            confidence=0.8,
            supporting_evidence={"helmet_status": "POSSIBLE_VIOLATION"},
            description="Review PPE.",
        ),
        SafetyEvent(
            event_type="HAZARD_ZONE_ENTRY",
            worker_tracking_id=2,
            video_filename="demo.mp4",
            source_timestamp=3.0,
            frame_number=75,
            confidence=0.9,
            supporting_evidence={"zone_name": "Pit"},
            description="Entered Pit.",
        ),
    ]
    metadata = VideoMetadata(25.0, 100, 1280, 720, 4.0)
    summary = build_summary(
        metadata, events, {1, 2}, 100, ppe_available=True, ppe_reason=None
    )

    events_json, events_csv, summary_json = write_reports(tmp_path, events, summary)

    assert summary["unique_tracking_ids"] == 2
    assert summary["possible_ppe_violations"] == 1
    assert summary["hazard_zone_entries"] == 1
    assert not any("accuracy" in key.lower() for key in summary)
    assert any("No accuracy metric" in item for item in summary["limitations"])
    assert len(json.loads(events_json.read_text(encoding="utf-8"))) == 2
    assert json.loads(summary_json.read_text(encoding="utf-8"))["total_events"] == 2
    with events_csv.open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 2


def test_summary_discloses_unavailable_ppe(tmp_path) -> None:
    metadata = VideoMetadata(30.0, 0, 640, 480, 0.0)
    summary = build_summary(
        metadata,
        [],
        set(),
        0,
        ppe_available=False,
        ppe_reason="weights missing",
    )
    assert any("UNKNOWN" in limitation for limitation in summary["limitations"])
