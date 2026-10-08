"""PPE-specific inference, worker association, and temporal confirmation."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .detection import _coordinates, _number, select_device
from .errors import ModelLoadError
from .models import PPEDetection, PPEObservation, PPEStatus, TrackedWorker

DEFAULT_PPE_REPOSITORY = "constructelligence/construction-site-safety-hazards"
DEFAULT_PPE_FILENAME = "buildvision-hazards-v0.3.pt"
DEFAULT_PPE_REVISION = "45d07d8e27a4754df1ea651f62153e000133bece"

HELMET_POSITIVE = {"helmet", "hardhat", "hard hat"}
HELMET_NEGATIVE = {"no helmet", "no hardhat", "without helmet"}
VEST_POSITIVE = {"vest", "safety vest", "high visibility vest", "hi vis vest"}
VEST_NEGATIVE = {
    "no vest",
    "no safety vest",
    "without vest",
    "without safety vest",
}


def normalize_label(label: str) -> str:
    return " ".join(label.lower().replace("_", " ").replace("-", " ").split())


class PPEDetector(Protocol):
    available: bool
    reason: str | None

    def detect(self, frame: Any) -> list[PPEDetection]: ...


class UnavailablePPEDetector:
    available = False

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def detect(self, frame: Any) -> list[PPEDetection]:
        return []


class UltralyticsPPEDetector:
    available = True
    reason = None

    def __init__(
        self,
        weights: str | Path,
        confidence: float = 0.35,
        device: str | None = None,
        model: Any | None = None,
    ) -> None:
        self.weights = str(weights)
        self.confidence = confidence
        self.device = select_device(device)
        self.fell_back_to_cpu = False
        if model is not None:
            self.model = model
            return
        try:
            from ultralytics import YOLO

            self.model = YOLO(self.weights)
        except Exception as exc:
            raise ModelLoadError(
                f"Could not load PPE model {self.weights!r}: {exc}"
            ) from exc

    def detect(self, frame: Any) -> list[PPEDetection]:
        options = {
            "source": frame,
            "conf": self.confidence,
            "device": self.device,
            "verbose": False,
        }
        try:
            results = self.model.predict(**options)
        except Exception:
            if self.device != "mps":
                raise
            self.device = "cpu"
            self.fell_back_to_cpu = True
            options["device"] = "cpu"
            results = self.model.predict(**options)
        if not results:
            return []
        boxes = getattr(results[0], "boxes", None)
        if boxes is None:
            return []
        names = getattr(results[0], "names", None) or getattr(self.model, "names", {})
        detections: list[PPEDetection] = []
        for box in boxes:
            class_id = int(_number(box.cls))
            label = names.get(class_id, str(class_id)) if hasattr(names, "get") else names[class_id]
            normalized = normalize_label(str(label))
            if normalized not in (
                HELMET_POSITIVE | HELMET_NEGATIVE | VEST_POSITIVE | VEST_NEGATIVE
            ):
                continue
            detections.append(
                PPEDetection(
                    bbox=_coordinates(box.xyxy),
                    confidence=_number(box.conf),
                    label=normalized,
                )
            )
        return detections


def create_ppe_detector(
    model_path: str | Path | None,
    download_model: bool,
    confidence: float,
    device: str | None,
) -> PPEDetector:
    """Create a real detector or an explicit UNKNOWN-producing adapter."""
    weights: str | Path | None = model_path
    if weights is not None and not Path(weights).is_file():
        return UnavailablePPEDetector(f"PPE weights not found: {weights}")
    if weights is None and download_model:
        try:
            from huggingface_hub import hf_hub_download

            weights = hf_hub_download(
                repo_id=DEFAULT_PPE_REPOSITORY,
                filename=DEFAULT_PPE_FILENAME,
                revision=DEFAULT_PPE_REVISION,
            )
        except Exception as exc:
            return UnavailablePPEDetector(f"PPE model download unavailable: {exc}")
    if weights is None:
        return UnavailablePPEDetector(
            "No PPE checkpoint configured; statuses are UNKNOWN"
        )
    try:
        return UltralyticsPPEDetector(weights, confidence, device)
    except ModelLoadError as exc:
        return UnavailablePPEDetector(str(exc))


def _center(box: tuple[int, int, int, int]) -> tuple[float, float]:
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def _matches_region(
    worker: TrackedWorker, detection: PPEDetection, gear: str
) -> bool:
    x1, y1, x2, y2 = worker.bbox
    width = max(1, x2 - x1)
    height = max(1, y2 - y1)
    cx, cy = _center(detection.bbox)
    horizontal_match = x1 - width * 0.08 <= cx <= x2 + width * 0.08
    if not horizontal_match:
        return False
    if gear == "helmet":
        return y1 - height * 0.12 <= cy <= y1 + height * 0.48
    return y1 + height * 0.18 <= cy <= y1 + height * 0.88


def _gear_status(
    detections: list[PPEDetection], positive: set[str], negative: set[str]
) -> tuple[PPEStatus, PPEDetection | None]:
    positive_hits = [d for d in detections if normalize_label(d.label) in positive]
    negative_hits = [d for d in detections if normalize_label(d.label) in negative]
    best_positive = max(positive_hits, key=lambda item: item.confidence, default=None)
    best_negative = max(negative_hits, key=lambda item: item.confidence, default=None)
    if best_negative and (
        best_positive is None or best_negative.confidence >= best_positive.confidence
    ):
        return PPEStatus.POSSIBLE_VIOLATION, best_negative
    if best_positive:
        return PPEStatus.COMPLIANT, best_positive
    return PPEStatus.UNKNOWN, None


def associate_ppe(
    workers: list[TrackedWorker], detections: list[PPEDetection]
) -> list[PPEObservation]:
    """Associate PPE evidence to worker head/torso regions without using absence."""
    observations: list[PPEObservation] = []
    for worker in workers:
        helmet_candidates = [
            item for item in detections if _matches_region(worker, item, "helmet")
        ]
        vest_candidates = [
            item for item in detections if _matches_region(worker, item, "vest")
        ]
        helmet, helmet_hit = _gear_status(
            helmet_candidates, HELMET_POSITIVE, HELMET_NEGATIVE
        )
        vest, vest_hit = _gear_status(vest_candidates, VEST_POSITIVE, VEST_NEGATIVE)
        if PPEStatus.POSSIBLE_VIOLATION in (helmet, vest):
            overall = PPEStatus.POSSIBLE_VIOLATION
        elif helmet == PPEStatus.COMPLIANT and vest == PPEStatus.COMPLIANT:
            overall = PPEStatus.COMPLIANT
        else:
            overall = PPEStatus.UNKNOWN
        hits = [hit for hit in (helmet_hit, vest_hit) if hit is not None]
        confidence = min((hit.confidence for hit in hits), default=None)
        observations.append(
            PPEObservation(
                worker_id=worker.track_id,
                helmet=helmet,
                vest=vest,
                status=overall,
                confidence=confidence,
                evidence={
                    "helmet_detection": (
                        {"label": helmet_hit.label, "confidence": helmet_hit.confidence}
                        if helmet_hit
                        else None
                    ),
                    "vest_detection": (
                        {"label": vest_hit.label, "confidence": vest_hit.confidence}
                        if vest_hit
                        else None
                    ),
                },
            )
        )
    return observations


@dataclass(frozen=True)
class PPETransition:
    worker_id: int
    confirmed_violation: bool = False
    cleared: bool = False
    violation_observations: int = 0
    window_size: int = 0


class TemporalPPEMonitor:
    """Confirm repeated negative labels and suppress one continuous incident."""

    def __init__(
        self,
        confirmation_frames: int = 3,
        window_size: int = 5,
        clearance_frames: int = 2,
    ) -> None:
        if confirmation_frames < 1 or window_size < confirmation_frames:
            raise ValueError("window_size must be at least confirmation_frames")
        self.confirmation_frames = confirmation_frames
        self.window_size = window_size
        self.clearance_frames = clearance_frames
        self._history: dict[int, deque[PPEStatus]] = defaultdict(
            lambda: deque(maxlen=window_size)
        )
        self._active: set[int] = set()
        self._compliant_streak: dict[int, int] = defaultdict(int)

    def update(self, observation: PPEObservation) -> PPETransition:
        worker_id = observation.worker_id
        history = self._history[worker_id]
        history.append(observation.status)
        violations = sum(
            status == PPEStatus.POSSIBLE_VIOLATION for status in history
        )
        confirmed = (
            observation.status == PPEStatus.POSSIBLE_VIOLATION
            and violations >= self.confirmation_frames
        )
        if observation.status == PPEStatus.COMPLIANT:
            self._compliant_streak[worker_id] += 1
        else:
            self._compliant_streak[worker_id] = 0

        if confirmed and worker_id not in self._active:
            self._active.add(worker_id)
            return PPETransition(
                worker_id,
                confirmed_violation=True,
                violation_observations=violations,
                window_size=len(history),
            )
        if (
            worker_id in self._active
            and self._compliant_streak[worker_id] >= self.clearance_frames
        ):
            self._active.remove(worker_id)
            history.clear()
            return PPETransition(worker_id, cleared=True)
        return PPETransition(
            worker_id,
            violation_observations=violations,
            window_size=len(history),
        )
