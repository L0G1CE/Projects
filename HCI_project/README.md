# Human Computer Interaction Project – Face Recognition Attendance System

## 📌 Overview
This project is a **Human Computer Interaction (HCI) project** that implements an **attendance tracking system** using:
- **Face recognition** powered by a trained deep learning model (`face_model.h5`)
- **QR code scanning** for alternative login
- **SQLite database** (`attendance.db`) to store attendance logs
- **Flask web application** for the user interface

It demonstrates how HCI principles can be applied to create a seamless, secure, and user-friendly attendance system.

---

## 🚀 Features
- 👤 **Face Registration** – Users can register their face via the web interface.
- 📸 **Face Recognition Login** – Automatic attendance marking using facial recognition.
- 📝 **Attendance History** – View attendance logs in the dashboard.
- 📱 **QR Code Login** – Alternative login option for users via QR codes.
- 👨‍💻 **Profile Management** – User profiles linked with facial data.
- 🎨 **Modern UI** – Styled with `style.css` and HTML templates (`home.html`, `profile.html`, etc.).
- 📂 **Local Database** – Attendance records stored in `attendance.db`.

---

## 📂 Project Structure
```
HCI_project/
│── app.py                 # Main Flask application
│── attendance.db          # SQLite database
│── face_model.h5          # Trained face recognition model
│── label_encoder.pkl      # Encoded labels for faces
│── faces/                 # Stored face images of registered users
│   └── <username>/        # Individual user images
│── static/
│   ├── style.css          # Styling
│   └── qrcodes/           # Generated QR codes
│── templates/
│   ├── base.html
│   ├── home.html
│   ├── profile.html
│   ├── register_face.html
│   ├── scan.html
│   ├── history.html
│   └── support.html
```

---

## 🛠️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/HCI_project.git
cd HCI_project
```

### 2️⃣ Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

*(If you don’t have a `requirements.txt`, make sure to install Flask, TensorFlow, OpenCV, Pillow, and other required packages manually.)*

### 4️⃣ Run the Application
```bash
python app.py
```
- Open your browser and go to: **`http://127.0.0.1:5000`**

---

## 📸 Usage
1. **Register User** – Go to the *Register* page and upload face images.
2. **Login via Face Recognition** – Scan face using the webcam to mark attendance.
3. **Login via QR Code** – Use the QR code assigned to the user for attendance.
4. **View History** – Check attendance logs in the *History* page.

---

## ⚙️ Tech Stack
- **Backend:** Flask (Python)
- **Database:** SQLite
- **Machine Learning:** TensorFlow/Keras (`face_model.h5`)
- **Frontend:** HTML, CSS, Bootstrap
- **Additional:** OpenCV (face recognition), QR Code generator

---

## 📌 Future Enhancements
- 🔒 Improve face recognition accuracy with more training data
- ☁️ Migrate database to MySQL/PostgreSQL
- 🌐 Deploy on cloud (Heroku, AWS, etc.)
- 📊 Add analytics dashboard for attendance statistics

---

## 👨‍💻 Contributors
- Jericho Lampano (Project Lead, Developer)
- Paul Mandap (Project Planner, Developer)
- Jesse Rey Isidro (Project Designer, Developer)