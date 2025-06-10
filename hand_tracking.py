
"""Utilities for processing webcam frames with MediaPipe hands."""

from typing import Tuple

import cv2
import mediapipe as mp


INDEX_TIP_ID = 8
DRAW_COLOR = (255, 0, 255)


def process_frame(img, hands, mp_draw, mp_hands) -> Tuple[object, object]:
    """Process a single image frame and annotate detected hands.

    Parameters
    ----------
    img : numpy.ndarray
        BGR image frame captured from the webcam.
    hands : mediapipe.python.solutions.hands.Hands
        Configured MediaPipe Hands instance used for detection.
    mp_draw : mediapipe.python.solutions.drawing_utils
        Drawing utilities for rendering landmarks on the frame.
    mp_hands : mediapipe.python.solutions.hands
        Module containing connection information for drawing.

    Returns
    -------
    tuple
        A tuple containing the annotated image and the raw MediaPipe results.
    """

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    if results.multi_hand_landmarks:
        height, width = img.shape[:2]
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            for idx, lm in enumerate(hand_landmarks.landmark):
                cx, cy = int(lm.x * width), int(lm.y * height)
                if idx == INDEX_TIP_ID:  # Index finger tip
                    cv2.circle(img, (cx, cy), 10, DRAW_COLOR, cv2.FILLED)
                    cv2.putText(
                        img,
                        f"X: {cx}, Y: {cy}",
                        (cx + 20, cy),
                        cv2.FONT_HERSHEY_PLAIN,
                        2,
                        DRAW_COLOR,
                        2,
                    )

                    # CUBE CONTROL LOGIC GOES HERE:
                    # In a desktop GUI, you would update the cube's position/rotation
                    # based on (cx, cy). This environment does not support 3D
                    # rendering or GUI display.
    return img, results
