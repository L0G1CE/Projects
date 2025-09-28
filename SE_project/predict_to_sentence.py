import cv2
import mediapipe as mp
import numpy as np
from tensorflow.keras.models import load_model
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Load gesture recognition model and label encoder
model = load_model("asl_dynamic_lstm.h5")
labels = np.load("label_encoder.npy")

# 🔁 Load your own fine-tuned T5 model
tokenizer = AutoTokenizer.from_pretrained("t5_finetuned_asl/final_model")  # Replace with your fine-tuned folder
t5 = AutoModelForSeq2SeqLM.from_pretrained("t5_finetuned_asl/final_model")

# MediaPipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

# Buffers
sequence = []
recognized_words = []
last_prediction = None
same_pred_counter = 0

# Sentence display
final_sentence = ""
sentence_timer = 0  # Countdown timer to display sentence for N frames

# Word order priority (helps grammar model)
preferred_order = ["i", "you", "my", "friend", "go", "school", "at", "12"]

cap = cv2.VideoCapture(0)

print("📸 ASL-to-Sentence is running...\nPress [ENTER] to generate sentence\nPress 'd' to delete last word\nPress 'q' to quit")

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            landmarks = []
            for lm in hand_landmarks.landmark:
                landmarks.extend([lm.x, lm.y, lm.z])
            sequence.append(landmarks)

            if len(sequence) > 30:
                sequence.pop(0)

            if len(sequence) == 30:
                input_data = np.array(sequence).reshape(1, 30, 63)
                prediction = model.predict(input_data, verbose=0)
                pred_index = np.argmax(prediction)
                pred_label = labels[pred_index]

                if pred_label == last_prediction:
                    same_pred_counter += 1
                else:
                    same_pred_counter = 0
                last_prediction = pred_label

                if same_pred_counter == 5:
                    if not recognized_words or pred_label != recognized_words[-1]:
                        recognized_words.append(pred_label)
                    same_pred_counter = 0

                cv2.putText(frame, f"Detected: {pred_label}", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    else:
        sequence = []

    # Draw live word buffer
    word_display = " ".join(recognized_words[-10:])
    cv2.putText(frame, f"Words: {word_display}", (10, 450),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # Draw final generated sentence
    if sentence_timer > 0:
        cv2.putText(frame, f"🧠 Sentence: {final_sentence}", (10, 410),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        sentence_timer -= 1

    # Key handling
    key = cv2.waitKey(1)

    if key == 13:  # Enter
        # 🔃 Reorder recognized words based on preferred order
        ordered_words = [w for w in preferred_order if w in recognized_words]

        input_text = "fix: " + " ".join(ordered_words)
        input_ids = tokenizer(input_text, return_tensors="pt").input_ids
        output = t5.generate(input_ids, max_length=50, num_beams=4, early_stopping=True)
        final_sentence = tokenizer.decode(output[0], skip_special_tokens=True)
        print("🧠 Generated Sentence:", final_sentence)

        recognized_words = []
        sentence_timer = 90  # show for ~3 seconds at 30 FPS

    elif key == ord('d'):  # Delete last word
        if recognized_words:
            print("⛔ Deleted:", recognized_words[-1])
            recognized_words.pop()

    elif key == ord('q'):
        break

    cv2.imshow("ASL Real-Time Sentence Generator", frame)

cap.release()
cv2.destroyAllWindows()
