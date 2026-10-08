from siteguard.database import SQLiteEventStore
from siteguard.models import SafetyEvent


def test_sqlite_event_round_trip_and_primary_key_deduplication(tmp_path) -> None:
    event = SafetyEvent(
        event_type="HAZARD_ZONE_ENTRY",
        worker_tracking_id=12,
        video_filename="site.mov",
        source_timestamp=1.25,
        frame_number=30,
        confidence=0.91,
        supporting_evidence={"zone_name": "Pit"},
        description="Worker entered Pit.",
        evidence_frame_path="evidence/frame.jpg",
    )
    path = tmp_path / "events.db"

    with SQLiteEventStore(path) as store:
        store.insert(event)
        store.insert(event)
        loaded = store.list_events("site.mov")

    assert len(loaded) == 1
    assert loaded[0].event_id == event.event_id
    assert loaded[0].supporting_evidence == {"zone_name": "Pit"}
    assert loaded[0].evidence_frame_path == "evidence/frame.jpg"
