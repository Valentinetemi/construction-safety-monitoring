from pathlib import Path

import pytest

from siteguard.errors import VideoDecodeError, VideoInputError
from siteguard.pipeline import AnalysisPipeline, PipelineConfig


class EmptyCapture:
    def __init__(self, _path: str) -> None:
        self.opened = True

    def isOpened(self):
        return self.opened

    def get(self, key):
        return {1: 30.0, 2: 10, 3: 640, 4: 480, 5: 0.0}.get(key, 0)

    def read(self):
        return False, None

    def release(self):
        self.opened = False


class FakeWriter:
    def isOpened(self):
        return True

    def release(self):
        pass


class FakeCV2:
    CAP_PROP_FPS = 1
    CAP_PROP_FRAME_COUNT = 2
    CAP_PROP_FRAME_WIDTH = 3
    CAP_PROP_FRAME_HEIGHT = 4
    CAP_PROP_POS_MSEC = 5

    VideoCapture = EmptyCapture

    @staticmethod
    def VideoWriter_fourcc(*_codec):
        return 0

    @staticmethod
    def VideoWriter(*_args):
        return FakeWriter()


class EmptyTracker:
    def update(self, _frame):
        return []


class NoPPE:
    available = False
    reason = "mocked unavailable detector"

    def detect(self, _frame):
        return []


def test_pipeline_rejects_missing_file_before_loading_models(tmp_path) -> None:
    config = PipelineConfig(tmp_path / "missing.mp4", tmp_path / "out")
    with pytest.raises(VideoInputError, match="does not exist"):
        AnalysisPipeline(config, tracker=EmptyTracker(), ppe_detector=NoPPE()).run()


def test_pipeline_reports_empty_video_decode_error(tmp_path) -> None:
    source = tmp_path / "empty.mp4"
    source.write_bytes(b"")
    config = PipelineConfig(source, tmp_path / "out")

    with pytest.raises(VideoDecodeError, match="No frames"):
        AnalysisPipeline(
            config,
            tracker=EmptyTracker(),
            ppe_detector=NoPPE(),
            cv2_module=FakeCV2(),
        ).run()

    assert not (tmp_path / "out" / "events.json").exists()
