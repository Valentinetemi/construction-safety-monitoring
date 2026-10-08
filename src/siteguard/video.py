"""Video validation, metadata, timestamp, and MP4 writer helpers."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .errors import VideoInputError, VideoWriterError
from .models import VideoMetadata

SUPPORTED_VIDEO_SUFFIXES = {".mp4", ".mov"}


def validate_video_path(path: str | Path) -> Path:
    source = Path(path)
    if not source.is_file():
        raise VideoInputError(f"Video file does not exist: {source}")
    if source.suffix.lower() not in SUPPORTED_VIDEO_SUFFIXES:
        raise VideoInputError(
            f"Unsupported video type {source.suffix or '(none)'!r}; use MP4 or MOV"
        )
    return source


def read_metadata(capture: Any, cv2_module: Any) -> VideoMetadata:
    fps = float(capture.get(cv2_module.CAP_PROP_FPS))
    frame_count = max(0, int(capture.get(cv2_module.CAP_PROP_FRAME_COUNT)))
    width = int(capture.get(cv2_module.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2_module.CAP_PROP_FRAME_HEIGHT))
    if not math.isfinite(fps) or fps <= 0:
        raise VideoInputError("Video reports an invalid or missing frame rate")
    if width <= 0 or height <= 0:
        raise VideoInputError("Video reports an invalid frame size")
    return VideoMetadata(
        fps=fps,
        frame_count=frame_count,
        width=width,
        height=height,
        duration_seconds=(frame_count / fps if frame_count else 0.0),
    )


def source_timestamp_seconds(
    frame_number: int, fps: float, position_milliseconds: float | None
) -> float:
    if (
        position_milliseconds is not None
        and math.isfinite(position_milliseconds)
        and position_milliseconds >= 0
        and (frame_number == 0 or position_milliseconds > 0)
    ):
        return position_milliseconds / 1000.0
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError("fps must be positive")
    return frame_number / fps


def open_mp4_writer(
    output_path: str | Path,
    fps: float,
    size: tuple[int, int],
    cv2_module: Any,
) -> tuple[Any, str]:
    path = str(output_path)
    for codec in ("avc1", "mp4v"):
        writer = cv2_module.VideoWriter(
            path, cv2_module.VideoWriter_fourcc(*codec), fps, size
        )
        if writer.isOpened():
            return writer, codec
        writer.release()
    raise VideoWriterError(
        "Could not initialize an MP4 writer with the avc1 or mp4v codec"
    )
