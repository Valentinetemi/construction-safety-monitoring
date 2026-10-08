from siteguard.models import TrackedWorker
from siteguard.zones import HazardZone, ZoneMonitor, point_in_polygon


SQUARE = ((10, 10), (100, 10), (100, 100), (10, 100))


def worker(worker_id: int, ground_x: int, ground_y: int) -> TrackedWorker:
    return TrackedWorker(worker_id, (ground_x - 10, ground_y - 50, ground_x + 10, ground_y), 0.9)


def test_polygon_containment_is_boundary_inclusive() -> None:
    assert point_in_polygon((50, 50), SQUARE)
    assert point_in_polygon((10, 50), SQUARE)
    assert point_in_polygon((10, 10), SQUARE)
    assert not point_in_polygon((101, 50), SQUARE)
    assert not point_in_polygon((50, 9), SQUARE)


def test_zone_emits_single_entry_and_exit_with_duration() -> None:
    monitor = ZoneMonitor([HazardZone("Excavation", SQUARE)])

    entry = monitor.update([worker(7, 50, 50)], frame_number=10, timestamp=1.0)
    repeated = monitor.update([worker(7, 55, 55)], frame_number=11, timestamp=1.1)
    exit_events = monitor.update([worker(7, 120, 50)], frame_number=30, timestamp=3.0)

    assert [event.transition for event in entry] == ["ENTRY"]
    assert repeated == []
    assert [event.transition for event in exit_events] == ["EXIT"]
    assert exit_events[0].duration_seconds == 2.0
    assert exit_events[0].reason == "observed"


def test_zone_tolerates_short_detection_drop_then_closes_lost_track() -> None:
    monitor = ZoneMonitor(
        [HazardZone("Lift", SQUARE)], missing_tolerance_frames=2
    )
    monitor.update([worker(2, 50, 50)], frame_number=1, timestamp=0.1)

    assert monitor.update([], frame_number=2, timestamp=0.2) == []
    assert monitor.update([], frame_number=3, timestamp=0.3) == []
    events = monitor.update([], frame_number=4, timestamp=0.4)

    assert len(events) == 1
    assert events[0].transition == "EXIT"
    assert events[0].reason == "track_lost"
    assert events[0].timestamp == 0.1
