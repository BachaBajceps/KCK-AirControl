
import cv2
import mediapipe as mp
def process_frame(img, hands, mp_draw, mp_hands):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Example: Get the tip of the index finger
            for id, lm in enumerate(hand_landmarks.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                if id == 8: # Index finger tip
                    cv2.circle(img, (cx, cy), 10, (255, 0, 255), cv2.FILLED)
                    cv2.putText(img, f'X: {cx}, Y: {cy}', (cx + 20, cy), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)
                    
                    # CUBE CONTROL LOGIC GOES HERE:
                    # In a desktop GUI, you would update the cube's position/rotation based on (cx, cy).
                    # This environment does not support 3D rendering or GUI display.
    return img, results
