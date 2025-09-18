# app/main_window.py
'''
Główny moduł aplikacji - klasa MainWindow.
Łączy wszystkie komponenty w działającą całość.
'''
import logging
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import TYPE_CHECKING, Final

import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

from app.config import ANIMATION_CONFIG
from app.state import AppState, Gesture
from app.view_3d import ThreeDView
from app.widgets import create_gesture_panel
from camera_handler import CameraHandler, CameraOutput

# Dalsza część bloku type-checking
if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


class MainWindow:
    '''Główna klasa aplikacji Tkinter, która zarządza UI i pętlą zdarzeń.'''

    UPDATE_INTERVAL_MS: Final[int] = 15

    def __init__(self, window: tk.Tk, window_title: str) -> None:
        # Inicjalizacja komponentów
        self.window = window
        self.state = AppState()
        self.camera_handler = CameraHandler()

        self.style = ttk.Style(self.window)
        self._configure_styles()

        # Konfiguracja okna
        self.window.title(window_title)

        # Słownik akcji powiązanych z gestami
        self.gesture_actions: dict[Gesture, Callable[[], None]] = {
            Gesture.POINTING: self._handle_color_change,
            Gesture.THUMBS_UP: self._handle_shape_change,
            Gesture.VICTORY: self._handle_view_reset,
            Gesture.FIST: self._handle_rotation_stop,
        }

        # Budowanie interfejsu
        self._setup_ui()

        # Inicjalizacja widoku 3D
        self.view_3d = ThreeDView(self.ax)

        # Deklaracja atrybutów UI, które są inicjalizowane później
        self.current_color_box: tk.Canvas
        self.next_color_box: tk.Canvas
        self.shape_label: ttk.Label
        self._video_photo: ImageTk.PhotoImage | None = None

        # Uruchomienie pętli
        self.update()
        self.window.protocol('WM_DELETE_WINDOW', self.on_closing)

    def _setup_ui(self) -> None:
        # Konfiguracja layoutu
        self.window.columnconfigure(0, weight=4)
        self.window.columnconfigure(1, weight=3)
        self.window.rowconfigure(0, weight=1)

        left_frame = ttk.Frame(self.window, padding='10')
        left_frame.grid(row=0, column=0, sticky='nsew')
        right_frame = ttk.Frame(self.window, padding='10')
        right_frame.grid(row=0, column=1, sticky='nsew')

        self.status_bar = ttk.Label(
            self.window, text='Inicjalizacja...', relief=tk.SUNKEN, anchor='w', padding=(5, 2)
        )
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky='ew')

        self.video_label = ttk.Label(left_frame, background='black')
        self.video_label.pack(fill=tk.BOTH, expand=True)

        control_panel = ttk.Frame(left_frame)
        control_panel.pack(fill=tk.X, pady=10, side=tk.BOTTOM)

        gesture_components = create_gesture_panel(control_panel)
        (
            self.gesture_frames,
            self.gesture_icons,
            self.gesture_labels,
        ) = gesture_components

        self.fig: Figure
        self.ax: Axes
        self.canvas: FigureCanvasTkAgg

        info_frame = ttk.LabelFrame(
            right_frame, text='Panel Wizualizacji', padding='10'
        )
        info_frame.pack(fill=tk.X, expand=False)

        # Reszta UI
        self._create_info_panel_widgets(info_frame)

        self.fig = plt.figure(facecolor='#f0f0f0')
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)  # type: ignore[no-untyped-call]
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=(10, 0))  # type: ignore[no-untyped-call]

    def _configure_styles(self) -> None:
        self.style.theme_use('clam')
        self.style.configure('Highlight.TFrame', background='#a3e4d7')
        self.style.configure('Highlight.TLabel', background='#a3e4d7', font=('Helvetica', 9, 'bold'))
        self.style.configure('TLabel', background='#f0f0f0')

    def _create_info_panel_widgets(self, parent: ttk.Frame | ttk.LabelFrame) -> None:
        color_frame = ttk.Frame(parent)
        color_frame.pack(fill=tk.X, pady=5)
        ttk.Label(color_frame, text='Obecny:').pack(side=tk.LEFT, padx=5)

        self.current_color_box = tk.Canvas(
            color_frame, width=20, height=20, bg=self.state.get_current_color()
        )
        self.current_color_box.pack(side=tk.LEFT)
        ttk.Label(color_frame, text='Następny:').pack(side=tk.LEFT, padx=(15, 5))
        next_color_index = (self.state.color_index + 1) % len(self.state.colors)

        self.next_color_box = tk.Canvas(
            color_frame, width=20, height=20, bg=self.state.colors[next_color_index]
        )
        self.next_color_box.pack(side=tk.LEFT)

        shape_text = f'Kształt: {self.state.shape_names[self.state.shape_index]}'
        self.shape_label = ttk.Label(parent, text=shape_text, font=('Helvetica', 12))
        self.shape_label.pack(anchor='w', padx=5, pady=5)

        ttk.Button(
            parent, text="Resetuj Widok (gest 'Victory')", command=self._handle_view_reset
        ).pack(pady=5, fill=tk.X)

    def update(self) -> None:
        camera_output: CameraOutput = self.camera_handler.process_frame()

        if camera_output.frame is not None:
            img_rgb = cv2.cvtColor(camera_output.frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img_rgb)
            self._video_photo = ImageTk.PhotoImage(image=img)
            self.video_label.configure(image=self._video_photo, text='')

        self._process_gestures(camera_output)

        # Wygładzanie ruchu
        smoothing = ANIMATION_CONFIG.smoothing_factor
        self.state.angle_x += (self.state.target_angle_x - self.state.angle_x) * smoothing
        self.state.angle_y += (self.state.target_angle_y - self.state.angle_y) * smoothing

        self.view_3d.draw(self.state)
        self.canvas.draw()  # type: ignore[no-untyped-call]

        self.window.after(self.UPDATE_INTERVAL_MS, self.update)

    def _process_gestures(self, camera_output: CameraOutput) -> None:
        self.state.gesture_history.append(camera_output.gesture)

        is_stable_gesture = (
            len(set(self.state.gesture_history)) == 1 and
            len(self.state.gesture_history) == self.state.gesture_history.maxlen
        )
        if is_stable_gesture:
            self.state.current_stable_gesture = self.state.gesture_history[0]

        active_gesture = self.state.current_stable_gesture or Gesture.UNKNOWN
        self._update_gesture_highlight(active_gesture)

        stable_gesture = self.state.current_stable_gesture

        if stable_gesture is Gesture.OPEN_HAND and camera_output.coords:
            self.state.target_angle_y = (camera_output.coords[0] - 0.5) * -360
            self.state.target_angle_x = (camera_output.coords[1] - 0.5) * 180

        if stable_gesture and stable_gesture != self.state.last_action_gesture:
            action = self.gesture_actions.get(stable_gesture)
            if action:
                action()
            else:
                logging.debug("No action for gesture: %s", stable_gesture.value)
            self.state.last_action_gesture = stable_gesture

    def _handle_color_change(self) -> None:
        self.state.next_color()
        self.current_color_box.config(bg=self.state.get_current_color())
        next_idx = (self.state.color_index + 1) % len(self.state.colors)
        self.next_color_box.config(bg=self.state.colors[next_idx])
        logging.info("Color changed to %s.", self.state.color_names[self.state.color_index])

    def _handle_shape_change(self) -> None:
        self.state.next_shape()
        shape_name = self.state.shape_names[self.state.shape_index]
        self.shape_label.config(text=f'Kształt: {shape_name}')
        logging.info("Shape changed to %s.", shape_name)

    def _handle_view_reset(self) -> None:
        self.state.target_angle_x, self.state.target_angle_y = 30.0, 45.0
        logging.info("View has been reset.")

    def _handle_rotation_stop(self) -> None:
        self.state.target_angle_x = self.state.angle_x
        self.state.target_angle_y = self.state.angle_y
        logging.info("Rotation stopped.")

    def _update_gesture_highlight(self, active_gesture: Gesture) -> None:
        if active_gesture not in self.gesture_frames:
            active_gesture = Gesture.UNKNOWN

        for gesture, frame in self.gesture_frames.items():
            frame_style = 'Highlight.TFrame' if gesture is active_gesture else 'TFrame'
            label_style = 'Highlight.TLabel' if gesture is active_gesture else 'TLabel'
            frame.config(style=frame_style)
            self.gesture_labels[gesture].config(style=label_style)

    def on_closing(self) -> None:
        self.camera_handler.release()
        self.window.destroy()
