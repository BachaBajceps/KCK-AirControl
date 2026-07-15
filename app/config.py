"""Central configuration for camera, animation, and rendered objects."""

from __future__ import annotations

import logging
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / '.env'


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _assignment_key(line: str) -> str | None:
    candidate = line.strip()
    if candidate.startswith('export '):
        candidate = candidate.removeprefix('export ').lstrip()
    if not candidate or candidate.startswith('#') or '=' not in candidate:
        return None

    key = candidate.split('=', maxsplit=1)[0].strip()
    return key if key else None


def _load_env_file(env_path: Path = ENV_PATH) -> None:
    """Load simple ``KEY=value`` entries without overriding the real environment."""
    if not env_path.is_file():
        return

    try:
        lines = env_path.read_text(encoding='utf-8').splitlines()
    except OSError as exc:
        logging.warning('Could not read configuration file %s: %s', env_path, exc)
        return

    for raw_line in lines:
        key = _assignment_key(raw_line)
        if key is None:
            continue
        value = _strip_quotes(raw_line.split('=', maxsplit=1)[1].strip())
        os.environ.setdefault(key, value)


def write_env_values(values: Mapping[str, str], env_path: Path = ENV_PATH) -> None:
    """Update selected values in an env file while preserving unrelated entries."""
    if not values:
        return

    existing_lines = env_path.read_text(encoding='utf-8').splitlines() if env_path.exists() else []
    updated_lines: list[str] = []
    written_keys: set[str] = set()

    for line in existing_lines:
        key = _assignment_key(line)
        if key is None or key not in values:
            updated_lines.append(line)
            continue
        if key not in written_keys:
            updated_lines.append(f'{key}={values[key]}')
            written_keys.add(key)

    missing_keys = values.keys() - written_keys
    if missing_keys and updated_lines and updated_lines[-1]:
        updated_lines.append('')
    updated_lines.extend(f'{key}={values[key]}' for key in values if key in missing_keys)

    env_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = env_path.with_name(f'.{env_path.name}.tmp')
    try:
        temporary_path.write_text('\n'.join(updated_lines) + '\n', encoding='utf-8')
        temporary_path.replace(env_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def _get_float(name: str, default: float, *, minimum: float, maximum: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    if not math.isfinite(value):
        return default
    return min(maximum, max(minimum, value))


def _get_int(name: str, default: int, *, minimum: int, maximum: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    value = max(minimum, value)
    return min(maximum, value) if maximum is not None else value


@dataclass(slots=True)
class CameraConfig:
    """Camera and hand-detection parameters."""

    min_detection_confidence: float = 0.6
    min_tracking_confidence: float = 0.5
    finger_straight_angle_threshold: float = 160.0
    finger_bent_angle_threshold: float = 100.0
    thumb_straight_angle_threshold: float = 150.0
    camera_index: int = 0


@dataclass(slots=True)
class AnimationConfig:
    """Animation smoothing and gesture-debouncing parameters."""

    smoothing_factor: float = 0.08
    gesture_history_length: int = 5


@dataclass(frozen=True, slots=True)
class ObjectConfig:
    """Available 3D shapes and colors with their display names."""

    shapes: tuple[str, ...] = ('CUBE', 'PYRAMID', 'SPHERE')
    shape_names: tuple[str, ...] = ('Sześcian', 'Piramida', 'Kula')
    colors: tuple[str, ...] = (
        '#00FFFF',
        '#FF0000',
        '#00FF00',
        '#FFFF00',
        '#FF00FF',
        '#FFFFFF',
    )
    color_names: tuple[str, ...] = (
        'Cyjan',
        'Czerwony',
        'Zielony',
        'Żółty',
        'Magenta',
        'Biały',
    )

    def __post_init__(self) -> None:
        if not self.shapes or len(self.shapes) != len(self.shape_names):
            raise ValueError('Every shape must have a display name.')
        if not self.colors or len(self.colors) != len(self.color_names):
            raise ValueError('Every color must have a display name.')


_load_env_file()

CAMERA_CONFIG = CameraConfig(
    min_detection_confidence=_get_float(
        'CAMERA_MIN_DETECTION_CONFIDENCE', 0.6, minimum=0.0, maximum=1.0
    ),
    min_tracking_confidence=_get_float(
        'CAMERA_MIN_TRACKING_CONFIDENCE', 0.5, minimum=0.0, maximum=1.0
    ),
    finger_straight_angle_threshold=_get_float(
        'CAMERA_FINGER_STRAIGHT_ANGLE_THRESHOLD', 160.0, minimum=0.0, maximum=180.0
    ),
    finger_bent_angle_threshold=_get_float(
        'CAMERA_FINGER_BENT_ANGLE_THRESHOLD', 100.0, minimum=0.0, maximum=180.0
    ),
    thumb_straight_angle_threshold=_get_float(
        'CAMERA_THUMB_STRAIGHT_ANGLE_THRESHOLD', 150.0, minimum=0.0, maximum=180.0
    ),
    camera_index=_get_int('CAMERA_INDEX', 0, minimum=0),
)
ANIMATION_CONFIG = AnimationConfig(
    smoothing_factor=_get_float('ANIMATION_SMOOTHING_FACTOR', 0.08, minimum=0.01, maximum=1.0),
    gesture_history_length=_get_int('ANIMATION_GESTURE_HISTORY_LENGTH', 5, minimum=1, maximum=30),
)
OBJECT_CONFIG = ObjectConfig()
