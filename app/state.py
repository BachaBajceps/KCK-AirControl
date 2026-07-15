"""Mutable application state and gesture stabilization."""

from collections import deque
from dataclasses import dataclass, field
from enum import Enum

from app.config import ANIMATION_CONFIG, OBJECT_CONFIG


class Gesture(Enum):
    OPEN_HAND = 'OPEN_HAND'
    POINTING = 'POINTING'
    VICTORY = 'VICTORY'
    THUMBS_UP = 'THUMBS_UP'
    FIST = 'FIST'
    UNKNOWN = 'UNKNOWN'
    NO_HAND = 'NO_HAND'
    NO_CAMERA = 'NO_CAMERA'
    ERROR = 'ERROR'


NON_GESTURE_SIGNALS = frozenset({Gesture.NO_HAND, Gesture.NO_CAMERA, Gesture.ERROR})


@dataclass(slots=True)
class AppState:
    """Store the current 3D view and debounced gesture state."""

    shape_index: int = 0
    color_index: int = 0
    angle_x: float = 30.0
    target_angle_x: float = 30.0
    angle_y: float = 45.0
    target_angle_y: float = 45.0

    shapes: tuple[str, ...] = OBJECT_CONFIG.shapes
    shape_names: tuple[str, ...] = OBJECT_CONFIG.shape_names
    colors: tuple[str, ...] = OBJECT_CONFIG.colors
    color_names: tuple[str, ...] = OBJECT_CONFIG.color_names

    gesture_history: deque[Gesture] = field(
        default_factory=lambda: deque(maxlen=ANIMATION_CONFIG.gesture_history_length)
    )
    current_stable_gesture: Gesture | None = None
    last_action_gesture: Gesture | None = None

    def next_color(self) -> None:
        self.color_index = (self.color_index + 1) % len(self.colors)

    def next_shape(self) -> None:
        self.shape_index = (self.shape_index + 1) % len(self.shapes)

    def get_current_color(self) -> str:
        return self.colors[self.color_index]

    def get_current_shape(self) -> str:
        return self.shapes[self.shape_index]

    def record_gesture(self, gesture: Gesture) -> Gesture:
        """Record one camera result and return the currently stable gesture."""
        if gesture in NON_GESTURE_SIGNALS:
            self.reset_gesture_tracking()
            return Gesture.UNKNOWN

        self.gesture_history.append(gesture)
        is_stable = (
            len(self.gesture_history) == self.gesture_history.maxlen
            and len(set(self.gesture_history)) == 1
        )
        if is_stable:
            self.current_stable_gesture = gesture
        return self.current_stable_gesture or Gesture.UNKNOWN

    def reset_gesture_tracking(self) -> None:
        self.gesture_history.clear()
        self.current_stable_gesture = None
        self.last_action_gesture = None

    def set_gesture_history_length(self, length: int) -> None:
        if length < 1:
            raise ValueError('Gesture history length must be positive.')
        self.gesture_history = deque(maxlen=length)
        self.current_stable_gesture = None
        self.last_action_gesture = None
