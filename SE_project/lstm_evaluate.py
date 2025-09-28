import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import to_categorical

# Load model
model = load_model("asl_dynamic_lstm.h5")
labels = np.load("label_encoder.npy")

# Load dataset
DATA_PATH = "data"
sequences, y_labels = [], []

for gesture in os.listdir(DATA_PATH):
    for file in os.listdir(os.path.join(DATA_PATH, gesture)):
        sequences.append(np.load(os.path.join(DATA_PATH, gesture, file)))
        y_labels.append(gesture)

X = np.array(sequences)
y_true = np.array(y_labels)

# Encode
le = LabelEncoder()
y_encoded = le.fit_transform(y_true)
y_cat = to_categorical(y_encoded)

# Predict
y_pred_probs = model.predict(X)
y_pred = np.argmax(y_pred_probs, axis=1)
y_true = np.argmax(y_cat, axis=1)

# Accuracy
accuracy = accuracy_score(y_true, y_pred)
print("🎯 Accuracy:", round(accuracy * 100, 2), "%")

# Classification Report
report = classification_report(y_true, y_pred, target_names=le.classes_)
print(report)

# Save to CSV
report_df = pd.DataFrame(classification_report(y_true, y_pred, target_names=le.classes_, output_dict=True)).transpose()
report_df["overall_accuracy"] = accuracy
report_df.to_csv("gesture_classification_report.csv")

# Confusion Matrix
cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', xticklabels=le.classes_, yticklabels=le.classes_, cmap='Blues')
plt.title("Confusion Matrix (Gesture Recognition)")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.tight_layout()
plt.savefig("confusion_matrix.png")
plt.show()