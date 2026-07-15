from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

import camera_handler
from app.state import Gesture
from camera_handler import FRAME_HEIGHT, FRAME_WIDTH, CameraHandler


class FakeCapture:
    def __init__(self, *, opened: bool, frame: np.ndarray[Any, Any] | None = None) -> None:
        self.opened = opened
        self.frame = frame
        self.released = False

    def isOpened(self) -> bool:  # noqa: N802 - mirrors the OpenCV API
        return self.opened and not self.released

    def set(self, _property: int, _value: int) -> bool:
        return True

    def read(self) -> tuple[bool, np.ndarray[Any, Any] | None]:
        return self.frame is not None, self.frame

    def release(self) -> None:
        self.released = True


class FakeHands:
    def __init__(self) -> None:
        self.closed = False

    def process(self, _frame: np.ndarray[Any, Any]) -> SimpleNamespace:
        return SimpleNamespace(multi_hand_landmarks=None)

    def close(self) -> None:
        self.closed = True


def test_unavailable_camera_is_not_reopened_on_every_frame(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captures: list[FakeCapture] = []

    def create_capture(_index: int) -> FakeCapture:
        capture = FakeCapture(opened=False)
        captures.append(capture)
        return capture

    monkeypatch.setattr(camera_handler.cv2, 'VideoCapture', create_capture)

    handler = CameraHandler()
    output = handler.process_frame()

    assert output.gesture is Gesture.NO_CAMERA
    assert output.frame is None
    assert len(captures) == 1


def test_process_frame_without_detected_hand(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
    capture = FakeCapture(opened=True, frame=frame)
    hands = FakeHands()
    monkeypatch.setattr(camera_handler.cv2, 'VideoCapture', lambda _index: capture)
    monkeypatch.setattr(camera_handler.mp.solutions.hands, 'Hands', lambda **_kwargs: hands)

    handler = CameraHandler()
    output = handler.process_frame()
    handler.release()

    assert output.gesture is Gesture.NO_HAND
    assert output.coords is None
    assert output.frame is not None
    assert output.frame.dtype == np.uint8
    assert output.frame.shape == (FRAME_HEIGHT, FRAME_WIDTH, 3)
    assert capture.released
    assert hands.closed
