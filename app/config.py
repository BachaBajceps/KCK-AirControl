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
    min_detection_confidence: float = 0.6
    min_tracking_confidence: float = 0.5
    finger_straight_angle_threshold: float = 160.0
    finger_bent_angle_threshold: float = 100.0
    thumb_straight_angle_threshold: float = 150.0
    camera_index: int = 0


@dataclass
class AnimationConfig:
    """Konfiguracja parametrów animacji i logiki."""
    smoothing_factor: float = 0.08
    gesture_history_length: int = 5


@dataclass
class ObjectConfig:
    """Konfiguracja domyślnych właściwości obiektu 3D."""
    shapes: tuple[str, ...] = ('CUBE', 'PYRAMID', 'SPHERE')
    shape_names: tuple[str, ...] = ('Sześcian', 'Piramida', 'Kula')
    colors: tuple[str, ...] = (
        '#00FFFF', '#FF0000', '#00FF00', '#FFFF00', '#FF00FF', '#FFFFFF'
    )
    color_names: tuple[str, ...] = (
        'Cyjan', 'Czerwony', 'Zielony', 'Żółty', 'Magenta', 'Biały'
    )


# Inicjalizacja instancji konfiguracji
CAMERA_CONFIG = CameraConfig()
ANIMATION_CONFIG = AnimationConfig()
OBJECT_CONFIG = ObjectConfig()
