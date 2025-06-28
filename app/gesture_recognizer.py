# app/gesture_recognizer.py
"""
Moduł odpowiedzialny za rozpoznawanie gestów na podstawie punktów orientacyjnych dłoni.
"""
from app.config import CAMERA_CONFIG
from app.state import Gesture


class GestureRecognizer:
    """
    Klasa do rozpoznawania gestów na podstawie punktów orientacyjnych dłoni.
    """

    def __init__(self) -> None:
        self.config = CAMERA_CONFIG

    def recognize(self, landmarks: list) -> Gesture:
        """
        Rozpoznaje gest na podstawie dostarczonych punktów orientacyjnych.
        """
        if not landmarks:
            return Gesture.UNKNOWN

        finger_states = self._get_finger_states(landmarks)
        return self._map_states_to_gesture(finger_states)

    def _get_finger_states(self, landmarks: list) -> dict[str, str]:
        """
        Określa stan każdego palca (zgięty, prosty, nieznany).
        """
        states = {}
        thumb_angle = self._calculate_angle(landmarks[0], landmarks[2], landmarks[4])

        is_thumb_straight = thumb_angle > self.config.thumb_straight_angle_threshold
        states['thumb'] = 'straight' if is_thumb_straight else 'bent'

        finger_indices = {
            'index': (5, 6, 8),
            'middle': (9, 10, 12),
            'ring': (13, 14, 16),
            'pinky': (17, 18, 20),
        }
        for finger, indices in finger_indices.items():
            angle = self._calculate_angle(
                landmarks[indices[0]], landmarks[indices[1]], landmarks[indices[2]]
            )
            if angle > self.config.finger_straight_angle_threshold:
                states[finger] = 'straight'
            elif angle < self.config.finger_bent_angle_threshold:
                states[finger] = 'bent'
            else:
                states[finger] = 'unknown'
        return states

    def _map_states_to_gesture(self, states: dict[str, str]) -> Gesture:
        """
        Mapuje stany palców na konkretny gest.
        """
        if all(s == 'straight' for s in states.values()):
            return Gesture.OPEN_HAND
        if (
            states['thumb'] == 'straight' and
            all(states[f] == 'bent' for f in ['index', 'middle', 'ring', 'pinky'])
        ):
            return Gesture.THUMBS_UP
        if (
            states['index'] == 'straight' and
            all(states[f] == 'bent' for f in ['thumb', 'middle', 'ring', 'pinky'])
        ):
            return Gesture.POINTING
        if (
            states['index'] == 'straight' and
            states['middle'] == 'straight' and
            all(states[f] == 'bent' for f in ['thumb', 'ring', 'pinky'])
        ):
            return Gesture.VICTORY
        if all(s == 'bent' for s in states.values()):
            return Gesture.FIST
        return Gesture.UNKNOWN

    @staticmethod
    def _calculate_angle(p1: tuple, p2: tuple, p3: tuple) -> float:
        """
        Oblicza kąt pomiędzy trzema punktami.
        """
        import numpy as np
        p1_arr, p2_arr, p3_arr = np.array(p1), np.array(p2), np.array(p3)
        v1 = p1_arr - p2_arr
        v2 = p3_arr - p2_arr
        dot_product = np.dot(v1, v2)
        norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
        if norm_product == 0:
            return 0.0
        angle = np.arccos(dot_product / norm_product)
        return np.degrees(angle)
