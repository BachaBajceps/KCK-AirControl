
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
                    # print(f"Index finger tip: ({cx}, {cy})") # Removed print for cleaner output during processing
                    # Here you would add logic to control the cube based on hand position/gestures
    return img, results

def main():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
    mp_draw = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0) # 0 for default webcam

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    while True:
        success, img = cap.read()
        if not success:
            print("Error: Could not read frame.")
            break

        img, results = process_frame(img, hands, mp_draw, mp_hands)
        
        cv2.imshow("Hand Tracking", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
