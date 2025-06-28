# app/config.py
"""
Centralny moduł konfiguracyjny aplikacji.

Zawiera wszystkie parametry, które można dostosować,
aby zmienić zachowanie aplikacji bez modyfikacji jej głównej logiki.
"""
from dataclasses import dataclass


@dataclass
class CameraConfig:
    """Konfiguracja parametrów detekcji gestów dla kamery."""
    MIN_DETECTION_CONFIDENCE: float = 0.6
    MIN_TRACKING_CONFIDENCE: float = 0.5
    FINGER_STRAIGHT_ANGLE_THRESHOLD: float = 160.0
    FINGER_BENT_ANGLE_THRESHOLD: float = 100.0
    THUMB_STRAIGHT_ANGLE_THRESHOLD: float = 150.0
    CAMERA_INDEX: int = 0


@dataclass
class AnimationConfig:
    """Konfiguracja parametrów animacji i logiki."""
    SMOOTHING_FACTOR: float = 0.08
    GESTURE_HISTORY_LENGTH: int = 5


@dataclass
class ObjectConfig:
    """Konfiguracja domyślnych właściwości obiektu 3D."""
    SHAPES: tuple[str, ...] = ('CUBE', 'PYRAMID', 'SPHERE')
    SHAPE_NAMES: tuple[str, ...] = ('Sześcian', 'Piramida', 'Kula')
    COLORS: tuple[str, ...] = (
        '#00FFFF', '#FF0000', '#00FF00', '#FFFF00', '#FF00FF', '#FFFFFF'
    )
    COLOR_NAMES: tuple[str, ...] = (
        'Cyjan', 'Czerwony', 'Zielony', 'Żółty', 'Magenta', 'Biały'
    )


# Inicjalizacja instancji konfiguracji
CAMERA_CONFIG = CameraConfig()
ANIMATION_CONFIG = AnimationConfig()
OBJECT_CONFIG = ObjectConfig()
