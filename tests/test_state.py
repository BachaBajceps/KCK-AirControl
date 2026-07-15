import pytest

from app.config import OBJECT_CONFIG
from app.state import AppState, Gesture


def test_initial_state() -> None:
    state = AppState()

    assert state.shape_index == 0
    assert state.color_index == 0
    assert state.angle_x == 30.0
    assert state.angle_y == 45.0
    assert state.current_stable_gesture is None
    assert state.last_action_gesture is None


def test_next_color_wraps_around() -> None:
    state = AppState(color_index=len(OBJECT_CONFIG.colors) - 1)

    state.next_color()

    assert state.color_index == 0


def test_next_shape_wraps_around() -> None:
    state = AppState(shape_index=len(OBJECT_CONFIG.shapes) - 1)

    state.next_shape()

    assert state.shape_index == 0


def test_get_current_color() -> None:
    state = AppState()

    assert state.get_current_color() == OBJECT_CONFIG.colors[state.color_index]
    state.next_color()
    assert state.get_current_color() == OBJECT_CONFIG.colors[state.color_index]


def test_get_current_shape() -> None:
    state = AppState()

    assert state.get_current_shape() == OBJECT_CONFIG.shapes[state.shape_index]
    state.next_shape()
    assert state.get_current_shape() == OBJECT_CONFIG.shapes[state.shape_index]


def test_gesture_becomes_stable_after_full_history() -> None:
    state = AppState()
    state.set_gesture_history_length(3)

    assert state.record_gesture(Gesture.POINTING) is Gesture.UNKNOWN
    assert state.record_gesture(Gesture.POINTING) is Gesture.UNKNOWN
    assert state.record_gesture(Gesture.POINTING) is Gesture.POINTING


def test_camera_signal_resets_gesture_and_action_state() -> None:
    state = AppState()
    state.set_gesture_history_length(1)
    state.record_gesture(Gesture.FIST)
    state.last_action_gesture = Gesture.FIST

    active_gesture = state.record_gesture(Gesture.NO_HAND)

    assert active_gesture is Gesture.UNKNOWN
    assert not state.gesture_history
    assert state.current_stable_gesture is None
    assert state.last_action_gesture is None


def test_changing_history_length_resets_samples() -> None:
    state = AppState()
    state.gesture_history.append(Gesture.OPEN_HAND)

    state.set_gesture_history_length(8)

    assert state.gesture_history.maxlen == 8
    assert not state.gesture_history


def test_history_length_must_be_positive() -> None:
    state = AppState()

    with pytest.raises(ValueError, match='positive'):
        state.set_gesture_history_length(0)
