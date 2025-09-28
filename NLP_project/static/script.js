function appendMessage(text, sender) {
  const msg = document.createElement("div");
  msg.className = "msg " + sender;
  msg.textContent = text;
  document.getElementById("messages").appendChild(msg);
  document.getElementById("messages").scrollTop = document.getElementById("messages").scrollHeight;
}

function showTypingIndicator() {
  document.getElementById("typingIndicator").classList.add("active");
}

function hideTypingIndicator() {
  document.getElementById("typingIndicator").classList.remove("active");
}

function speak(text) {
  const synth = window.speechSynthesis;
  const utter = new SpeechSynthesisUtterance(text);
  utter.rate = 0.9;
  utter.pitch = 1;
  synth.speak(utter);
}

function sendMessage() {
  const input = document.getElementById("userInput");
  const message = input.value.trim();
  if (!message) return;

  appendMessage(message, "user");
  input.value = "";
  showTypingIndicator();

  fetch("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message })
  })
    .then(res => res.json())
    .then(data => {
      hideTypingIndicator();
      appendMessage(data.response, "bot");
      speak(data.response);
    })
    .catch(error => {
      hideTypingIndicator();
      appendMessage("Sorry, I encountered an error. Please try again.", "bot");
    });
}

function startVoiceInput() {
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  const voiceBtn = document.getElementById("voiceBtn");

  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.start();

  recognition.onstart = () => {
    voiceBtn.classList.add("listening");
    voiceBtn.innerHTML = '<span>🎙️</span> Listening...';
    console.log("🎙️ Listening...");
  };

  recognition.onend = () => {
    voiceBtn.classList.remove("listening");
    voiceBtn.innerHTML = '<span>🎤</span> Speak';
  };

  recognition.onerror = (event) => {
    voiceBtn.classList.remove("listening");
    voiceBtn.innerHTML = '<span>🎤</span> Speak';
    alert("Speech recognition error: " + event.error);
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById("userInput").value = transcript;
    sendMessage();
  };
}

// Handle "Enter" key
document.getElementById("userInput").addEventListener("keypress", function(event) {
  if (event.key === "Enter") {
    sendMessage();
  }
});

// Clear welcome message on first interaction
let firstInteraction = true;
const originalSendMessage = sendMessage;
sendMessage = function () {
  if (firstInteraction) {
    document.querySelector(".welcome-message").style.display = "none";
    firstInteraction = false;
  }
  originalSendMessage();
};
