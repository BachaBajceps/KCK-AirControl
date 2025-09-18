# app/widgets.py
'''
Moduł zawierający pomocnicze funkcje do budowy komponentów GUI.
'''
import logging
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from PIL import Image, ImageTk

from app.state import Gesture

ICONS_DIR = Path(__file__).resolve().parent.parent / 'icons'


def create_gesture_panel(
    parent_frame: ttk.Frame,
) -> tuple[dict[Gesture, ttk.Frame], dict[Gesture, ttk.Label], dict[Gesture, ttk.Label]]:
    '''Tworzy i zwraca komponenty panelu gestów.'''
    gestures_frame = ttk.LabelFrame(parent_frame, text='Wykryte Gesty', padding=10)
    gestures_frame.pack(fill=tk.X)

    gesture_icons: dict[Gesture, ttk.Label] = {}
    gesture_frames: dict[Gesture, ttk.Frame] = {}
    gesture_labels: dict[Gesture, ttk.Label] = {}

    gestures = {
        Gesture.OPEN_HAND: 'open_hand.png',
        Gesture.FIST: 'fist.png',
        Gesture.POINTING: 'pointing.png',
        Gesture.VICTORY: 'victory.png',
        Gesture.THUMBS_UP: 'thumbs_up.png',
        Gesture.UNKNOWN: 'unknown.png',
    }

    for gesture, icon_file in gestures.items():
        frame = ttk.Frame(gestures_frame)
        frame.pack(side=tk.LEFT, padx=10, pady=5, expand=True)
        gesture_frames[gesture] = frame

        icon_path = ICONS_DIR / icon_file
        try:
            with Image.open(icon_path) as image:
                resized = image.resize((48, 48), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(resized)
            icon_label = ttk.Label(frame, image=photo)
            icon_label.image = photo  # type: ignore[attr-defined]
            icon_label.pack()
        except (FileNotFoundError, OSError) as exc:
            icon_label = ttk.Label(frame, text='[Ikona?]')
            icon_label.pack()
            logging.warning(
                "Could not load icon for %s gesture from %s: %s",
                gesture.value,
                icon_path,
                exc,
            )
        gesture_icons[gesture] = icon_label

        text_label = ttk.Label(frame, text=gesture.value, anchor='center')
        text_label.pack()
        gesture_labels[gesture] = text_label

    return gesture_frames, gesture_icons, gesture_labels
