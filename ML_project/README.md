# Machine Learning Project – Olist OTIF Delivery Prediction

## 📌 Overview
This project builds a **machine learning model** to predict **On-Time, In-Full (OTIF) deliveries** using the **Olist e-commerce dataset**. It includes:
- **Data preparation and feature engineering**
- **Model training (XGBoost)**
- **Pipeline saving with Joblib**
- **Flask web app** for deployment and prediction

The goal is to demonstrate how machine learning can be applied to improve logistics and supply chain management by predicting delivery reliability.

---

## 🚀 Features
- 🧹 **Data Preparation** – Combines and processes raw Olist datasets into structured training data.
- 📊 **Feature Engineering** – Extracts features relevant to OTIF performance.
- 🤖 **Model Training** – Trains an XGBoost model to classify/predict OTIF outcomes.
- 💾 **Saved Pipeline** – Exports trained pipeline (`otif_xgb_pipeline.joblib`).
- 🌐 **Flask App** – Simple web interface for making predictions with the trained model.

---

## 📂 Project Structure
```
ML_project/
│── app.py                        # Flask web application
│── build_olist_otif_dataset.py   # Prepares dataset from Olist raw data
│── olist_otif_dataset.csv        # Processed dataset for training/testing
│── otif_xgb_pipeline.joblib      # Trained ML pipeline (XGBoost model)
│── requirements.txt              # Dependencies
│── train_otif_xgb.py             # Training script for XGBoost model
│── archive/                      # Raw Olist datasets
│   ├── olist_customers_dataset.csv
│   ├── olist_geolocation_dataset.csv
│   ├── olist_orders_dataset.csv
│   ├── olist_order_items_dataset.csv
│   ├── olist_order_payments_dataset.csv
│   ├── olist_order_reviews_dataset.csv
│   ├── olist_products_dataset.csv
│   ├── olist_sellers_dataset.csv
│   └── product_category_name_translation.csv
```

---

## 🛠️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/ML_project.git
cd ML_project
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

---

## 📸 Usage

### Step 1: Build Dataset
```bash
python build_olist_otif_dataset.py
```
- Processes raw Olist data into `olist_otif_dataset.csv`.

### Step 2: Train the Model
```bash
python train_otif_xgb.py
```
- Trains an XGBoost model and saves it as `otif_xgb_pipeline.joblib`.

### Step 3: Run the Flask App
```bash
python app.py
```
- Opens a local server at `http://127.0.0.1:5000`
- Allows users to input delivery/order details for OTIF prediction.

---

## 🌐 Flask API Endpoints

### **`/` – Home**
- Displays the main interface for the prediction app.

### **`/predict` – Make Prediction**
- **Method:** POST
- **Description:** Takes user input (order features) and predicts whether the order will be **On-Time, In-Full (OTIF)**.
- **Request Example:**
```json
{
  "order_id": "abc123",
  "customer_id": "cust001",
  "seller_id": "seller045",
  "product_id": "prod010",
  "shipping_limit_date": "2025-09-28",
  "price": 100.5,
  "freight_value": 15.0,
  "order_item_count": 3,
  "payment_value": 115.5,
  "delivery_days": 7
}
```
- **Response Example:**
```json
{
  "prediction": "On-Time",
  "confidence": 0.92
}
```

---

## ⚙️ Tech Stack
- **Programming:** Python
- **ML Frameworks:** scikit-learn, XGBoost, Joblib
- **Web Framework:** Flask
- **Data Storage:** CSV (Olist dataset)

---

## 📊 Dataset
The project uses the **Olist e-commerce dataset** containing:
- Orders
- Customers
- Sellers
- Products
- Reviews
- Geolocation
- Payments

These are merged and cleaned to build the **OTIF prediction dataset**.

---

## 📌 Future Enhancements
- 🔮 Improve feature engineering (shipping times, delays, seasonal effects).
- 📈 Add evaluation metrics dashboards.
- ☁️ Deploy Flask app to cloud (Heroku, AWS, etc.).
- 🧑‍🤝‍🧑 Extend to real-world delivery datasets for broader generalization.

---

## 👨‍💻 Contributors
- Jericho Lampano (Developer, Data Scientist)

