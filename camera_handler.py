# camera_handler.py
import cv2
import mediapipe as mp
import math

class CameraHandler:
    def __init__(self):
        # Inicjalizacja kamery
        self.vid = cv2.VideoCapture(0)
        if not self.vid.isOpened():
            raise ValueError("Nie można otworzyć kamery!", 0)

        # Inicjalizacja MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        # Ustawiamy max_num_hands=1, aby uprościć logikę sterowania
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils

    def process_frame(self):
        """
        Przetwarza jedną klatkę z kamery, wykrywa gesty i zwraca dane.
        :return: Tuple (klatka_obrazu, nazwa_gestu, współrzędne_dłoni)
        """
        ret, frame = self.vid.read()
        if not ret:
            return None, "ERROR", None

        # Odbicie lustrzane i konwersja kolorów
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Przetwarzanie klatki przez MediaPipe
        results = self.hands.process(frame_rgb)

        gesture = "NO_HAND"
        hand_coords = None

        if results.multi_hand_landmarks:
            # Bierzemy pierwszą wykrytą dłoń
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Rysowanie punktów na dłoni dla wizualizacji
            self.mp_drawing.draw_landmarks(
                frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
            
            # Logika rozpoznawania gestów
            gesture = self._recognize_gesture(hand_landmarks)
            
            # Pobieranie współrzędnych do sterowania (użyjemy punktu 9 - podstawa środkowego palca)
            # Normalizowane współrzędne (0.0 do 1.0)
            if gesture == "OPEN_HAND":
                control_point = hand_landmarks.landmark[9]
                hand_coords = (control_point.x, control_point.y)

        return frame, gesture, hand_coords

    def _recognize_gesture(self, hand_landmarks):
        """Prosta logika do rozpoznawania gestów na podstawie pozycji palców."""
        # Pobieramy punkty charakterystyczne (tips - czubki, pips - środkowe stawy)
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        ring_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        pinky_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        
        index_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]
        middle_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
        ring_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_PIP]
        pinky_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_PIP]

        # Gest WSKAZYWANIA (index wyprostowany, reszta zgięta)
        if (index_tip.y < index_pip.y and
            middle_tip.y > middle_pip.y and
            ring_tip.y > ring_pip.y and
            pinky_tip.y > pinky_pip.y):
            return "POINTING"

        # Gest PIĘŚCI (wszystkie palce zgięte)
        if (index_tip.y > index_pip.y and
            middle_tip.y > middle_pip.y and
            ring_tip.y > ring_pip.y and
            pinky_tip.y > pinky_pip.y):
            return "FIST"

        # W przeciwnym wypadku zakładamy OTWARTĄ DŁOŃ
        return "OPEN_HAND"

    def release(self):
        """Zwalnia zasób kamery."""
        if self.vid.isOpened():
            self.vid.release()