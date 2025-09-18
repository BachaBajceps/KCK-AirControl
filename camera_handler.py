'''
Moduł odpowiedzialny za obsługę kamery i rozpoznawanie gestów dłoni.
Zaktualizowany o logikę ponownej inicjalizacji w przypadku utraty połączenia.
'''
import logging
from typing import Any, Final, NamedTuple

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


# Zwracany typ danych z NamedTuple dla czytelności
class CameraOutput(NamedTuple):
    frame: npt.NDArray[np.uint8] | None
    gesture: Gesture
    coords: tuple[float, float] | None


class CameraHandler:
    '''
    Ulepszona, niezawodna klasa do obsługi kamery i rozpoznawania gestów.
    Posiada mechanizm do ponownej próby inicjalizacji kamery.
    '''

    def __init__(self) -> None:
        self.config = CAMERA_CONFIG
        self.vid: cv2.VideoCapture | None = None
        self.hands: mp.solutions.hands.Hands | None = None
        self.mp_hands: Any | None = None
        self.mp_drawing: Any | None = None
        self.is_camera_available: bool = False
        self.gesture_recognizer = GestureRecognizer()

        self.initialize_camera()

    def initialize_camera(self) -> bool:
        """
        Inicjalizuje lub reinicjalizuje kamerę i model MediaPipe.
        Zwraca True w przypadku sukcesu, False w przeciwnym razie.
        """
        self.release()
        logging.info(
            "Attempting to initialize camera at index %s...", self.config.camera_index
        )
        vid = cv2.VideoCapture(self.config.camera_index)
        if not vid.isOpened():
            logging.error("Failed to open camera.")
            vid.release()
            self.is_camera_available = False
            return False

        vid.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        vid.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        vid.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.vid = vid
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=self.config.min_detection_confidence,
            min_tracking_confidence=self.config.min_tracking_confidence,
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.is_camera_available = True
        logging.info("Camera initialized successfully.")
        return True

    def _ensure_camera_ready(self) -> bool:
        if self.is_camera_available and self.vid and self.hands:
            return True
        return self.initialize_camera()

    def process_frame(self) -> CameraOutput:
        '''Przetwarza klatkę i zwraca wynik jako obiekt CameraOutput.'''
        for attempt in range(RECONNECT_ATTEMPTS):
            if not self._ensure_camera_ready() or not self.vid or not self.hands:
                return CameraOutput(frame=None, gesture=Gesture.NO_CAMERA, coords=None)

            ret, frame = self.vid.read()
            if ret:
                break

            logging.warning(
                "Could not read frame from camera (attempt %s/%s).",
                attempt + 1,
                RECONNECT_ATTEMPTS,
            )
            self.is_camera_available = False
            self.release()
        else:
            logging.error("Camera read failed after reconnection attempts.")
            return CameraOutput(frame=None, gesture=Gesture.ERROR, coords=None)

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame.flags.writeable = False
        results = self.hands.process(frame_rgb)
        frame.flags.writeable = True

        gesture = Gesture.NO_HAND
        hand_coords = None

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            if self.mp_drawing:
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )

            gesture = self.gesture_recognizer.recognize(tuple(hand_landmarks.landmark))

            if gesture is Gesture.OPEN_HAND:
                control_point = hand_landmarks.landmark[0]
                hand_coords = (control_point.x, control_point.y)

        return CameraOutput(
            frame=frame.astype(np.uint8),
            gesture=gesture,
            coords=hand_coords,
        )

    def release(self) -> None:
        '''Zwalnia zasób kamery.'''
        if self.vid and self.vid.isOpened():
            self.vid.release()
            logging.info("Camera resource released.")
        if self.hands:
            self.hands.close()
        self.vid = None
        self.hands = None
        self.mp_hands = None
        self.mp_drawing = None
        self.is_camera_available = False
