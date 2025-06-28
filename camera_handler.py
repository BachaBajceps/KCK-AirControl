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
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmark

from app.config import CAMERA_CONFIG
from app.gesture_recognizer import GestureRecognizer

# Stałe dla uniknięcia "magicznych liczb"
NUM_FINGERS: Final[int] = 4


# Zwracany typ danych z NamedTuple dla czytelności
class CameraOutput(NamedTuple):
    frame: npt.NDArray[np.uint8] | None
    gesture: str
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
        self.mp_drawing: Any | None = None
        self.is_camera_available: bool = False
        self.gesture_recognizer = GestureRecognizer()

        self.initialize_camera()

    def initialize_camera(self) -> bool:
        """
        Inicjalizuje lub reinicjalizuje kamerę i model MediaPipe.
        Zwraca True w przypadku sukcesu, False w przeciwnym razie.
        """
        logging.info("Attempting to initialize camera at index %s...", self.config.camera_index)
        self.vid = cv2.VideoCapture(self.config.camera_index)
        self.is_camera_available = self.vid.isOpened()

        if self.is_camera_available:
            self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.vid.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                max_num_hands=1,
                min_detection_confidence=self.config.min_detection_confidence,
                min_tracking_confidence=self.config.min_tracking_confidence,
            )
            self.mp_drawing = mp.solutions.drawing_utils
            logging.info("Camera initialized successfully.")
            return True

        logging.error("Failed to open camera.")
        if self.vid:
            self.vid.release()
        self.is_camera_available = False
        return False

    

    def process_frame(self) -> CameraOutput:
        '''Przetwarza klatkę i zwraca wynik jako obiekt CameraOutput.'''
        if not self.is_camera_available or not self.vid or not self.hands:
            return CameraOutput(frame=None, gesture='NO_CAMERA', coords=None)

        ret, frame = self.vid.read()
        if not ret:
            logging.warning("Could not read frame from camera. Connection may be lost.")
            self.is_camera_available = False
            return CameraOutput(frame=None, gesture='ERROR', coords=None)

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame.flags.writeable = False
        results = self.hands.process(frame_rgb)
        frame.flags.writeable = True

        gesture = "NO_HAND"
        hand_coords = None

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            if self.mp_drawing:
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )

            gesture = self.gesture_recognizer.recognize(hand_landmarks.landmark).value

            if gesture == "OPEN_HAND":
                control_point = hand_landmarks.landmark[0]
                hand_coords = (control_point.x, control_point.y)

        return CameraOutput(frame=frame.astype(np.uint8), gesture=gesture, coords=hand_coords)

    def release(self) -> None:
        '''Zwalnia zasób kamery.'''
        if self.vid and self.vid.isOpened():
            self.vid.release()
            logging.info("Camera resource released.")
        self.is_camera_available = False
