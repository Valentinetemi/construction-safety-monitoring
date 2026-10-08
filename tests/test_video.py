import pytest

from siteguard.video import source_timestamp_seconds, validate_video_path
from siteguard.errors import VideoInputError


def test_timestamp_prefers_source_position() -> None:
    assert source_timestamp_seconds(30, 25.0, 1500.0) == 1.5


def test_timestamp_falls_back_to_frame_rate_when_position_missing() -> None:
    assert source_timestamp_seconds(30, 25.0, 0.0) == 1.2
    assert source_timestamp_seconds(30, 25.0, None) == 1.2


def test_missing_and_unsupported_video_are_rejected(tmp_path) -> None:
    with pytest.raises(VideoInputError, match="does not exist"):
        validate_video_path(tmp_path / "missing.mp4")

    text_file = tmp_path / "input.txt"
    text_file.write_text("not a video", encoding="utf-8")
    with pytest.raises(VideoInputError, match="Unsupported video type"):
        validate_video_path(text_file)
