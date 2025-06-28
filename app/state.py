# app/state.py
'''
Moduł definiujący stan aplikacji.
Zawiera wszystkie dane, które mogą się zmieniać w trakcie działania programu.
'''
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


@dataclass
class AppState:
    '''Przechowuje cały bieżący stan aplikacji.'''
    # Stan obiektu 3D
    shape_index: int = 0
    color_index: int = 0
    angle_x: float = 30.0
    target_angle_x: float = 30.0
    angle_y: float = 45.0
    target_angle_y: float = 45.0

    # Wczytywanie konfiguracji
    shapes: tuple[str, ...] = OBJECT_CONFIG.SHAPES
    shape_names: tuple[str, ...] = OBJECT_CONFIG.SHAPE_NAMES
    colors: tuple[str, ...] = OBJECT_CONFIG.COLORS
    color_names: tuple[str, ...] = OBJECT_CONFIG.COLOR_NAMES

    # Stan gestów
    gesture_history: deque[str] = field(
        default_factory=lambda: deque(maxlen=ANIMATION_CONFIG.GESTURE_HISTORY_LENGTH)
    )
    current_stable_gesture: str | None = None
    last_action_gesture: str | None = None

    # Metody do modyfikacji stanu
    def next_color(self) -> None:
        self.color_index = (self.color_index + 1) % len(self.colors)

    def next_shape(self) -> None:
        self.shape_index = (self.shape_index + 1) % len(self.shapes)

    def get_current_color(self) -> str:
        return self.colors[self.color_index]

    def get_current_shape(self) -> str:
        return self.shapes[self.shape_index]
