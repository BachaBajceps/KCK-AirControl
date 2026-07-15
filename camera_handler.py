"""Webcam capture and MediaPipe hand-gesture integration."""

from __future__ import annotations

import logging
import time
from typing import Any, Final, NamedTuple, TypeAlias, cast

import cv2
import mediapipe as mp
import numpy as np
import numpy.typing as npt

from app.config import CAMERA_CONFIG
from app.gesture_recognizer import GestureRecognizer
from app.state import Gesture

FRAME_WIDTH: Final[int] = 640
FRAME_HEIGHT: Final[int] = 480
RECONNECT_ATTEMPTS: Final[int] = 2
RECONNECT_INTERVAL_SECONDS: Final[float] = 2.0

FrameArray: TypeAlias = npt.NDArray[np.uint8]


class CameraOutput(NamedTuple):
    frame: FrameArray | None
    gesture: Gesture
    coords: tuple[float, float] | None


class CameraHandler:
    """Capture frames, track one hand, and recover from camera failures."""

    def __init__(self) -> None:
        self.config = CAMERA_CONFIG
        self.vid: cv2.VideoCapture | None = None
        self.hands: Any | None = None
        self.mp_drawing: Any | None = None
        self.hand_connections: Any | None = None
        self.is_camera_available = False
        self.gesture_recognizer = GestureRecognizer()
        self._next_reconnect_at = 0.0

        self.initialize_camera()

    def initialize_camera(self) -> bool:
        """Initialize or reinitialize the camera and MediaPipe model."""
        self.release()
        logging.info('Attempting to initialize camera at index %s...', self.config.camera_index)

        vid: cv2.VideoCapture | None = None
        hands: Any | None = None
        try:
            vid = cv2.VideoCapture(self.config.camera_index)
            if not vid.isOpened():
                logging.error('Failed to open camera.')
                vid.release()
                self._defer_reconnect()
                return False

            vid.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            vid.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            vid.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            hands_solution = mp.solutions.hands
            hands = hands_solution.Hands(
                max_num_hands=1,
                min_detection_confidence=self.config.min_detection_confidence,
                min_tracking_confidence=self.config.min_tracking_confidence,
            )
            drawing_utils = mp.solutions.drawing_utils
        except (cv2.error, OSError, RuntimeError, ValueError):
            logging.exception('Could not initialize camera pipeline.')
            if hands is not None:
                hands.close()
            if vid is not None:
                vid.release()
            self._defer_reconnect()
            return False

        self.vid = vid
        self.hands = hands
        self.mp_drawing = drawing_utils
        self.hand_connections = hands_solution.HAND_CONNECTIONS
        self.is_camera_available = True
        self._next_reconnect_at = 0.0
        logging.info('Camera initialized successfully.')
        return True

    def _ensure_camera_ready(self) -> bool:
        if self.is_camera_available and self.vid is not None and self.hands is not None:
            return True
        if time.monotonic() < self._next_reconnect_at:
            return False
        return self.initialize_camera()

    def _defer_reconnect(self) -> None:
        self.is_camera_available = False
        self._next_reconnect_at = time.monotonic() + RECONNECT_INTERVAL_SECONDS

    def process_frame(self) -> CameraOutput:
        """Capture and process one frame."""
        frame: FrameArray | None = None
        for attempt in range(RECONNECT_ATTEMPTS):
            if not self._ensure_camera_ready() or self.vid is None or self.hands is None:
                return CameraOutput(frame=None, gesture=Gesture.NO_CAMERA, coords=None)

            try:
                captured, raw_frame = self.vid.read()
            except cv2.error as exc:
                logging.warning('Camera read raised an OpenCV error: %s', exc)
                captured, raw_frame = False, None

            if captured and raw_frame is not None:
                frame = cast('FrameArray', raw_frame)
                break

            logging.warning(
                'Could not read frame from camera (attempt %s/%s).',
                attempt + 1,
                RECONNECT_ATTEMPTS,
            )
            self.release()
        else:
            logging.error('Camera read failed after reconnection attempts.')
            self._defer_reconnect()
            return CameraOutput(frame=None, gesture=Gesture.ERROR, coords=None)

        hands = self.hands
        if hands is None or frame is None:
            self._defer_reconnect()
            return CameraOutput(frame=None, gesture=Gesture.ERROR, coords=None)

        try:
            frame = cast('FrameArray', cv2.flip(frame, 1))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb.flags.writeable = False
            results = hands.process(frame_rgb)

            gesture = Gesture.NO_HAND
            hand_coords = None
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                drawing_utils = self.mp_drawing
                hand_connections = self.hand_connections
                if drawing_utils is not None and hand_connections is not None:
                    drawing_utils.draw_landmarks(
                        frame,
                        hand_landmarks,
                        hand_connections,
                    )

                gesture = self.gesture_recognizer.recognize(tuple(hand_landmarks.landmark))
                if gesture is Gesture.OPEN_HAND:
                    control_point = hand_landmarks.landmark[0]
                    hand_coords = (control_point.x, control_point.y)
        except (cv2.error, IndexError, RuntimeError, TypeError, ValueError):
            logging.exception('Could not process camera frame.')
            self.release()
            self._defer_reconnect()
            return CameraOutput(frame=None, gesture=Gesture.ERROR, coords=None)

        return CameraOutput(frame=frame, gesture=gesture, coords=hand_coords)

    def release(self) -> None:
        """Release camera and MediaPipe resources."""
        if self.vid is not None:
            if self.vid.isOpened():
                self.vid.release()
                logging.info('Camera resource released.')
            else:
                self.vid.release()
        if self.hands is not None:
            try:
                self.hands.close()
            except RuntimeError as exc:
                logging.warning('Could not close MediaPipe cleanly: %s', exc)
        self.vid = None
        self.hands = None
        self.mp_drawing = None
        self.hand_connections = None
        self.is_camera_available = False
