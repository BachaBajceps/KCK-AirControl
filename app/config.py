# app/config.py
"""
Centralny moduł konfiguracyjny aplikacji.

Zawiera wszystkie parametry, które można dostosować,
aby zmienić zachowanie aplikacji bez modyfikacji jej głównej logiki.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_env_file() -> None:
    """Wczytuje wartości z pliku `.env` do zmiennych środowiskowych."""
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', maxsplit=1)
        key = key.strip()
        value = _strip_quotes(value.strip())
        os.environ.setdefault(key, value)


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and ((value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    )):
        return value[1:-1]
    return value


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


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


_load_env_file()

# Inicjalizacja instancji konfiguracji z możliwością nadpisania przez zmienne środowiskowe
CAMERA_CONFIG = CameraConfig(
    min_detection_confidence=_get_float('CAMERA_MIN_DETECTION_CONFIDENCE', 0.6),
    min_tracking_confidence=_get_float('CAMERA_MIN_TRACKING_CONFIDENCE', 0.5),
    finger_straight_angle_threshold=_get_float('CAMERA_FINGER_STRAIGHT_ANGLE_THRESHOLD', 160.0),
    finger_bent_angle_threshold=_get_float('CAMERA_FINGER_BENT_ANGLE_THRESHOLD', 100.0),
    thumb_straight_angle_threshold=_get_float('CAMERA_THUMB_STRAIGHT_ANGLE_THRESHOLD', 150.0),
    camera_index=_get_int('CAMERA_INDEX', 0),
)
ANIMATION_CONFIG = AnimationConfig(
    smoothing_factor=_get_float('ANIMATION_SMOOTHING_FACTOR', 0.08),
    gesture_history_length=max(1, _get_int('ANIMATION_GESTURE_HISTORY_LENGTH', 5)),
)
OBJECT_CONFIG = ObjectConfig()
