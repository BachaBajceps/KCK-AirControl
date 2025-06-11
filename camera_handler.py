"""
Moduł odpowiedzialny za obsługę kamery i rozpoznawanie gestów dłoni.
"""

from typing import Final

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmark

# Stałe dla uniknięcia "magicznych liczb"
NUM_FINGERS: Final[int] = 4


class CameraHandlerConfig:
    """Klasa konfiguracyjna do łatwego dostosowywania parametrów detekcji."""

    MIN_DETECTION_CONFIDENCE: float = 0.6
    MIN_TRACKING_CONFIDENCE: float = 0.5
    FINGER_STRAIGHT_ANGLE_THRESHOLD: float = 160.0
    FINGER_BENT_ANGLE_THRESHOLD: float = 100.0
    THUMB_STRAIGHT_ANGLE_THRESHOLD: float = 150.0


class CameraHandler:
    """
    Ulepszona, niezawodna klasa do obsługi kamery i rozpoznawania gestów.
    """

    def __init__(self, camera_index: int = 0) -> None:
        self.config = CameraHandlerConfig()
        self.vid: cv2.VideoCapture = cv2.VideoCapture(camera_index)
        self.is_camera_available: bool = self.vid.isOpened()
        if not self.is_camera_available:
            return

        self.mp_hands = mp.solutions.hands
        self.hands: mp.solutions.hands.Hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=self.config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=self.config.MIN_TRACKING_CONFIDENCE,
        )
        self.mp_drawing = mp.solutions.drawing_utils

    def _calculate_angle(
        self, p1: NormalizedLandmark, p2: NormalizedLandmark, p3: NormalizedLandmark,
    ) -> float:
        """Oblicza kąt (w stopniach) między trzema punktami (p2 jest wierzchołkiem)."""
        point1 = np.array([p1.x, p1.y])
        point2 = np.array([p2.x, p2.y])
        point3 = np.array([p3.x, p3.y])

        vec_ba = point1 - point2
        vec_bc = point3 - point2

        cosine_angle = np.dot(vec_ba, vec_bc) / (
            np.linalg.norm(vec_ba) * np.linalg.norm(vec_bc)
        )
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))

        return np.degrees(angle)

    def _get_finger_states(self, landmarks: list[NormalizedLandmark]) -> dict[str, str]:
        """Analizuje landmarki i zwraca stan każdego palca."""
        states: dict[str, str] = {}

        thumb_angle = self._calculate_angle(landmarks[0], landmarks[2], landmarks[4])
        states["thumb"] = (
            "straight"
            if thumb_angle > self.config.THUMB_STRAIGHT_ANGLE_THRESHOLD
            else "bent"
        )

        finger_indices = {
            "index": [5, 6, 8],
            "middle": [9, 10, 12],
            "ring": [13, 14, 16],
            "pinky": [17, 18, 20],
        }

        for finger, indices in finger_indices.items():
            angle = self._calculate_angle(
                landmarks[indices[0]], landmarks[indices[1]], landmarks[indices[2]],
            )
            if angle > self.config.FINGER_STRAIGHT_ANGLE_THRESHOLD:
                states[finger] = "straight"
            elif angle < self.config.FINGER_BENT_ANGLE_THRESHOLD:
                states[finger] = "bent"
            else:
                states[finger] = "unknown"

        return states

    def _recognize_gesture(
        self, hand_landmarks: mp.tasks.vision.HandLandmarkerResult,
    ) -> str:
        """Rozpoznaje gest na podstawie stanów palców."""
        landmarks = hand_landmarks.landmark
        states = self._get_finger_states(landmarks)

        straight_fingers = sum(
            1
            for finger in ["index", "middle", "ring", "pinky"]
            if states[finger] == "straight"
        )
        bent_fingers = sum(
            1
            for finger in ["index", "middle", "ring", "pinky"]
            if states[finger] == "bent"
        )

        if states["thumb"] == "straight" and straight_fingers == NUM_FINGERS:
            return "OPEN_HAND"
        if (
            states["index"] == "straight"
            and states["middle"] == "bent"
            and states["ring"] == "bent"
            and states["pinky"] == "bent"
        ):
            return "POINTING"
        if (
            states["index"] == "straight"
            and states["middle"] == "straight"
            and states["ring"] == "bent"
            and states["pinky"] == "bent"
        ):
            return "VICTORY"
        if states["thumb"] == "straight" and bent_fingers == NUM_FINGERS:
            return "THUMBS_UP"
        if bent_fingers == NUM_FINGERS:
            return "FIST"
        return "UNKNOWN"

    def process_frame(
        self,
    ) -> tuple[np.ndarray | None, str, tuple[float, float] | None]:
        """Przetwarza klatkę, wykrywa gest i zwraca dane."""
        if not self.is_camera_available:
            return None, "NO_CAMERA", None

        ret, frame = self.vid.read()
        if not ret:
            return None, "ERROR", None

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame.flags.writeable = False
        results = self.hands.process(frame_rgb)
        frame.flags.writeable = True

        gesture = "NO_HAND"
        hand_coords = None

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]

            self.mp_drawing.draw_landmarks(
                frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
            )

            gesture = self._recognize_gesture(hand_landmarks)

            if gesture == "OPEN_HAND":
                control_point = hand_landmarks.landmark[0]
                hand_coords = (control_point.x, control_point.y)

        return frame, gesture, hand_coords

    def release(self) -> None:
        """Zwalnia zasób kamery."""
        if self.is_camera_available and self.vid.isOpened():
            self.vid.release()
