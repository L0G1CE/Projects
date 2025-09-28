# Software Engineering Project – ASL Gesture Recognition & Translation System

## 📌 Overview
This project is a **Software Engineering capstone/research project** that develops an **American Sign Language (ASL) gesture recognition and translation system**.  

It combines:  
- **Dynamic gesture recognition** using an **LSTM model** trained on recorded ASL sequences.  
- **Natural language translation** using a **fine-tuned T5 model** to generate grammatically correct sentences from recognized gestures.  

The system serves as both:  
- A **research prototype** to explore multi-model ASL translation pipelines.  
- A **practical application** allowing end-users to record gestures, train models, and translate ASL into text.

---

## 🚀 Features
- 🎥 **Gesture Recording** – Capture ASL gesture sequences for dataset creation.  
- 🧠 **LSTM Training** – Train a recurrent neural network (`asl_dynamic_lstm.h5`) on recorded gesture sequences.  
- 📝 **LSTM Evaluation** – Assess accuracy and performance of gesture recognition (`lstm_evaluate.py`).  
- 🔤 **T5 Fine-Tuning** – Adapt a pre-trained T5 transformer for ASL-to-English translation (`fine_tune_t5.py`).  
- 📊 **T5 Evaluation** – Measure quality of generated translations (`t5_evaluate.py`).  
- 🔗 **Prediction Pipeline** – Convert recorded gestures → recognized tokens → natural sentences (`predict_to_sentence.py`).  
- 📂 **Pre-trained Models & Checkpoints** – Includes fine-tuned T5 model artifacts and checkpoints.  

---

## 📂 Project Structure
```
SE_project/
│── data/                       # Dataset folder (ASL recordings, sequences)
│── t5_finetuned_asl/           # Fine-tuned T5 model artifacts
│   ├── checkpoint-100/         # Saved model checkpoint
│   ├── final_model/            # Final trained T5 model
│   ├── runs/                   # Training logs/runs
│   ├── config / tokenizer / added_tokens ...  
│
│── asl_data.xlsx               # Processed ASL dataset
│── asl_dynamic_lstm.h5         # Trained LSTM model
│── label_encoder.npy           # Encoded labels for gestures
│
│── record_gesture_sequences.py # Capture gesture sequences
│── train_lstm.py               # Train LSTM on ASL data
│── lstm_evaluate.py            # Evaluate LSTM model
│── fine_tune_t5.py             # Fine-tune T5 for translation
│── t5_evaluate.py              # Evaluate T5 translation
│── predict_to_sentence.py      # End-to-end prediction pipeline
```

---

## 🛠️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/SE_project.git
cd SE_project
```

### 2️⃣ Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

*(If no `requirements.txt` is provided, you will need: `tensorflow/keras`, `torch`, `transformers`, `numpy`, `pandas`, `scikit-learn`, `opencv-python`, `matplotlib`, etc.)*

---

## 📸 Usage Workflow

### Step 1: Record Gestures
```bash
python record_gesture_sequences.py
```
- Collect gesture sequences for training (saved in `data/`).

### Step 2: Train the LSTM
```bash
python train_lstm.py
```
- Trains the LSTM model (`asl_dynamic_lstm.h5`).

### Step 3: Evaluate the LSTM
```bash
python lstm_evaluate.py
```
- Tests accuracy of gesture recognition.

### Step 4: Fine-Tune T5
```bash
python fine_tune_t5.py
```
- Fine-tunes a pre-trained T5 model on recognized ASL sequences for translation.

### Step 5: Evaluate T5
```bash
python t5_evaluate.py
```
- Measures translation performance (BLEU, ROUGE, etc.).

### Step 6: Predict Sentences
```bash
python predict_to_sentence.py
```
- Runs the end-to-end pipeline:  
  **ASL gesture → LSTM recognition → T5 translation → English sentence.**

---

## ⚙️ Tech Stack
- **Deep Learning:** TensorFlow/Keras (LSTM), PyTorch + Hugging Face Transformers (T5).  
- **Data Handling:** NumPy, Pandas.  
- **Visualization:** Matplotlib.  
- **Preprocessing:** OpenCV (gesture recording).  

---

## 📌 Future Enhancements
- 🎤 Add real-time **webcam-based recognition** (continuous ASL to text).  
- 🔊 Integrate **text-to-speech** for voice output.  
- 📱 Deploy as a **mobile app** (using TensorFlow Lite or ONNX).  
- ☁️ Cloud-based training + hosting for scalability.  

---

## 👨‍💻 Contributors
- Jericho Lampano (Lead Developer, Researcher)  
- Jesse Rey Isidro (Model Trainer, researcher)
- John Lloyd Apawan (Model Evaluator, researcher)
- John Paul Caya (Data Gatherer, researcher)