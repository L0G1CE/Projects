import os
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping

# Load data
DATA_PATH = "data"
sequences, labels = [], []

for gesture in os.listdir(DATA_PATH):
    gesture_path = os.path.join(DATA_PATH, gesture)
    if not os.path.isdir(gesture_path): continue
    for file in os.listdir(gesture_path):
        sequence = np.load(os.path.join(gesture_path, file))
        sequences.append(sequence)
        labels.append(gesture)

X = np.array(sequences)
y = np.array(labels)

# Normalize (optional)
# X = np.array([seq - np.mean(seq, axis=0) for seq in X])

# Encode labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)
y_cat = to_categorical(y_encoded)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y_cat, test_size=0.3, random_state=42)

# Build LSTM model
model = Sequential()
model.add(LSTM(64, return_sequences=True, input_shape=(30, 63)))
model.add(Dropout(0.4))
model.add(LSTM(64))
model.add(Dropout(0.4))
model.add(Dense(64, activation='relu'))
model.add(Dense(y_cat.shape[1], activation='softmax'))

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Callbacks
checkpoint = ModelCheckpoint("asl_dynamic_lstm.h5", save_best_only=True, monitor='val_accuracy', mode='max')
early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

# Train
history = model.fit(
    X_train, y_train,
    epochs=50,
    validation_data=(X_test, y_test),
    callbacks=[checkpoint, early_stop]
)

# Save encoder
np.save("label_encoder.npy", label_encoder.classes_)
print("✅ Training complete. Model and labels saved.")
