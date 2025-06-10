import cv2
import mediapipe as mp
import numpy as np
import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import *

# Initialize MediaPipe hand detection
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Cube vertices and edges
vertices = [
    [1, 1, -1],
    [1, -1, -1],
    [-1, -1, -1],
    [-1, 1, -1],
    [1, 1, 1],
    [1, -1, 1],
    [-1, -1, 1],
    [-1, 1, 1]
]

edges = (
    (0,1),(1,2),(2,3),(3,0),
    (4,5),(5,6),(6,7),(7,4),
    (0,4),(1,5),(2,6),(3,7)
)

def draw_cube():
    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glVertex3fv(vertices[vertex])
    glEnd()


def distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Hand Controlled Cube")
    gluPerspective(45, (800/600), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5)

    cap = cv2.VideoCapture(0)
    rotation_x, rotation_y = 0, 0
    scale = 1.0

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise SystemExit

            ret, frame = cap.read()
            if not ret:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)

            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Get index finger and pinky tips
                h, w, _ = frame.shape
                index_tip = hand_landmarks.landmark[8]
                pinky_tip = hand_landmarks.landmark[20]
                ix, iy = int(index_tip.x * w), int(index_tip.y * h)
                px, py = int(pinky_tip.x * w), int(pinky_tip.y * h)

                # Rotation based on index finger position relative to center
                rotation_x = (iy - h/2) / (h/2) * 90
                rotation_y = (ix - w/2) / (w/2) * 90

                # Pinch to scale
                pinch_dist = distance((ix, iy), (px, py))
                if pinch_dist < 40:  # arbitrary threshold
                    scale = max(0.5, scale - 0.02)
                else:
                    scale = min(1.5, scale + 0.02)

            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
            glPushMatrix()
            glScalef(scale, scale, scale)
            glRotatef(rotation_x, 1, 0, 0)
            glRotatef(rotation_y, 0, 1, 0)
            draw_cube()
            glPopMatrix()

            pygame.display.flip()
            pygame.time.wait(10)
    finally:
        cap.release()
        pygame.quit()

if __name__ == "__main__":
    main()
