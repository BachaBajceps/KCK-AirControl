'''
Moduł odpowiedzialny za obsługę kamery i rozpoznawanie gestów dłoni.
'''
import logging
import math
from dataclasses import dataclass
from typing import Final, NamedTuple, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmark

# Stałe dla uniknięcia "magicznych liczb"
NUM_FINGERS: Final[int] = 4

# Zwracany typ danych z NamedTuple dla czytelności
class CameraOutput(NamedTuple):
    frame: Optional[np.ndarray]
    gesture: str
    coords: Optional[Tuple[float, float]]


@dataclass
class CameraHandlerConfig:
    '''Klasa konfiguracyjna do łatwego dostosowywania parametrów detekcji.'''
    MIN_DETECTION_CONFIDENCE: float = 0.6
    MIN_TRACKING_CONFIDENCE: float = 0.5
    FINGER_STRAIGHT_ANGLE_THRESHOLD: float = 160.0
    FINGER_BENT_ANGLE_THRESHOLD: float = 100.0
    THUMB_STRAIGHT_ANGLE_THRESHOLD: float = 150.0

class CameraHandler:
    '''
    Ulepszona, niezawodna klasa do obsługi kamery i rozpoznawania gestów.
    '''

    def __init__(self, camera_index: int = 0) -> None:
        self.config = CameraHandlerConfig()
        self.vid = cv2.VideoCapture(camera_index)
        self.is_camera_available = self.vid.isOpened()

        if self.is_camera_available:
            # --- OPTYMALIZACJE DLA WYDAJNOŚCI I RESPONSYWNOŚCI ---
            # 1. Zmniejsz rozdzielczość, aby przyspieszyć MediaPipe
            self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            # 2. Zmniejsz bufor, aby zredukować opóźnienie
            self.vid.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            logging.info("Camera initialized with optimized settings (640x480, buffer=1).")
        else:
            logging.error("Failed to open camera.")
            return

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=self.config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=self.config.MIN_TRACKING_CONFIDENCE,
        )
        self.mp_drawing = mp.solutions.drawing_utils

    def _calculate_angle(self, p1: NormalizedLandmark, p2: NormalizedLandmark, p3: NormalizedLandmark) -> float:
        '''Oblicza kąt (w stopniach) między trzema punktami (p2 jest wierzchołkiem).'''
        a = np.array([p1.x, p1.y])
        b = np.array([p2.x, p2.y])
        c = np.array([p3.x, p3.y])

        ba = a - b
        bc = c - b

        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        # Zabezpieczenie przed błędami numerycznymi
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))

        return np.degrees(angle)

    def _get_finger_states(self, lm: list[NormalizedLandmark]) -> dict[str, str]:
        '''
        Analizuje landmarki i zwraca stan każdego palca ('straight', 'bent', 'unknown').
        '''
        states: dict[str, str] = {}
        
        # Kciuk (ma inną strukturę stawów)
        # Kąt: WRIST -> THUMB_MCP -> THUMB_TIP
        thumb_angle = self._calculate_angle(lm[0], lm[2], lm[4])
        if thumb_angle > self.config.THUMB_STRAIGHT_ANGLE_THRESHOLD:
            states['thumb'] = 'straight'
        else:
            states['thumb'] = 'bent'
            
        # Pozostałe cztery palce
        finger_indices = {
            'index': [5, 6, 8],   # MCP, PIP, TIP
            'middle': [9, 10, 12],
            'ring': [13, 14, 16],
            'pinky': [17, 18, 20]
        }
        
        for finger, indices in finger_indices.items():
            # Kąt w stawie PIP - kluczowy dla określenia zgięcia
            angle = self._calculate_angle(lm[indices[0]], lm[indices[1]], lm[indices[2]])
            if angle > self.config.FINGER_STRAIGHT_ANGLE_THRESHOLD:
                states[finger] = 'straight'
            elif angle < self.config.FINGER_BENT_ANGLE_THRESHOLD:
                states[finger] = 'bent'
            else:
                states[finger] = 'unknown' # Stan pośredni, aby unikać jittera
        
        return states

    def _recognize_gesture(self, hand_landmarks: mp.tasks.vision.HandLandmarkerResult) -> str:
        '''
        Rozpoznaje gest na podstawie stanów palców.
        Kolejność warunków jest ważna - od najbardziej specyficznych do ogólnych.
        '''
        lm = hand_landmarks.landmark
        states = self._get_finger_states(lm)
        
        # Liczba wyprostowanych palców (bez kciuka)
        straight_fingers = sum(1 for finger in ['index', 'middle', 'ring', 'pinky'] if states[finger] == 'straight')
        # Liczba zgiętych palców (bez kciuka)
        bent_fingers = sum(1 for finger in ['index', 'middle', 'ring', 'pinky'] if states[finger] == 'bent')

        # GEST: OTWARTA DŁOŃ (OPEN_HAND)
        if states['thumb'] == 'straight' and straight_fingers == NUM_FINGERS:
            return "OPEN_HAND"

        # GEST: WSKAZYWANIE (POINTING)
        if states['index'] == 'straight' and states['middle'] == 'bent' and states['ring'] == 'bent' and states['pinky'] == 'bent':
            return "POINTING"

        # GEST: ZWYCIĘSTWO (VICTORY)
        if states['index'] == 'straight' and states['middle'] == 'straight' and states['ring'] == 'bent' and states['pinky'] == 'bent':
            return "VICTORY"

        # GEST: KCIUK W GÓRĘ (THUMBS_UP)
        if states['thumb'] == 'straight' and bent_fingers == NUM_FINGERS:
            return "THUMBS_UP"

        # GEST: PIĘŚĆ (FIST)
        if bent_fingers == NUM_FINGERS:
            return "FIST"

        # Jeśli żaden z powyższych warunków nie jest spełniony.
        return "UNKNOWN"


    def process_frame(self) -> CameraOutput:
        '''Przetwarza klatkę i zwraca wynik jako obiekt CameraOutput.'''
        if not self.is_camera_available:
            return CameraOutput(frame=None, gesture='NO_CAMERA', coords=None)

        ret, frame = self.vid.read()
        if not ret:
            logging.warning("Could not read frame from camera.")
            return CameraOutput(frame=None, gesture='ERROR', coords=None)

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Poprawiamy wydajność, oznaczając klatkę jako niemodyfikowalną
        frame.flags.writeable = False
        results = self.hands.process(frame_rgb)
        frame.flags.writeable = True

        gesture = "NO_HAND"
        hand_coords = None

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            
            self.mp_drawing.draw_landmarks(
                frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
            )
            
            gesture = self._recognize_gesture(hand_landmarks)
            
            if gesture == "OPEN_HAND":
                # Nadgarstek (landmark 0) jest stabilnym punktem do sterowania
                control_point = hand_landmarks.landmark[0] 
                hand_coords = (control_point.x, control_point.y)

        return CameraOutput(frame=frame, gesture=gesture, coords=hand_coords)

    def release(self) -> None:
        '''Zwalnia zasób kamery.'''
        if self.is_camera_available and self.vid.isOpened():
            self.vid.release()
            logging.info("Camera resource released.")