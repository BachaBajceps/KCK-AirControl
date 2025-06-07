
import unittest
import cv2
import mediapipe as mp
import numpy as np
from unittest.mock import MagicMock, patch
from hand_tracking import process_frame

class TestHandTracking(unittest.TestCase):

    @patch('cv2.cvtColor')
    @patch('mediapipe.solutions.hands.Hands')
    def test_process_frame_no_hands(self, mock_hands_class, mock_cvtColor):
        # Mock cv2.cvtColor to return a dummy RGB image
        mock_cvtColor.return_value = np.zeros((480, 640, 3), dtype=np.uint8)

        # Mock mediapipe.solutions.hands.Hands instance
        mock_hands_instance = MagicMock()
        mock_hands_class.return_value = mock_hands_instance

        # Mock the process method to return no hand landmarks
        mock_hands_instance.process.return_value = MagicMock(multi_hand_landmarks=None)

        # Mock mp_draw and mp_hands (though not strictly needed for this no-hands case)
        mock_mp_draw = MagicMock()
        mock_mp_hands = MagicMock()

        # Create a dummy image
        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)

        # Call the function
        processed_img, results = process_frame(dummy_img, mock_hands_instance, mock_mp_draw, mock_mp_hands)

        # Assertions
        mock_cvtColor.assert_called_once()
        mock_hands_instance.process.assert_called_once()
        self.assertIsNone(results.multi_hand_landmarks)
        self.assertTrue(np.array_equal(processed_img, dummy_img)) # Image should be unchanged if no hands

    @patch('cv2.cvtColor')
    @patch('cv2.circle')
    @patch('mediapipe.solutions.hands.Hands')
    @patch('mediapipe.solutions.drawing_utils') # Patch the module itself
    def test_process_frame_with_hands(self, mock_mp_draw_module, mock_hands_class, mock_circle, mock_cvtColor):
        # Mock cv2.cvtColor to return a dummy RGB image
        mock_cvtColor.return_value = np.zeros((480, 640, 3), dtype=np.uint8)

        # Mock mediapipe.solutions.hands.Hands instance
        mock_hands_instance = MagicMock()
        mock_hands_class.return_value = mock_hands_instance

        # Create a mock hand landmark object
        mock_landmark = MagicMock()
        mock_landmark.x = 0.5
        mock_landmark.y = 0.5
        
        # Create a mock hand_landmarks object with a list of landmarks
        mock_hand_landmarks = MagicMock()
        mock_hand_landmarks.landmark = [MagicMock() for _ in range(21)] # 21 landmarks for a hand
        mock_hand_landmarks.landmark[8] = mock_landmark # Set index finger tip

        # Mock the process method to return hand landmarks
        mock_results = MagicMock()
        mock_results.multi_hand_landmarks = [mock_hand_landmarks]
        mock_hands_instance.process.return_value = mock_results

        # Mock mp_hands
        mock_mp_hands = MagicMock()
        mock_mp_hands.HAND_CONNECTIONS = "dummy_connections"

        # Create a dummy image
        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)

        # Call the function, passing mock_mp_draw_module as the mp_draw argument
        processed_img, results = process_frame(dummy_img, mock_hands_instance, mock_mp_draw_module, mock_mp_hands)

        # Assertions
        mock_cvtColor.assert_called_once()
        mock_hands_instance.process.assert_called_once()
        mock_mp_draw_module.draw_landmarks.assert_called_once_with(dummy_img, mock_hand_landmarks, "dummy_connections")
        mock_circle.assert_called_once() # Should be called for index finger tip
        self.assertIsNotNone(results.multi_hand_landmarks)
        self.assertTrue(np.array_equal(processed_img, dummy_img)) # Image should be modified in place, but content is mocked

if __name__ == '__main__':
    unittest.main()
