# app/widgets.py
'''
Moduł zawierający pomocnicze funkcje do budowy komponentów GUI.
'''
import logging
import os
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk


# Poprawka dla MyPy (type-arg): Dodano precyzyjne typowanie dla słowników
def create_gesture_panel(
    parent_frame: ttk.Frame,
) -> tuple[dict[str, ttk.Frame], dict[str, ttk.Label], dict[str, ttk.Label]]:
    '''Tworzy i zwraca komponenty panelu gestów.'''
    gestures_frame = ttk.LabelFrame(parent_frame, text='Wykryte Gesty', padding=10)
    gestures_frame.pack(fill=tk.X)

    gesture_icons: dict[str, ttk.Label] = {}
    gesture_frames: dict[str, ttk.Frame] = {}
    gesture_labels: dict[str, ttk.Label] = {}

    gestures = {
        'OPEN_HAND': 'open_hand.png', 'FIST': 'fist.png', 'POINTING': 'pointing.png',
        'VICTORY': 'victory.png', 'THUMBS_UP': 'thumbs_up.png', 'UNKNOWN': 'unknown.png',
    }

    for name, icon_file in gestures.items():
        frame = ttk.Frame(gestures_frame)
        frame.pack(side=tk.LEFT, padx=10, pady=5, expand=True)
        gesture_frames[name] = frame

        try:
            path = os.path.join('icons', icon_file)
            img = Image.open(path).resize((48, 48), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            icon_label = ttk.Label(frame, image=photo)
            icon_label.image = photo  # type: ignore[attr-defined]
            icon_label.pack()
            gesture_icons[name] = icon_label
        except FileNotFoundError:
            icon_label = ttk.Label(frame, text='[Ikona?]')
            icon_label.pack()
            logging.warning("Icon file not found: %s", path)

        text_label = ttk.Label(frame, text=name, anchor='center')
        text_label.pack()
        gesture_labels[name] = text_label

    return gesture_frames, gesture_icons, gesture_labels
