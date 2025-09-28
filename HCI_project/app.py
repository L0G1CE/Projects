import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from sklearn.preprocessing import LabelEncoder
import pickle
from datetime import datetime
from flask import Flask, Response, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import uuid
import time
import shutil
import qrcode

app = Flask(__name__)
app.secret_key = 'face_attendance_secret_key'

DATASET_DIR = "faces"
os.makedirs(DATASET_DIR, exist_ok=True)

# -------------------- DATABASE SETUP --------------------
def init_db():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        face_encoding BLOB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS attendance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        log_type TEXT CHECK(log_type IN ('IN', 'OUT')),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    conn.commit()
    conn.close()

init_db()

# -------------------- FACE MODEL --------------------
def load_faces_from_dataset():
    faces_data = []
    labels = []
    for user_name in os.listdir(DATASET_DIR):
        user_dir = os.path.join(DATASET_DIR, user_name)
        if not os.path.isdir(user_dir):
            continue
        for img_file in os.listdir(user_dir):
            img_path = os.path.join(user_dir, img_file)
            image = cv2.imread(img_path)
            if image is None:
                continue
            image = cv2.resize(image, (224, 224))
            image = img_to_array(image)
            image = preprocess_input(image)
            faces_data.append(image)
            labels.append(user_name)
    return faces_data, labels

class FaceModel:
    def __init__(self):
        self.model = None
        self.le = None
        self.recognizer_ready = False
        self.setup_model()

    def setup_model(self):
        if os.path.exists('face_model.h5') and os.path.exists('label_encoder.pkl'):
            try:
                self.model = load_model('face_model.h5')
                self.le = pickle.loads(open('label_encoder.pkl', 'rb').read())
                self.recognizer_ready = True
            except:
                self.create_new_model()
        else:
            self.create_new_model()

    def create_new_model(self):
        base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
        self.model = Sequential([
            base_model,
            MaxPooling2D(),
            Flatten(),
            Dense(128, activation='relu'),
            Dropout(0.5),
            Dense(2, activation='softmax')
        ])
        self.model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        self.le = LabelEncoder()
        self.le.fit(['unknown', 'known'])
        self.recognizer_ready = False

    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml').detectMultiScale(gray, 1.1, 5)

    def recognize_face(self, face_img):
        if not self.recognizer_ready:
            return "unknown", 0
        face_img = cv2.resize(face_img, (224, 224))
        face_img = img_to_array(face_img)
        face_img = preprocess_input(face_img)
        face_img = np.expand_dims(face_img, axis=0)
        preds = self.model.predict(face_img)
        i = np.argmax(preds)
        return self.le.classes_[i], preds[0][i]

    def train_model(self, faces_data, labels):
        self.le.fit(list(set(labels)))
        encoded_labels = self.le.transform(labels)
        with open('label_encoder.pkl', 'wb') as f:
            f.write(pickle.dumps(self.le))
        base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
        self.model = Sequential([
            base_model,
            MaxPooling2D(),
            Flatten(),
            Dense(128, activation='relu'),
            Dropout(0.5),
            Dense(len(self.le.classes_), activation='softmax')
        ])
        self.model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        y = tf.keras.utils.to_categorical(encoded_labels, len(self.le.classes_))
        self.model.fit(np.array(faces_data), y, batch_size=32, epochs=5, verbose=1)
        self.model.save('face_model.h5')
        self.recognizer_ready = True

face_model = FaceModel()

def retrain_model_from_dataset():
    faces_data, labels = load_faces_from_dataset()
    print(f"[INFO] Loaded {len(faces_data)} training samples from dataset.")

    if faces_data and labels:
        try:
            face_model.train_model(faces_data, labels)
            print("[INFO] Model retrained successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to train model: {str(e)}")
    else:
        print("[WARN] No training data found. Resetting model.")
        for file in ['face_model.h5', 'label_encoder.pkl']:
            if os.path.exists(file):
                os.remove(file)
        face_model.recognizer_ready = False


# -------------------- ROUTES --------------------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/history')
def history():
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT a.id, u.name, a.log_type, a.timestamp FROM attendance_logs a JOIN users u ON a.user_id = u.id ORDER BY a.timestamp DESC")
    logs = c.fetchall()
    c.execute("SELECT id, name FROM users")
    users = c.fetchall()
    conn.close()
    return render_template('history.html', logs=logs, users=users)

@app.route('/profile')
def profile():
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()

    # Add derived flag: has_face_data = True if folder exists and has images
    enriched_users = []
    for user in users:
        user_dict = dict(user)
        folder = os.path.join("faces", user['name'])
        has_data = os.path.isdir(folder) and len(os.listdir(folder)) > 0
        user_dict['has_face_data'] = has_data
        enriched_users.append(user_dict)

    return render_template('profile.html', users=enriched_users)


@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/video_feed')
def video_feed():
    def generate_frames():
        camera = cv2.VideoCapture(0)
        while True:
            success, frame = camera.read()
            if not success:
                break
            faces = face_model.detect_faces(frame)
            for (x, y, w, h) in faces:
                face_img = frame[y:y+h, x:x+w]
                if face_model.recognizer_ready:
                    name, prob = face_model.recognize_face(face_img)
                    label = f"{name}: {prob:.2f}"
                    cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        camera.release()
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/register_user', methods=['POST'])
def register_user():
    name = request.form.get('name')
    email = request.form.get('email')
    role = request.form.get('role')

    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    try:
        c.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
        user_id = c.lastrowid
        conn.commit()
        conn.close()

        # ✅ Generate QR code to /scan
        qr = qrcode.make(f'http://localhost:5000/scan')  # Replace with your domain if deployed
        os.makedirs('static/qrcodes', exist_ok=True)
        qr.save(f'static/qrcodes/{user_id}.png')

        flash('User registered successfully. Now capturing face data...', 'success')
        return redirect(url_for('register_face_page', user_id=user_id))
    except sqlite3.IntegrityError:
        conn.close()
        flash('Email already exists', 'danger')
        return redirect(url_for('profile'))

@app.route('/register_face_page/<int:user_id>')
def register_face_page(user_id):
    return render_template('register_face.html', user_id=user_id)

@app.route('/process_face_registration/<int:user_id>', methods=['POST'])
def process_face_registration(user_id):
    success = register_face(user_id)
    if success:
        flash('Face registered successfully.', 'success')
    else:
        flash('Face registration failed.', 'danger')
    return redirect(url_for('profile'))

def register_face(user_id, frame_count=20):
    print(f"[INFO] Registering face for user ID: {user_id}")
    
    # Fetch user name
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()

    if not result:
        print("[ERROR] User not found in database.")
        return False

    user_name = result[0]
    user_folder = os.path.join(DATASET_DIR, user_name)
    os.makedirs(user_folder, exist_ok=True)

    # Open camera
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("[ERROR] Could not open webcam.")
        return False

    count = 0
    while count < frame_count:
        ret, frame = camera.read()
        if not ret:
            print("[ERROR] Failed to read frame.")
            break

        faces = face_model.detect_faces(frame)
        for (x, y, w, h) in faces:
            face_img = frame[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (224, 224))
            file_path = os.path.join(user_folder, f"{uuid.uuid4().hex}.jpg")
            cv2.imwrite(file_path, face_img)
            print(f"[INFO] Saved {file_path}")
            count += 1
            time.sleep(0.1)
            if count >= frame_count:
                break

    camera.release()

    if count == 0:
        print("[WARN] No images captured for training.")
        return False

    print("[INFO] Finished capturing. Starting model retraining...")

    # Load all faces again from dataset and retrain
    faces_data = []
    labels = []
    for user_name_dir in os.listdir(DATASET_DIR):
        folder_path = os.path.join(DATASET_DIR, user_name_dir)
        if not os.path.isdir(folder_path):
            continue
        for img_file in os.listdir(folder_path):
            img_path = os.path.join(folder_path, img_file)
            image = cv2.imread(img_path)
            if image is None:
                continue
            image = cv2.resize(image, (224, 224))
            image = img_to_array(image)
            image = preprocess_input(image)
            faces_data.append(image)
            labels.append(user_name)

    if faces_data and labels:
        face_model.train_model(faces_data, labels)
        print("[INFO] Model retrained successfully.")
    else:
        print("[WARN] No training data found during retraining.")

    print("[INFO] Registration complete.")
    return True



@app.route('/api/scan_face', methods=['POST'])
def scan_face():
    camera = cv2.VideoCapture(0)
    time.sleep(1)
    ret, frame = camera.read()
    camera.release()
    if not ret:
        return jsonify({'status': 'error', 'message': 'Could not capture frame'})
    faces = face_model.detect_faces(frame)
    for (x, y, w, h) in faces:
        face_img = frame[y:y+h, x:x+w]
        name, prob = face_model.recognize_face(face_img)
        if prob >= 0.85 and name != "unknown":
            conn = sqlite3.connect('attendance.db')
            c = conn.cursor()
            c.execute("SELECT id, name FROM users WHERE name = ?", (name,))
            user = c.fetchone()
            conn.close()
            if user:
                return jsonify({'user_id': user[0], 'name': user[1], 'status': 'recognized'})
    return jsonify({'status': 'unrecognized'})

@app.route('/log_attendance', methods=['POST'])
def log_attendance():
    user_id = request.form.get('user_id')
    log_type = request.form.get('log_type')
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("INSERT INTO attendance_logs (user_id, log_type) VALUES (?, ?)", (user_id, log_type))
    conn.commit()
    conn.close()
    flash(f'Attendance {log_type} logged.', 'success')
    return redirect(url_for('scan'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    if user:
        user_folder = os.path.join(DATASET_DIR, user[0])
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder)
    c.execute("DELETE FROM attendance_logs WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    retrain_model_from_dataset()
    flash("User deleted and model retrained.", "success")
    return redirect(url_for("profile"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
