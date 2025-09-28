import cv2
import mediapipe as mp
import numpy as np
import os
import time

GESTURE_LABEL = "12"  # Change this for each gesture
SAVE_PATH = f"data/{GESTURE_LABEL}"
os.makedirs(SAVE_PATH, exist_ok=True)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
sequence = []
recording = False
countdown_start_time = None
sample_count = 0
COUNTDOWN_SECONDS = 3

print("🎥 Press 's' to start 30-frame recording after a countdown. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    # Draw hand landmarks
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            if recording:
                landmarks = []
                for lm in hand_landmarks.landmark:
                    landmarks.extend([lm.x, lm.y, lm.z])
                sequence.append(landmarks)
                cv2.putText(frame, f"Recording frame {len(sequence)}/30", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                if len(sequence) == 30:
                    np.save(f"{SAVE_PATH}/sample_{sample_count}.npy", np.array(sequence))
                    print(f"✅ Saved: sample_{sample_count}")
                    sample_count += 1
                    sequence = []
                    recording = False

    else:
        if recording:
            cv2.putText(frame, "⚠️ Hand not detected. Cancelling...", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            print("⚠️ Hand lost — resetting.")
            sequence = []
            recording = False

    # Countdown logic
    if countdown_start_time is not None:
        elapsed = time.time() - countdown_start_time
        remaining = COUNTDOWN_SECONDS - int(elapsed)

        if remaining > 0:
            cv2.putText(frame, f"Starting in {remaining}", (200, 250),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)
        else:
            print("▶️ Recording started.")
            recording = True
            sequence = []
            countdown_start_time = None

    # Keypress handling
    key = cv2.waitKey(1)
    if key == ord('s') and countdown_start_time is None and not recording:
        print("⏳ Countdown started...")
        countdown_start_time = time.time()

    elif key == ord('q'):
        break

    cv2.imshow("Gesture Recorder (w/ Countdown)", frame)

cap.release()
cv2.destroyAllWindows()
