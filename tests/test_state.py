import pytest
from app.state import AppState, Gesture
from app.config import OBJECT_CONFIG

def test_initial_state():
    state = AppState()
    assert state.shape_index == 0
    assert state.color_index == 0
    assert state.angle_x == 30.0
    assert state.angle_y == 45.0
    assert state.current_stable_gesture is None
    assert state.last_action_gesture is None

def test_next_color():
    state = AppState()
    initial_color_index = state.color_index
    state.next_color()
    assert state.color_index == (initial_color_index + 1) % len(OBJECT_CONFIG.colors)
    state.next_color()
    assert state.color_index == (initial_color_index + 2) % len(OBJECT_CONFIG.colors)

def test_next_shape():
    state = AppState()
    initial_shape_index = state.shape_index
    state.next_shape()
    assert state.shape_index == (initial_shape_index + 1) % len(OBJECT_CONFIG.shapes)
    state.next_shape()
    assert state.shape_index == (initial_shape_index + 2) % len(OBJECT_CONFIG.shapes)

def test_get_current_color():
    state = AppState()
    assert state.get_current_color() == OBJECT_CONFIG.colors[state.color_index]
    state.next_color()
    assert state.get_current_color() == OBJECT_CONFIG.colors[state.color_index]

def test_get_current_shape():
    state = AppState()
    assert state.get_current_shape() == OBJECT_CONFIG.shapes[state.shape_index]
    state.next_shape()
    assert state.get_current_shape() == OBJECT_CONFIG.shapes[state.shape_index]
