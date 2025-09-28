# NLP Project – Chatbot using OpenRouter API

## 📌 Overview
This project is a **Flask-based chatbot web application** that integrates with the **OpenRouter API** for natural language processing.  
It allows users to interact with an AI assistant through a simple web interface.  

The chatbot demonstrates how to combine **Flask**, **JavaScript frontend**, and **OpenRouter’s large language models** into a functional NLP application.

---

## 🚀 Features
- 💬 **Chatbot Interface** – Users can send and receive messages in real time.  
- 🔗 **OpenRouter API Integration** – Backend connects to OpenRouter to process user queries.  
- ⚙️ **Environment Config** – `.env` file stores API keys and configuration.  
- 🌐 **Web UI** – Clean interface built with `index.html`, styled via `style.css`, and enhanced with `script.js`.  
- 📦 **Requirements Managed** – via `requirements.txt`.  

---

## 📂 Project Structure
```
NLP_project/
│── main.py            # Flask application entrypoint (chatbot API integration)
│── requirements.txt   # Python dependencies
│── .env               # API keys and environment variables
│── static/
│   ├── script.js      # Handles AJAX calls for sending/receiving chatbot messages
│   └── style.css      # UI styling
│── templates/
│   └── index.html     # Chatbot frontend interface
```

---

## 🛠️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/NLP_project.git
cd NLP_project
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

### 4️⃣ Set Environment Variables
Create a `.env` file in the root directory with:
```
FLASK_ENV=development
SECRET_KEY=your-secret-key
OPENROUTER_API_KEY=your-openrouter-api-key
```

### 5️⃣ Run the Application
```bash
python main.py
```
Access the chatbot at: **`http://127.0.0.1:5000`**

---

## 📸 Usage
1. Open the chatbot interface in your browser.  
2. Type a message in the input box and hit **Send**.  
3. The chatbot forwards your message to the **OpenRouter API** and returns the AI’s response.  
4. Continue chatting in real time.  

---

## 📡 API Request/Response Example

### Request (Python `requests` example):
```python
import requests

headers = {
    "Authorization": "Bearer YOUR_OPENROUTER_API_KEY",
    "Content-Type": "application/json"
}

data = {
    "model": "openai/gpt-3.5-turbo",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]
}

response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
print(response.json())
```

### Response (JSON example):
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1699999999,
  "model": "openai/gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I'm doing great! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ]
}
```

This structure shows the assistant’s reply in `choices[0].message.content`.

---

## ⚙️ Tech Stack
- **Backend:** Flask (Python)  
- **API:** OpenRouter API (LLM-powered responses)  
- **Frontend:** HTML, CSS, JavaScript  
- **Config:** dotenv (`.env`)  

---

## 📌 Future Enhancements
- 🎤 Add **speech-to-text** (voice input) and **text-to-speech** (audio replies).  
- 🧠 Support multiple models or personalities (select which OpenRouter model to use).  
- 📱 Make the UI mobile-friendly.  
- ☁️ Deploy to Heroku, Render, or AWS for public use.  

---

## 👨‍💻 Contributors
- Jericho Lampano (Developer, Chatbot Integration)  
