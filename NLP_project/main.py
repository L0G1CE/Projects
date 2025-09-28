from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

app = Flask(__name__)

# Content filter
blocked_keywords = ["politics", "religion", "election", "god", "president", "vote"]

def is_blocked(user_input):
    return any(word.lower() in user_input.lower() for word in blocked_keywords)

def chat_with_openrouter(user_input):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "VoiceWebChatbot"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input}
        ]
    }

    response = requests.post(API_URL, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code}"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json.get("message")
    if is_blocked(user_input):
        return jsonify({"response": "⚠️ That topic is restricted."})

    reply = chat_with_openrouter(user_input)
    return jsonify({"response": reply})

if __name__ == "__main__":
    app.run(debug=True)
