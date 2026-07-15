import pytest
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmark

from app.gesture_recognizer import GestureRecognizer
from app.state import Gesture

FINGER_INDICES = {
    'thumb': (0, 2, 4),
    'index': (5, 6, 8),
    'middle': (9, 10, 12),
    'ring': (13, 14, 16),
    'pinky': (17, 18, 20),
}

FINGER_EXTRAS = {
    'thumb': (1, 3),
    'index': (7,),
    'middle': (11,),
    'ring': (15,),
    'pinky': (19,),
}

BASE_X = {
    'thumb': -0.3,
    'index': -0.15,
    'middle': 0.0,
    'ring': 0.15,
    'pinky': 0.3,
}


def _make_landmarks(**finger_states: str) -> list[NormalizedLandmark]:
    landmarks = [NormalizedLandmark() for _ in range(21)]

    for finger, (base_idx, mid_idx, tip_idx) in FINGER_INDICES.items():
        state = finger_states.get(finger, 'bent')
        base_x = BASE_X[finger]

        if state == 'straight':
            mid_point = (base_x, 0.5)
            tip_point = (base_x, 1.0)
        else:
            mid_point = (base_x, 0.5)
            tip_point = (base_x + 0.3, 0.3)

        _set_point(landmarks[base_idx], (base_x, 0.0))
        _set_point(landmarks[mid_idx], mid_point)
        _set_point(landmarks[tip_idx], tip_point)

        for extra_idx in FINGER_EXTRAS.get(finger, ()):  # zapewnia sensowne wartości pośrednie
            blend_y = (mid_point[1] + tip_point[1]) / 2
            blend_x = tip_point[0] if state != 'straight' else base_x
            _set_point(landmarks[extra_idx], (blend_x, blend_y))

    return landmarks


def _set_point(landmark: NormalizedLandmark, coords: tuple[float, float]) -> None:
    landmark.x, landmark.y, landmark.z = coords[0], coords[1], 0.0


@pytest.fixture()
def recognizer() -> GestureRecognizer:
    return GestureRecognizer()


def test_recognize_open_hand(recognizer: GestureRecognizer) -> None:
    landmarks = _make_landmarks(
        thumb='straight', index='straight', middle='straight', ring='straight', pinky='straight'
    )
    assert recognizer.recognize(landmarks) is Gesture.OPEN_HAND


def test_recognize_thumbs_up(recognizer: GestureRecognizer) -> None:
    landmarks = _make_landmarks(
        thumb='straight', index='bent', middle='bent', ring='bent', pinky='bent'
    )
    assert recognizer.recognize(landmarks) is Gesture.THUMBS_UP


def test_recognize_pointing(recognizer: GestureRecognizer) -> None:
    landmarks = _make_landmarks(
        thumb='bent', index='straight', middle='bent', ring='bent', pinky='bent'
    )
    assert recognizer.recognize(landmarks) is Gesture.POINTING


def test_recognize_victory(recognizer: GestureRecognizer) -> None:
    landmarks = _make_landmarks(
        thumb='bent', index='straight', middle='straight', ring='bent', pinky='bent'
    )
    assert recognizer.recognize(landmarks) is Gesture.VICTORY


def test_recognize_fist(recognizer: GestureRecognizer) -> None:
    landmarks = _make_landmarks(
        thumb='bent', index='bent', middle='bent', ring='bent', pinky='bent'
    )
    assert recognizer.recognize(landmarks) is Gesture.FIST


def test_recognize_unknown_mix(recognizer: GestureRecognizer) -> None:
    landmarks = _make_landmarks(
        thumb='straight', index='straight', middle='bent', ring='straight', pinky='bent'
    )
    assert recognizer.recognize(landmarks) is Gesture.UNKNOWN


def test_recognize_rejects_incomplete_landmark_data(
    recognizer: GestureRecognizer,
) -> None:
    assert recognizer.recognize([NormalizedLandmark()]) is Gesture.UNKNOWN


def test_calculate_angle_handles_coincident_points() -> None:
    point = (1.0, 2.0, 3.0)

    assert GestureRecognizer._calculate_angle(point, point, point) == 0.0
