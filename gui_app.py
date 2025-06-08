
import tkinter as tk
from tkinter import ttk
import cv2
import mediapipe as mp
from PIL import Image, ImageTk
import numpy as np
from hand_tracking import process_frame # Assuming process_frame is in hand_tracking.py

class HandControlApp:
    def __init__(self, window, window_title="Hand Controlled Cube"):
        self.window = window
        self.window.title(window_title)
        self.window.geometry("1000x700") # Set a default window size

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        self.mp_draw = mp.solutions.drawing_utils

        self.vid = cv2.VideoCapture(0)
        if not self.vid.isOpened():
            tk.messagebox.showerror("Error", "Could not open webcam.")
            self.window.destroy()
            return

        # Create a main frame to hold everything
        main_frame = ttk.Frame(window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left side: Webcam Feed
        webcam_frame = ttk.LabelFrame(main_frame, text="Webcam Feed", padding="10")
        webcam_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(webcam_frame, width=640, height=480, bg="black")
        self.canvas.pack()

        self.data_label = ttk.Label(webcam_frame, text="Hand Data: X: 0, Y: 0", font=("Arial", 14))
        self.data_label.pack(pady=10)

        # Right side: Cube Placeholder
        cube_frame = ttk.LabelFrame(main_frame, text="3D Cube Control", padding="10")
        cube_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.cube_placeholder_label = ttk.Label(cube_frame, text="3D Cube Placeholder\n(Integrate 3D library here)",
                                                font=("Arial", 16), anchor="center", justify="center")
        self.cube_placeholder_label.pack(expand=True, fill=tk.BOTH)
        
        self.cube_info_label = ttk.Label(cube_frame, text="""
        To make the cube interactive, you would integrate a Python 3D library
        (e.g., PyOpenGL, Panda3D, or a custom rendering solution) here.
        The hand data from the webcam feed would then be used to control
        the cube's position, rotation, or scale.
        This environment does not support 3D rendering or GUI display for testing.
        """, wraplength=350, justify=tk.LEFT)
        self.cube_info_label.pack(pady=10)


        self.delay = 10 # milliseconds
        self.update_frame()

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_frame(self):
        ret, frame = self.vid.read()
        if ret:
            # Process the frame using the function from hand_tracking.py
            processed_frame, results = process_frame(frame, self.hands, self.mp_draw, self.mp_hands)
            
            # Update hand data display
            if results and results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    for id, lm in enumerate(hand_landmarks.landmark):
                        if id == 8: # Index finger tip
                            h, w, c = processed_frame.shape
                            cx, cy = int(lm.x * w), int(lm.y * h)
                            self.data_label.config(text=f"Hand Data: X: {cx}, Y: {cy}")
                            # Here you would pass cx, cy to your 3D cube logic
                            break # Only need data for one hand/finger for now
            else:
                self.data_label.config(text="Hand Data: X: 0, Y: 0 (No hand detected)")

            # Convert image for Tkinter
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        
        self.window.after(self.delay, self.update_frame)

    def on_closing(self):
        if self.vid.isOpened():
            self.vid.release()
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = HandControlApp(root)
    root.mainloop()

