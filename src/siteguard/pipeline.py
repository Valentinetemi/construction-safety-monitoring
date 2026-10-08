"""End-to-end offline video analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .database import SQLiteEventStore
from .detection import PersonDetector
from .errors import VideoDecodeError, VideoInputError
from .events import EventDeduplicator, ppe_event, zone_event
from .models import AnalysisResult, PPEObservation, PPEStatus, SafetyEvent
from .ppe import (
    PPEDetector,
    TemporalPPEMonitor,
    associate_ppe,
    create_ppe_detector,
)
from .reporting import build_summary, write_reports
from .tracking import ByteTrackPersonTracker
from .video import (
    open_mp4_writer,
    read_metadata,
    source_timestamp_seconds,
    validate_video_path,
)
from .zones import HazardZone, ZoneMonitor

ProgressCallback = Callable[[int, int], None]


@dataclass(frozen=True)
class PipelineConfig:
    input_path: Path
    output_dir: Path
    zones: tuple[HazardZone, ...] = field(default_factory=tuple)
    person_model: str = "yolo11n.pt"
    ppe_model_path: Path | None = None
    download_ppe_model: bool = False
    person_confidence: float = 0.35
    ppe_confidence: float = 0.35
    ppe_confirmation_frames: int = 3
    ppe_window_size: int = 5
    device: str | None = None


def _draw_annotations(
    frame: Any,
    workers: list[Any],
    observations: list[PPEObservation],
    ppe_detections: list[Any],
    zones: tuple[HazardZone, ...],
    cv2_module: Any,
) -> Any:
    import numpy as np

    observation_by_worker = {item.worker_id: item for item in observations}
    for zone in zones:
        points = np.asarray(zone.polygon, dtype=np.int32).reshape((-1, 1, 2))
        cv2_module.polylines(frame, [points], True, (0, 0, 255), 2)
        anchor = zone.polygon[0]
        cv2_module.putText(
            frame,
            f"HAZARD: {zone.name}",
            (anchor[0], max(20, anchor[1] - 8)),
            cv2_module.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 255),
            2,
        )

    for worker in workers:
        x1, y1, x2, y2 = worker.bbox
        observation = observation_by_worker.get(worker.track_id)
        status = observation.status if observation else PPEStatus.UNKNOWN
        color = {
            PPEStatus.COMPLIANT: (0, 180, 0),
            PPEStatus.POSSIBLE_VIOLATION: (0, 0, 255),
            PPEStatus.UNKNOWN: (0, 180, 255),
        }[status]
        cv2_module.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2_module.circle(frame, worker.ground_point, 5, color, -1)
        label = f"Worker {worker.track_id} | PPE {status.value}"
        if observation:
            label += f" | H:{observation.helmet.value[0]} V:{observation.vest.value[0]}"
        cv2_module.putText(
            frame,
            label,
            (x1, max(22, y1 - 8)),
            cv2_module.FONT_HERSHEY_SIMPLEX,
            0.48,
            color,
            2,
        )

    for detection in ppe_detections:
        x1, y1, x2, y2 = detection.bbox
        negative = detection.label.startswith("no ") or detection.label.startswith("without ")
        color = (0, 0, 220) if negative else (255, 160, 0)
        cv2_module.rectangle(frame, (x1, y1), (x2, y2), color, 1)
        cv2_module.putText(
            frame,
            f"{detection.label} {detection.confidence:.2f}",
            (x1, max(12, y1 - 3)),
            cv2_module.FONT_HERSHEY_SIMPLEX,
            0.38,
            color,
            1,
        )
    return frame


class AnalysisPipeline:
    def __init__(
        self,
        config: PipelineConfig,
        tracker: Any | None = None,
        ppe_detector: PPEDetector | None = None,
        cv2_module: Any | None = None,
    ) -> None:
        self.config = config
        self._tracker = tracker
        self._ppe_detector = ppe_detector
        self._cv2 = cv2_module

    def run(self, progress: ProgressCallback | None = None) -> AnalysisResult:
        source = validate_video_path(self.config.input_path)
        cv2 = self._cv2
        if cv2 is None:
            try:
                import cv2 as imported_cv2
            except ImportError as exc:
                raise VideoInputError(
                    "OpenCV is not installed; install the project dependencies first"
                ) from exc
            cv2 = imported_cv2

        capture = cv2.VideoCapture(str(source))
        if not capture.isOpened():
            capture.release()
            raise VideoInputError(f"OpenCV could not open video: {source}")
        writer = None
        store = None
        try:
            metadata = read_metadata(capture, cv2)
            output_dir = self.config.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            evidence_dir = output_dir / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)
            annotated_video = output_dir / "annotated_video.mp4"
            writer, codec = open_mp4_writer(
                annotated_video,
                metadata.fps,
                (metadata.width, metadata.height),
                cv2,
            )
            tracker = self._tracker
            if tracker is None:
                detector = PersonDetector(
                    self.config.person_model,
                    self.config.person_confidence,
                    self.config.device,
                )
                tracker = ByteTrackPersonTracker(detector)
            ppe_detector = self._ppe_detector or create_ppe_detector(
                self.config.ppe_model_path,
                self.config.download_ppe_model,
                self.config.ppe_confidence,
                self.config.device,
            )
            zone_monitor = ZoneMonitor(list(self.config.zones))
            ppe_monitor = TemporalPPEMonitor(
                self.config.ppe_confirmation_frames,
                self.config.ppe_window_size,
            )
            deduplicator = EventDeduplicator()
            database_path = output_dir / "siteguard.db"
            store = SQLiteEventStore(database_path)
            all_events: list[SafetyEvent] = []
            worker_ids: set[int] = set()
            warnings: list[str] = []
            if codec != "avc1":
                warnings.append(
                    "The output used mp4v because H.264/avc1 was unavailable; some browsers may require transcoding."
                )

            frame_number = 0
            last_timestamp = 0.0
            last_annotated_frame = None
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                position_ms = float(capture.get(cv2.CAP_PROP_POS_MSEC))
                timestamp = source_timestamp_seconds(
                    frame_number, metadata.fps, position_ms
                )
                last_timestamp = timestamp
                workers = tracker.update(frame)
                worker_ids.update(worker.track_id for worker in workers)
                ppe_detections = ppe_detector.detect(frame)
                observations = associate_ppe(workers, ppe_detections)
                new_events: list[SafetyEvent] = []

                for transition in zone_monitor.update(
                    workers, frame_number, timestamp
                ):
                    context = transition.zone_name
                    if transition.transition == "ENTRY":
                        if deduplicator.activate(
                            "HAZARD_ZONE", transition.worker_id, context
                        ):
                            new_events.append(zone_event(transition, source.name))
                    else:
                        deduplicator.deactivate(
                            "HAZARD_ZONE", transition.worker_id, context
                        )
                        new_events.append(zone_event(transition, source.name))

                for observation in observations:
                    transition = ppe_monitor.update(observation)
                    if transition.cleared:
                        deduplicator.deactivate(
                            "PPE_POSSIBLE_VIOLATION", observation.worker_id
                        )
                    if transition.confirmed_violation and deduplicator.activate(
                        "PPE_POSSIBLE_VIOLATION", observation.worker_id
                    ):
                        new_events.append(
                            ppe_event(
                                observation,
                                transition,
                                source.name,
                                frame_number,
                                timestamp,
                            )
                        )

                annotated = _draw_annotations(
                    frame,
                    workers,
                    observations,
                    ppe_detections,
                    self.config.zones,
                    cv2,
                )
                for event in new_events:
                    relative = Path("evidence") / f"{event.event_id}.jpg"
                    evidence_path = output_dir / relative
                    if cv2.imwrite(str(evidence_path), annotated):
                        event.evidence_frame_path = str(relative)
                    store.insert(event)
                    all_events.append(event)
                writer.write(annotated)
                last_annotated_frame = annotated.copy()
                frame_number += 1
                if progress:
                    progress(frame_number, metadata.frame_count)

            if frame_number == 0:
                raise VideoDecodeError(f"No frames could be decoded from {source}")
            if metadata.frame_count and frame_number < metadata.frame_count - 1:
                warnings.append(
                    f"Decoding stopped after {frame_number} of {metadata.frame_count} reported frames."
                )

            for transition in zone_monitor.finalize(
                frame_number - 1, last_timestamp
            ):
                event = zone_event(transition, source.name)
                if last_annotated_frame is not None:
                    relative = Path("evidence") / f"{event.event_id}.jpg"
                    if cv2.imwrite(
                        str(output_dir / relative), last_annotated_frame
                    ):
                        event.evidence_frame_path = str(relative)
                store.insert(event)
                all_events.append(event)

            summary = build_summary(
                metadata,
                all_events,
                worker_ids,
                frame_number,
                ppe_detector.available,
                ppe_detector.reason,
                warnings,
            )
            events_json, events_csv, summary_json = write_reports(
                output_dir, all_events, summary
            )
            return AnalysisResult(
                output_dir=output_dir,
                annotated_video=annotated_video,
                events_json=events_json,
                events_csv=events_csv,
                summary_json=summary_json,
                database_path=database_path,
                events=tuple(all_events),
                summary=summary,
            )
        finally:
            capture.release()
            if writer is not None:
                writer.release()
            if store is not None:
                store.close()


def analyze_video(
    config: PipelineConfig, progress: ProgressCallback | None = None
) -> AnalysisResult:
    return AnalysisPipeline(config).run(progress)
