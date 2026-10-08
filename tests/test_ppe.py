from siteguard.models import PPEDetection, PPEObservation, PPEStatus, TrackedWorker
from siteguard.ppe import TemporalPPEMonitor, associate_ppe, create_ppe_detector


def make_observation(worker_id: int, status: PPEStatus) -> PPEObservation:
    return PPEObservation(
        worker_id=worker_id,
        helmet=status,
        vest=PPEStatus.UNKNOWN,
        status=status,
        confidence=0.8,
    )


def test_ppe_association_aggregates_positive_evidence() -> None:
    worker = TrackedWorker(4, (100, 100, 300, 500), 0.95)
    detections = [
        PPEDetection((160, 100, 230, 190), 0.91, "hardhat"),
        PPEDetection((130, 230, 270, 390), 0.87, "safety vest"),
    ]

    observation = associate_ppe([worker], detections)[0]

    assert observation.helmet == PPEStatus.COMPLIANT
    assert observation.vest == PPEStatus.COMPLIANT
    assert observation.status == PPEStatus.COMPLIANT
    assert observation.confidence == 0.87


def test_no_detection_is_unknown_not_a_violation() -> None:
    worker = TrackedWorker(4, (100, 100, 300, 500), 0.95)

    observation = associate_ppe([worker], [])[0]

    assert observation.helmet == PPEStatus.UNKNOWN
    assert observation.vest == PPEStatus.UNKNOWN
    assert observation.status == PPEStatus.UNKNOWN
    assert observation.confidence is None


def test_explicit_negative_label_is_possible_violation() -> None:
    worker = TrackedWorker(4, (100, 100, 300, 500), 0.95)
    detections = [PPEDetection((160, 105, 230, 190), 0.72, "no-hardhat")]

    observation = associate_ppe([worker], detections)[0]

    assert observation.helmet == PPEStatus.POSSIBLE_VIOLATION
    assert observation.status == PPEStatus.POSSIBLE_VIOLATION


def test_missing_ppe_weights_create_unknown_adapter(tmp_path) -> None:
    detector = create_ppe_detector(
        tmp_path / "missing.pt", download_model=False, confidence=0.35, device="cpu"
    )

    assert not detector.available
    assert "not found" in (detector.reason or "")
    assert detector.detect(object()) == []


def test_temporal_confirmation_and_continuous_incident_deduplication() -> None:
    monitor = TemporalPPEMonitor(
        confirmation_frames=3, window_size=5, clearance_frames=2
    )
    violation = make_observation(9, PPEStatus.POSSIBLE_VIOLATION)
    compliant = make_observation(9, PPEStatus.COMPLIANT)

    assert not monitor.update(violation).confirmed_violation
    assert not monitor.update(violation).confirmed_violation
    assert monitor.update(violation).confirmed_violation
    assert not monitor.update(violation).confirmed_violation
    assert not monitor.update(compliant).cleared
    assert monitor.update(compliant).cleared

    # A cleared incident can be confirmed again, but still requires fresh evidence.
    monitor.update(violation)
    monitor.update(violation)
    assert monitor.update(violation).confirmed_violation
