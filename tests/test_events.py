from siteguard.events import EventDeduplicator


def test_event_deduplicator_tracks_continuous_incidents() -> None:
    deduplicator = EventDeduplicator()

    assert deduplicator.activate("HAZARD_ZONE", 3, "Crane")
    assert not deduplicator.activate("HAZARD_ZONE", 3, "Crane")
    assert deduplicator.activate("HAZARD_ZONE", 3, "Excavation")

    deduplicator.deactivate("HAZARD_ZONE", 3, "Crane")
    assert deduplicator.activate("HAZARD_ZONE", 3, "Crane")
