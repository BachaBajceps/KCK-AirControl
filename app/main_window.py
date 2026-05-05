# app/main_window.py
'''
Główny moduł aplikacji - klasa MainWindow.
Łączy wszystkie komponenty w działającą całość.
'''
from __future__ import annotations

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

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from tkinter import Event


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

        # Status
        self._status_message = ''
        self._status_from_action = False
        self._status_reset_job: str | None = None

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

        # Skróty klawiaturowe
        self._bind_shortcuts()

        # Początkowy status
        self._set_status('Inicjalizacja...')

        # Uruchomienie pętli
        self.update()
        self.window.protocol('WM_DELETE_WINDOW', self.on_closing)

    def _bind_shortcuts(self) -> None:
        self.window.bind('<c>', self._handle_color_shortcut)
        self.window.bind('<s>', self._handle_shape_shortcut)
        self.window.bind('<r>', self._handle_reset_shortcut)

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
            self.window, relief=tk.SUNKEN, anchor='w', padding=(5, 2)
        )
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky='ew')

        self.video_label = ttk.Label(left_frame, background='black', text='Brak obrazu z kamery')
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
        else:
            self._video_photo = None
            self.video_label.configure(image='', text='Brak obrazu z kamery')

        self._update_camera_status(camera_output)
        self._process_gestures(camera_output)

        # Wygładzanie ruchu
        smoothing = ANIMATION_CONFIG.smoothing_factor
        self.state.angle_x += (self.state.target_angle_x - self.state.angle_x) * smoothing
        self.state.angle_y += (self.state.target_angle_y - self.state.angle_y) * smoothing

        self.view_3d.draw(self.state)
        self.canvas.draw()  # type: ignore[no-untyped-call]

        self.window.after(self.UPDATE_INTERVAL_MS, self.update)

    def _update_camera_status(self, camera_output: CameraOutput) -> None:
        if camera_output.gesture is Gesture.NO_CAMERA:
            self._set_status('Brak połączenia z kamerą')
            return
        if camera_output.gesture is Gesture.ERROR:
            self._set_status('Błąd odczytu kamery')
            return
        if camera_output.gesture is Gesture.NO_HAND:
            if not self._status_from_action:
                self._set_status('Wyczekuję gestu w kadrze')
            return
        if not self._status_from_action and self._status_message in {
            'Inicjalizacja...', 'Brak połączenia z kamerą', 'Błąd odczytu kamery', 'Wyczekuję gestu w kadrze'
        }:
            self._set_status('Kamera gotowa - wykonaj gest')

    def _process_gestures(self, camera_output: CameraOutput) -> None:
        if camera_output.gesture in {Gesture.NO_HAND, Gesture.NO_CAMERA, Gesture.ERROR}:
            if self.state.gesture_history:
                self.state.gesture_history.clear()
            self.state.current_stable_gesture = None
            self.state.last_action_gesture = None
            self._update_gesture_highlight(Gesture.UNKNOWN)
            return

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
                logging.debug('No action for gesture: %s', stable_gesture.value)
            self.state.last_action_gesture = stable_gesture

    def _handle_color_change(self) -> None:
        self.state.next_color()
        self.current_color_box.config(bg=self.state.get_current_color())
        next_idx = (self.state.color_index + 1) % len(self.state.colors)
        self.next_color_box.config(bg=self.state.colors[next_idx])
        color_name = self.state.color_names[self.state.color_index]
        logging.info('Color changed to %s.', color_name)
        self._set_status(f'Kolor: {color_name}', is_action=True)

    def _handle_shape_change(self) -> None:
        self.state.next_shape()
        shape_name = self.state.shape_names[self.state.shape_index]
        self.shape_label.config(text=f'Kształt: {shape_name}')
        logging.info('Shape changed to %s.', shape_name)
        self._set_status(f'Kształt: {shape_name}', is_action=True)

    def _handle_view_reset(self) -> None:
        self.state.target_angle_x, self.state.target_angle_y = 30.0, 45.0
        logging.info('View has been reset.')
        self._set_status('Widok przywrócony', is_action=True)

    def _handle_rotation_stop(self) -> None:
        self.state.target_angle_x = self.state.angle_x
        self.state.target_angle_y = self.state.angle_y
        logging.info('Rotation stopped.')
        self._set_status('Obrót zatrzymany', is_action=True)

    def _update_gesture_highlight(self, active_gesture: Gesture) -> None:
        if active_gesture not in self.gesture_frames:
            active_gesture = Gesture.UNKNOWN

        for gesture, frame in self.gesture_frames.items():
            frame_style = 'Highlight.TFrame' if gesture is active_gesture else 'TFrame'
            label_style = 'Highlight.TLabel' if gesture is active_gesture else 'TLabel'
            frame.config(style=frame_style)
            self.gesture_labels[gesture].config(style=label_style)

    def _handle_color_shortcut(self, _event: 'Event') -> str:
        self._handle_color_change()
        return 'break'

    def _handle_shape_shortcut(self, _event: 'Event') -> str:
        self._handle_shape_change()
        return 'break'

    def _handle_reset_shortcut(self, _event: 'Event') -> str:
        self._handle_view_reset()
        return 'break'

    def _set_status(self, message: str, *, is_action: bool = False) -> None:
        if message == self._status_message and self._status_from_action == is_action:
            return

        self._status_message = message
        self._status_from_action = is_action
        self.status_bar.config(text=message)

        if is_action:
            if self._status_reset_job is not None:
                self.window.after_cancel(self._status_reset_job)
            self._status_reset_job = self.window.after(2000, self._clear_action_status)
        elif self._status_reset_job is not None:
            self.window.after_cancel(self._status_reset_job)
            self._status_reset_job = None

    def _clear_action_status(self) -> None:
        self._status_from_action = False
        self._status_reset_job = None

    def on_closing(self) -> None:
        if self._status_reset_job is not None:
            self.window.after_cancel(self._status_reset_job)
        self.camera_handler.release()
        self.window.destroy()
