"""These tests use fake tensor/model objects; they do not validate YOLO accuracy."""

from siteguard.detection import PersonDetector


class FakeBox:
    def __init__(self, class_id, confidence, coordinates, track_id=None):
        self.cls = [class_id]
        self.conf = [confidence]
        self.xyxy = [coordinates]
        self.id = [track_id] if track_id is not None else None


class FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes


class FakeModel:
    def predict(self, **_kwargs):
        return [
            FakeResult(
                [
                    FakeBox(0, 0.9, [1, 2, 30, 40]),
                    FakeBox(2, 0.99, [5, 5, 10, 10]),
                ]
            )
        ]

    def track(self, **_kwargs):
        return [
            FakeResult(
                [
                    FakeBox(0, 0.88, [1, 2, 30, 40], track_id=17),
                    FakeBox(0, 0.2, [5, 5, 10, 10], track_id=18),
                ]
            )
        ]


def test_model_adapter_filters_classes_and_preserves_track_ids() -> None:
    detector = PersonDetector(confidence=0.35, device="cpu", model=FakeModel())

    detections = detector.detect(object())
    workers = detector.track(object())

    assert len(detections) == 1
    assert detections[0].bbox == (1, 2, 30, 40)
    assert len(workers) == 1
    assert workers[0].track_id == 17
