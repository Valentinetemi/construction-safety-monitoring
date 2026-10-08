"""Ultralytics person detection with Apple Silicon selection and CPU fallback."""

from __future__ import annotations

from typing import Any

from .errors import ModelLoadError
from .models import Detection, TrackedWorker


def select_device(requested: str | None = None) -> str:
    """Return an explicit device, preferring MPS when PyTorch exposes it."""
    if requested:
        return requested
    try:
        import torch

        if torch.backends.mps.is_available():
            return "mps"
    except (ImportError, AttributeError):
        pass
    return "cpu"


def _number(value: Any) -> float:
    if hasattr(value, "item"):
        return float(value.item())
    if isinstance(value, (list, tuple)):
        return _number(value[0])
    return float(value)


def _coordinates(value: Any) -> tuple[int, int, int, int]:
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "tolist"):
        value = value.tolist()
    while len(value) == 1 and isinstance(value[0], (list, tuple)):
        value = value[0]
    return tuple(int(round(float(part))) for part in value[:4])  # type: ignore[return-value]


class PersonDetector:
    """Thin model adapter used for both detection and ByteTrack inference."""

    def __init__(
        self,
        model_name: str = "yolo11n.pt",
        confidence: float = 0.35,
        device: str | None = None,
        model: Any | None = None,
    ) -> None:
        self.model_name = model_name
        self.confidence = confidence
        self.device = select_device(device)
        self._fell_back_to_cpu = False
        if model is not None:
            self.model = model
            return
        try:
            from ultralytics import YOLO

            self.model = YOLO(model_name)
        except Exception as exc:  # Ultralytics raises several loader exception types.
            raise ModelLoadError(
                f"Could not load person model {model_name!r}: {exc}"
            ) from exc

    @property
    def fell_back_to_cpu(self) -> bool:
        return self._fell_back_to_cpu

    def _run(self, method: str, frame: Any, **kwargs: Any) -> Any:
        inference = getattr(self.model, method)
        options = {
            "source": frame,
            "conf": self.confidence,
            "classes": [0],
            "device": self.device,
            "verbose": False,
            **kwargs,
        }
        try:
            return inference(**options)
        except Exception:
            if self.device != "mps":
                raise
            self.device = "cpu"
            self._fell_back_to_cpu = True
            options["device"] = "cpu"
            return inference(**options)

    def detect(self, frame: Any) -> list[Detection]:
        results = self._run("predict", frame)
        if not results:
            return []
        detections: list[Detection] = []
        boxes = getattr(results[0], "boxes", None)
        if boxes is None:
            return detections
        for box in boxes:
            class_id = int(_number(box.cls))
            confidence = _number(box.conf)
            if class_id == 0 and confidence >= self.confidence:
                detections.append(
                    Detection(
                        bbox=_coordinates(box.xyxy), confidence=confidence
                    )
                )
        return detections

    def track(self, frame: Any) -> list[TrackedWorker]:
        results = self._run(
            "track",
            frame,
            persist=True,
            tracker="bytetrack.yaml",
        )
        if not results:
            return []
        boxes = getattr(results[0], "boxes", None)
        if boxes is None:
            return []
        workers: list[TrackedWorker] = []
        for box in boxes:
            track_id = getattr(box, "id", None)
            if track_id is None or int(_number(box.cls)) != 0:
                continue
            confidence = _number(box.conf)
            if confidence < self.confidence:
                continue
            workers.append(
                TrackedWorker(
                    track_id=int(_number(track_id)),
                    bbox=_coordinates(box.xyxy),
                    confidence=confidence,
                )
            )
        return workers
