'''
Moduł odpowiedzialny za obsługę kamery i rozpoznawanie gestów dłoni.
Zaktualizowany o logikę ponownej inicjalizacji w przypadku utraty połączenia.
'''
import logging
from dataclasses import dataclass
from typing import Any, Final, NamedTuple

import cv2
import mediapipe as mp
import numpy as np
import numpy.typing as npt
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmark

# Stałe dla uniknięcia "magicznych liczb"
NUM_FINGERS: Final[int] = 4


# Zwracany typ danych z NamedTuple dla czytelności
class CameraOutput(NamedTuple):
    frame: npt.NDArray[np.uint8] | None
    gesture: str
    coords: tuple[float, float] | None


@dataclass
class CameraHandlerConfig:
    '''Klasa konfiguracyjna do łatwego dostosowywania parametrów detekcji.'''
    min_detection_confidence: float = 0.6
    min_tracking_confidence: float = 0.5
    finger_straight_angle_threshold: float = 160.0
    finger_bent_angle_threshold: float = 100.0
    thumb_straight_angle_threshold: float = 150.0


class CameraHandler:
    '''
    Ulepszona, niezawodna klasa do obsługi kamery i rozpoznawania gestów.
    Posiada mechanizm do ponownej próby inicjalizacji kamery.
    '''

    def __init__(self, camera_index: int = 0) -> None:
        self.camera_index = camera_index
        self.config = CameraHandlerConfig()
        self.vid: cv2.VideoCapture | None = None
        self.hands: mp.solutions.hands.Hands | None = None
        self.mp_drawing: Any | None = None
        self.is_camera_available: bool = False

        self.initialize_camera()

    def initialize_camera(self) -> bool:
        """
        Inicjalizuje lub reinicjalizuje kamerę i model MediaPipe.
        Zwraca True w przypadku sukcesu, False w przeciwnym razie.
        """
        logging.info("Attempting to initialize camera at index %s...", self.camera_index)
        self.vid = cv2.VideoCapture(self.camera_index)
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

    def _calculate_angle(
        self, p1: NormalizedLandmark, p2: NormalizedLandmark, p3: NormalizedLandmark
    ) -> float:
        a = np.array([p1.x, p1.y])
        b = np.array([p2.x, p2.y])
        c = np.array([p3.x, p3.y])
        ba = a - b
        bc = c - b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        return float(np.degrees(angle))

    def _get_finger_states(self, lm: list[NormalizedLandmark]) -> dict[str, str]:
        states = {}
        thumb_angle = self._calculate_angle(lm[0], lm[2], lm[4])

        is_thumb_straight = thumb_angle > self.config.thumb_straight_angle_threshold
        states['thumb'] = 'straight' if is_thumb_straight else 'bent'

        finger_indices = {
            'index': [5, 6, 8],
            'middle': [9, 10, 12],
            'ring': [13, 14, 16],
            'pinky': [17, 18, 20],
        }
        for finger, indices in finger_indices.items():
            angle = self._calculate_angle(lm[indices[0]], lm[indices[1]], lm[indices[2]])
            if angle > self.config.finger_straight_angle_threshold:
                states[finger] = 'straight'
            elif angle < self.config.finger_bent_angle_threshold:
                states[finger] = 'bent'
            else:
                states[finger] = 'unknown'
        return states

    def _recognize_gesture(self, hand_landmarks: mp.tasks.vision.HandLandmarkerResult) -> str:
        lm = hand_landmarks.landmark
        states = self._get_finger_states(lm)
        finger_names = ['index', 'middle', 'ring', 'pinky']
        straight_fingers = sum(1 for f in finger_names if states[f] == 'straight')
        bent_fingers = sum(1 for f in finger_names if states[f] == 'bent')

        if states['thumb'] == 'straight' and straight_fingers == NUM_FINGERS:
            return "OPEN_HAND"
        if states['index'] == 'straight' and bent_fingers == NUM_FINGERS:
            return "POINTING"
        is_victory = (
            states['index'] == 'straight'
            and states['middle'] == 'straight'
            and bent_fingers == 2
        )
        if is_victory:
            return "VICTORY"
        if states['thumb'] == 'straight' and bent_fingers == NUM_FINGERS:
            return "THUMBS_UP"
        if bent_fingers == NUM_FINGERS:
            return "FIST"
        return "UNKNOWN"

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

            gesture = self._recognize_gesture(hand_landmarks)

            if gesture == "OPEN_HAND":
                control_point = hand_landmarks.landmark[0]
                hand_coords = (control_point.x, control_point.y)

        return CameraOutput(frame=frame, gesture=gesture, coords=hand_coords)

    def release(self) -> None:
        '''Zwalnia zasób kamery.'''
        if self.vid and self.vid.isOpened():
            self.vid.release()
            logging.info("Camera resource released.")
        self.is_camera_available = False
