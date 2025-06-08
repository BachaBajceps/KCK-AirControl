
import cv2
import mediapipe as mp
import requests # Import requests library

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
                    
                    # Send hand data to Flask server
                    try:
                        requests.post('http://localhost:53102/hand_data', json={'x': cx, 'y': cy})
                    except requests.exceptions.ConnectionError as e:
                        print(f"Could not connect to Flask server: {e}. Make sure app.py is running.")
                    
                    # CUBE CONTROL LOGIC GOES HERE:
                    # On your local machine, you would integrate a 3D rendering library (e.g., OpenGL, Pygame with 3D capabilities, or a dedicated game engine)
                    # to draw and manipulate a cube based on the hand landmark coordinates (cx, cy) or other hand gestures.
                    # This environment does not support 3D rendering or multiple display windows.
    return img, results

def main():
    # For CPU optimization:
    # 1. Consider reducing the webcam resolution if performance is critical and lower resolution is acceptable.
    #    Example: cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    #             cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    # 2. The 'min_detection_confidence' and 'min_tracking_confidence' are already set to 0.7,
    #    which is a common balance. Adjusting these might have minor impact.
    # 3. If MediaPipe offers a 'lite' model for hands, you might explore that option,
    #    though it's not directly exposed as a simple parameter here.
    # 4. Minimize drawing operations if they become a bottleneck.

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
