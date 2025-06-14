'''
Główny moduł aplikacji - klasa MainWindow.
Łączy wszystkie komponenty w działającą całość.
'''
import logging
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

from app.state import AppState, Gesture
from app.view_3d import ThreeDView
from app.widgets import create_gesture_panel
from camera_handler import CameraHandler, CameraOutput


class MainWindow:
    '''Główna klasa aplikacji Tkinter, która zarządza UI i pętlą zdarzeń.'''

    def __init__(self, window: tk.Tk, window_title: str) -> None:
        # Inicjalizacja komponentów
        self.window = window
        self.state = AppState()
        self.camera_handler = CameraHandler()

        # Konfiguracja okna
        self.window.title(window_title)
        style = ttk.Style(self.window)
        style.theme_use('clam')

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

        self.status_bar = ttk.Label(self.window, text='Inicjalizacja...', relief=tk.SUNKEN, anchor='w', padding=(5, 2))
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky='ew')

        self.video_label = ttk.Label(left_frame, background='black')
        self.video_label.pack(fill=tk.BOTH, expand=True)

        control_panel = ttk.Frame(left_frame)
        control_panel.pack(fill=tk.X, pady=10, side=tk.BOTTOM)

        self.gesture_frames, self.gesture_icons, self.gesture_labels = create_gesture_panel(control_panel)

        info_frame = ttk.LabelFrame(right_frame, text='Panel Wizualizacji', padding='10')
        info_frame.pack(fill=tk.X, expand=False)

        # Reszta UI
        self._create_info_panel_widgets(info_frame)

        self.fig = plt.figure(facecolor='#f0f0f0')
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    def _create_info_panel_widgets(self, parent: ttk.Frame) -> None:
        color_frame = ttk.Frame(parent)
        color_frame.pack(fill=tk.X, pady=5)
        ttk.Label(color_frame, text='Obecny:').pack(side=tk.LEFT, padx=5)
        self.current_color_box = tk.Canvas(color_frame, width=20, height=20, bg=self.state.get_current_color())
        self.current_color_box.pack(side=tk.LEFT)
        ttk.Label(color_frame, text='Następny:').pack(side=tk.LEFT, padx=(15, 5))
        next_color_index = (self.state.color_index + 1) % len(self.state.colors)
        self.next_color_box = tk.Canvas(color_frame, width=20, height=20, bg=self.state.colors[next_color_index])
        self.next_color_box.pack(side=tk.LEFT)

        self.shape_label = ttk.Label(parent, text=f'Kształt: {self.state.shape_names[self.state.shape_index]}', font=('Helvetica', 12))
        self.shape_label.pack(anchor='w', padx=5, pady=5)

        ttk.Button(parent, text="Resetuj Widok (gest 'Victory')", command=self._handle_view_reset).pack(pady=5, fill=tk.X)

    def update(self) -> None:
        # ... Logika pozostaje bardzo podobna, ale operuje na self.state ...
        camera_output: CameraOutput = self.camera_handler.process_frame()

        if camera_output.frame is not None:
            img = Image.fromarray(cv2.cvtColor(camera_output.frame, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk  # type: ignore[attr-defined]
            self.video_label.configure(image=imgtk, text='')

        self._process_gestures(camera_output)

        # Wygładzanie ruchu
        self.state.angle_x += (self.state.target_angle_x - self.state.angle_x) * 0.08
        self.state.angle_y += (self.state.target_angle_y - self.state.angle_y) * 0.08

        self.view_3d.draw(self.state)
        self.canvas.draw()

        self.window.after(15, self.update)

    def _process_gestures(self, camera_output: CameraOutput) -> None:
        self.state.gesture_history.append(camera_output.gesture)
        if len(set(self.state.gesture_history)) == 1 and len(self.state.gesture_history) == self.state.gesture_history.maxlen:
            self.state.current_stable_gesture = self.state.gesture_history[0]

        self._update_gesture_highlight(self.state.current_stable_gesture or 'UNKNOWN')

        stable_gesture = self.state.current_stable_gesture

        if stable_gesture == Gesture.OPEN_HAND.value and camera_output.coords:
            self.state.target_angle_y = (camera_output.coords[0] - 0.5) * -360
            self.state.target_angle_x = (camera_output.coords[1] - 0.5) * 180

        if stable_gesture and stable_gesture != self.state.last_action_gesture:
            try:
                gesture_enum = Gesture(stable_gesture)
                if gesture_enum in self.gesture_actions:
                    self.gesture_actions[gesture_enum]()
            except ValueError:
                logging.debug(f"No action for gesture: {stable_gesture}")
            self.state.last_action_gesture = stable_gesture

    def _handle_color_change(self) -> None:
        self.state.next_color()
        self.current_color_box.config(bg=self.state.get_current_color())
        next_idx = (self.state.color_index + 1) % len(self.state.colors)
        self.next_color_box.config(bg=self.state.colors[next_idx])
        logging.info(f"Color changed to {self.state.color_names[self.state.color_index]}.")

    def _handle_shape_change(self) -> None:
        self.state.next_shape()
        self.shape_label.config(text=f'Kształt: {self.state.shape_names[self.state.shape_index]}')
        logging.info(f"Shape changed to {self.state.shape_names[self.state.shape_index]}.")

    def _handle_view_reset(self) -> None:
        self.state.target_angle_x, self.state.target_angle_y = 30.0, 45.0
        logging.info("View has been reset.")

    def _handle_rotation_stop(self) -> None:
        self.state.target_angle_x, self.state.target_angle_y = self.state.angle_x, self.state.angle_y
        logging.info("Rotation stopped.")

    def _update_gesture_highlight(self, active_gesture: str) -> None:
        for name, frame in self.gesture_frames.items():
            style_name = 'Highlight' if name == active_gesture else ''
            frame.config(style=f'{style_name}.TFrame')
            self.gesture_labels[name].config(style=f'{style_name}.TLabel')

        style = ttk.Style()
        style.configure('Highlight.TFrame', background='#a3e4d7')
        style.configure('Highlight.TLabel', background='#a3e4d7', font=('Helvetica', 9, 'bold'))
        style.configure('TLabel', background='#f0f0f0')

    def on_closing(self) -> None:
        self.camera_handler.release()
        self.window.destroy()
