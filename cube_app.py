"""Główny moduł aplikacji GUI do sterowania obiektem 3D."""

import os
import tkinter as tk
from collections import deque
from tkinter import ttk

import cv2
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image, ImageTk

from camera_handler import CameraHandler


class CubeApp:
    """Główna klasa aplikacji Tkinter."""

    def __init__(self, window: tk.Tk, window_title: str) -> None:
        self.window = window
        self.window.title(window_title)
        style = ttk.Style(self.window)
        style.theme_use("clam")

        self.shapes = ["CUBE", "PYRAMID", "SPHERE"]
        self.shape_names = ["Sześcian", "Piramida", "Kula"]
        self.shape_index = 0

        self.colors = ["#00FFFF", "#FF0000", "#00FF00", "#FFFF00", "#FF00FF", "#FFFFFF"]
        self.color_names = ["Cyjan", "Czerwony", "Zielony", "Żółty", "Magenta", "Biały"]
        self.color_index = 0

        self.angle_x: float = 30.0
        self.target_angle_x: float = 30.0
        self.angle_y: float = 45.0
        self.target_angle_y: float = 45.0
        self.smoothing_factor = 0.1
        self.rotation_sensitivity = 1.5

        self.gesture_history: deque[str] = deque(maxlen=5)
        self.current_stable_gesture: str | None = None
        self.last_action_gesture: str | None = None

        self.camera_handler = CameraHandler()

        self.window.columnconfigure(0, weight=4)
        self.window.columnconfigure(1, weight=3)
        self.window.rowconfigure(0, weight=1)

        left_frame = ttk.Frame(self.window, padding="10")
        left_frame.grid(row=0, column=0, sticky="nsew")
        right_frame = ttk.Frame(self.window, padding="10")
        right_frame.grid(row=0, column=1, sticky="nsew")

        self.status_bar = ttk.Label(
            self.window,
            text="Inicjalizacja...",
            relief=tk.SUNKEN,
            anchor="w",
            padding=(5, 2),
        )
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.video_label = ttk.Label(left_frame, background="black")
        self.video_label.pack(fill=tk.BOTH, expand=True)
        control_panel = ttk.Frame(left_frame)
        control_panel.pack(fill=tk.X, pady=10, side=tk.BOTTOM)
        self._create_gesture_ui(control_panel)

        info_frame = ttk.LabelFrame(
            right_frame, text="Panel Wizualizacji", padding="10",
        )
        info_frame.pack(fill=tk.X, expand=False)

        color_frame = ttk.Frame(info_frame)
        color_frame.pack(fill=tk.X, pady=5)
        ttk.Label(color_frame, text="Obecny:").pack(side=tk.LEFT, padx=5)
        self.current_color_box = tk.Canvas(
            color_frame, width=20, height=20, bg=self.colors[self.color_index],
        )
        self.current_color_box.pack(side=tk.LEFT)
        ttk.Label(color_frame, text="Następny:").pack(side=tk.LEFT, padx=(15, 5))
        next_color_index = (self.color_index + 1) % len(self.colors)
        self.next_color_box = tk.Canvas(
            color_frame, width=20, height=20, bg=self.colors[next_color_index],
        )
        self.next_color_box.pack(side=tk.LEFT)

        self.shape_label = ttk.Label(
            info_frame,
            text=f"Kształt: {self.shape_names[self.shape_index]}",
            font=("Helvetica", 12),
        )
        self.shape_label.pack(anchor="w", padx=5, pady=5)

        ttk.Button(
            info_frame, text="Resetuj Widok (gest 'Victory')", command=self.reset_view,
        ).pack(pady=5, fill=tk.X)

        self.fig = plt.figure(facecolor="#f0f0f0")
        self.ax: Axes = self.fig.add_subplot(111, projection="3d")
        self.ax.set_facecolor("#f0f0f0")
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        if not self.camera_handler.is_camera_available:
            self.show_no_camera_message()

        self.update()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def reset_view(self) -> None:
        """Resetuje pozycję obiektu do wartości początkowych."""
        self.target_angle_x, self.target_angle_y = 30.0, 45.0
        self.status_bar.config(text="Widok zresetowany.")

    def _create_gesture_ui(self, parent_frame: ttk.Frame) -> None:
        gestures_frame = ttk.LabelFrame(parent_frame, text="Wykryte Gesty", padding=10)
        gestures_frame.pack(fill=tk.X)
        self.gesture_icons: dict[str, ttk.Label] = {}
        self.gesture_frames: dict[str, ttk.Frame] = {}
        self.gesture_labels: dict[str, ttk.Label] = {}

        gestures = {
            "OPEN_HAND": "open_hand.png",
            "FIST": "fist.png",
            "POINTING": "pointing.png",
            "VICTORY": "victory.png",
            "THUMBS_UP": "thumbs_up.png",
            "UNKNOWN": "unknown.png",
        }

        for name, icon_file in gestures.items():
            frame = ttk.Frame(gestures_frame)
            frame.pack(side=tk.LEFT, padx=10, pady=5, expand=True)
            self.gesture_frames[name] = frame

            try:
                path = os.path.join("icons", icon_file)
                img = Image.open(path).resize((48, 48), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                icon_label = ttk.Label(frame, image=photo)
                icon_label.image = photo  # type: ignore[attr-defined]
                icon_label.pack()
                self.gesture_icons[name] = icon_label
            except FileNotFoundError:
                icon_label = ttk.Label(frame, text="[Ikona?]")
                icon_label.pack()

            text_label = ttk.Label(frame, text=name, anchor="center")
            text_label.pack()
            self.gesture_labels[name] = text_label

    def _update_gesture_highlight(self, active_gesture: str) -> None:
        for name in self.gesture_frames:
            is_active = name == active_gesture
            style_name = "Highlight" if is_active else ""
            self.gesture_frames[name].config(style=f"{style_name}.TFrame")
            self.gesture_labels[name].config(style=f"{style_name}.TLabel")

        style = ttk.Style()
        style.configure("Highlight.TFrame", background="#a3e4d7")
        style.configure(
            "Highlight.TLabel", background="#a3e4d7", font=("Helvetica", 9, "bold"),
        )
        style.configure("TLabel", background="#f0f0f0")

    def show_no_camera_message(self) -> None:
        """Wyświetla komunikat o braku kamery."""
        self.video_label.configure(
            text="Brak sygnału z kamery",
            font=("Helvetica", 14),
            background="gray",
            foreground="white",
        )

    def draw_shape(self) -> None:
        """Rysuje wybrany kształt 3D na kanwie Matplotlib."""
        self.ax.cla()
        shape_type = self.shapes[self.shape_index]
        color = self.colors[self.color_index]

        if shape_type == "CUBE":
            v = np.array(
                [
                    [-0.5, -0.5, -0.5],
                    [0.5, -0.5, -0.5],
                    [0.5, 0.5, -0.5],
                    [-0.5, 0.5, -0.5],
                    [-0.5, -0.5, 0.5],
                    [0.5, -0.5, 0.5],
                    [0.5, 0.5, 0.5],
                    [-0.5, 0.5, 0.5],
                ],
            )
            faces = [
                [v[j] for j in i]
                for i in [
                    [0, 1, 2, 3],
                    [4, 5, 6, 7],
                    [0, 1, 5, 4],
                    [2, 3, 7, 6],
                    [0, 3, 7, 4],
                    [1, 2, 6, 5],
                ]
            ]
            self.ax.add_collection3d(
                Poly3DCollection(
                    faces, facecolors=color, linewidths=1, edgecolors="k", alpha=0.9,
                ),
            )
        elif shape_type == "PYRAMID":
            v = np.array(
                [
                    [-0.5, -0.5, -0.5],
                    [0.5, -0.5, -0.5],
                    [0.5, 0.5, -0.5],
                    [-0.5, 0.5, -0.5],
                    [0, 0, 0.5],
                ],
            )
            faces = [
                [v[i] for i in j]
                for j in [[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4], [0, 1, 2, 3]]
            ]
            self.ax.add_collection3d(
                Poly3DCollection(
                    faces, facecolors=color, linewidths=1, edgecolors="k", alpha=0.9,
                ),
            )
        elif shape_type == "SPHERE":
            u, v = np.mgrid[0 : 2 * np.pi : 30j, 0 : np.pi : 20j]
            x = 0.5 * np.cos(u) * np.sin(v)
            y = 0.5 * np.sin(u) * np.sin(v)
            z = 0.5 * np.cos(v)
            self.ax.plot_surface(x, y, z, color=color, alpha=0.9)

        self.ax.set_xlabel("OŚ X", color="red")
        self.ax.set_ylabel("OŚ Y", color="green")
        self.ax.set_zlabel("OŚ Z", color="blue")  # type: ignore[attr-defined]

        self.ax.set_box_aspect((1, 1, 1))  # type: ignore[attr-defined]
        self.ax.set_xlim(-0.7, 0.7)
        self.ax.set_ylim(-0.7, 0.7)
        self.ax.set_zlim(-0.7, 0.7)  # type: ignore[attr-defined]
        self.ax.view_init(elev=self.angle_x, azim=self.angle_y)  # type: ignore[attr-defined]
        self.canvas.draw()

    def update(self) -> None:
        """Główna pętla aktualizująca stan aplikacji."""
        if not self.camera_handler.is_camera_available:
            self.draw_shape()
            self.window.after(500, self.update)
            return

        frame, gesture, hand_coords = self.camera_handler.process_frame()

        if frame is not None:
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk  # type: ignore[attr-defined]
            self.video_label.configure(image=imgtk, text="")

        self.gesture_history.append(gesture)
        if (
            len(set(self.gesture_history)) == 1
            and len(self.gesture_history) == self.gesture_history.maxlen
        ):
            self.current_stable_gesture = self.gesture_history[0]

        self._update_gesture_highlight(self.current_stable_gesture or "UNKNOWN")

        stable_gesture = self.current_stable_gesture

        if stable_gesture == "OPEN_HAND" and hand_coords:
            base_angle_y, base_angle_x = -360.0, 180.0
            self.target_angle_y = (
                (hand_coords[0] - 0.5) * base_angle_y * self.rotation_sensitivity
            )
            self.target_angle_x = (
                (hand_coords[1] - 0.5) * base_angle_x * self.rotation_sensitivity
            )

        if stable_gesture != self.last_action_gesture:
            if stable_gesture == "POINTING":
                self.color_index = (self.color_index + 1) % len(self.colors)
                self.current_color_box.config(bg=self.colors[self.color_index])
                next_idx = (self.color_index + 1) % len(self.colors)
                self.next_color_box.config(bg=self.colors[next_idx])
                self.status_bar.config(
                    text=f"Zmieniono kolor na {self.color_names[self.color_index]}.",
                )
            elif stable_gesture == "THUMBS_UP":
                self.shape_index = (self.shape_index + 1) % len(self.shapes)
                self.shape_label.config(
                    text=f"Kształt: {self.shape_names[self.shape_index]}",
                )
                self.status_bar.config(
                    text=f"Zmieniono kształt na {self.shape_names[self.shape_index]}.",
                )
            elif stable_gesture == "VICTORY":
                self.reset_view()
            elif stable_gesture == "FIST":
                self.target_angle_x, self.target_angle_y = self.angle_x, self.angle_y
                self.status_bar.config(text="Obrót zatrzymany.")

            self.last_action_gesture = stable_gesture

        self.angle_x += (self.target_angle_x - self.angle_x) * self.smoothing_factor
        self.angle_y += (self.target_angle_y - self.angle_y) * self.smoothing_factor

        self.draw_shape()
        self.window.after(15, self.update)

    def on_closing(self) -> None:
        """Obsługuje zamknięcie okna aplikacji."""
        self.camera_handler.release()
        self.window.destroy()
