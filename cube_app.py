# cube_app.py
import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# <<< NOWOŚĆ: Importujemy nasz nowy handler
from camera_handler import CameraHandler

class CubeApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        
        # --- Zmienne sterujące ---
        self.colors = ['cyan', 'red', 'green', 'yellow', 'magenta']
        self.color_index = 0
        self.cube_color = self.colors[self.color_index]
        self.angle_x = 30
        self.angle_y = 45
        self.last_gesture = None

        # --- Inicjalizacja CameraHandler ---
        # <<< ZMIANA: Cała logika kamery jest teraz w tej klasie
        self.camera_handler = CameraHandler()
        
        # --- Główny layout (bez zmian) ---
        main_frame = tk.Frame(window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        right_frame = tk.Frame(main_frame, width=500, height=500)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Widgety w lewej kolumnie (bez zmian w definicji) ---
        self.video_label = tk.Label(left_frame)
        self.video_label.pack(padx=5, pady=5)
        info_frame = ttk.LabelFrame(left_frame, text="Dane z Aplikacji")
        info_frame.pack(fill=tk.X, padx=5, pady=10)
        self.gesture_label = ttk.Label(info_frame, text="Wykryty gest: Czekam...", font=("Helvetica", 12))
        self.gesture_label.pack(pady=5, padx=10, anchor='w')
        self.color_label = ttk.Label(info_frame, text=f"Wybrany kolor: {self.cube_color.capitalize()}", font=("Helvetica", 12))
        self.color_label.pack(pady=5, padx=10, anchor='w')

        # --- Widgety w prawej kolumnie (Kostka 3D) (bez zmian w definicji) ---
        self.fig = plt.figure(figsize=(5, 5))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- Uruchomienie pętli aktualizacji ---
        self.delay = 15
        self.update()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def draw_cube(self):
        # Ta metoda pozostaje bez zmian
        self.ax.cla()
        vertices = np.array([[0,0,0], [1,0,0], [1,1,0], [0,1,0], [0,0,1], [1,0,1], [1,1,1], [0,1,1]])
        faces = [[vertices[j] for j in [0,1,5,4]], [vertices[j] for j in [7,6,2,3]], [vertices[j] for j in [0,3,7,4]],
                 [vertices[j] for j in [1,2,6,5]], [vertices[j] for j in [4,5,6,7]], [vertices[j] for j in [0,1,2,3]]]
        poly3d = Poly3DCollection(faces, facecolors=self.cube_color, linewidths=1, edgecolors='k', alpha=0.8)
        self.ax.add_collection3d(poly3d)
        self.ax.set_xlabel('X'); self.ax.set_ylabel('Y'); self.ax.set_zlabel('Z')
        self.ax.set_xlim([0,1]); self.ax.set_ylim([0,1]); self.ax.set_zlim([0,1])
        self.ax.view_init(elev=self.angle_x, azim=self.angle_y)
        self.canvas.draw()

    def update(self):
        # <<< ZMIANA: Całkowicie nowa logika pętli update
        
        # 1. Pobierz dane z CameraHandler
        frame, gesture, hand_coords = self.camera_handler.process_frame()

        # 2. Zaktualizuj obraz z kamery w GUI
        if frame is not None:
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        # 3. Zaktualizuj etykietę z gestem
        self.gesture_label.config(text=f"Wykryty gest: {gesture}")

        # 4. Steruj kostką na podstawie gestów
        if gesture == "OPEN_HAND" and hand_coords:
            # Mapuj pozycję dłoni (0.0-1.0) na kąty obrotu
            # Oś X dłoni kontroluje obrót wokół osi Y kostki
            # Oś Y dłoni kontroluje obrót wokół osi X kostki
            self.angle_y = (hand_coords[0] - 0.5) * 360  # Obrót od -180 do 180
            self.angle_x = (1 - hand_coords[1] - 0.5) * 180 # Obrót od -90 do 90
        
        elif gesture == "POINTING" and self.last_gesture != "POINTING":
            # Zmień kolor tylko raz, przy zmianie gestu na POINTING
            self.color_index = (self.color_index + 1) % len(self.colors)
            self.cube_color = self.colors[self.color_index]
            self.color_label.config(text=f"Wybrany kolor: {self.cube_color.capitalize()}")

        # Zapisz ostatni gest, aby uniknąć wielokrotnych akcji
        self.last_gesture = gesture

        # 5. Przerysuj kostkę z nowymi parametrami
        self.draw_cube()

        # 6. Cykliczne wywołanie
        self.window.after(self.delay, self.update)
    
    def on_closing(self):
        # <<< ZMIANA: Zwalniamy zasoby przez handler
        self.camera_handler.release()
        self.window.destroy()