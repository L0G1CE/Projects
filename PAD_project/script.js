// ======== Word Bank ========
const wordBank = {
  Easy: [
    "cloud", "data", "aws", "app", "file", "save", "store", "login", "user", "web",
    "wifi", "server", "code", "plan", "tool"
  ],
  Medium: [
    "service", "account", "backup", "online", "access", "network", "secure", "upload", "system", "browser",
    "billing", "region", "support", "control", "dashboard"
  ],
  Hard: [
    "virtualization", "deployment", "authentication", "subscription", "configuration", "integration",
    "availability", "infrastructure", "monitoring", "optimization", "encryption", "permission", "automation", "scalability"
  ]
};


// ======== Game State ========
let currentWord = "";
let scrambledWord = "";
let scrambleWorker = new Worker("worker.js");
let score = 0;
let timeLeft = 60;
let level = "Easy";
let history = [];
let timerInterval = null;
let gameStarted = false;

const user = localStorage.getItem("spellraceUser") || "Guest";

let unusedWords = {
  Easy: [],
  Medium: [],
  Hard: []
};

// ======== DOM Elements ========
const scrambledWordEl = document.getElementById("scrambled-word");
const userInput = document.getElementById("user-input");
const timerEl = document.getElementById("timer");
const scoreEl = document.getElementById("score");
const levelEl = document.getElementById("level");
const feedbackEl = document.getElementById("feedback");
const historyList = document.getElementById("history-list");
const restartBtn = document.getElementById("restart-button");
const restartContainer = document.getElementById("restart-container");

// ======== Word Logic ========
function shuffleWithWorker(word, callback) {
  scrambleWorker.postMessage(word);
  scrambleWorker.onmessage = function (e) {
    callback(e.data);
  };
}

function getRandomWord(difficulty) {
  const words = unusedWords[difficulty];
  if (words.length === 0) return null;
  const index = Math.floor(Math.random() * words.length);
  return words.splice(index, 1)[0];
}

function updateScrambledWord() {
  currentWord = getRandomWord(level);
  if (!currentWord) {
    scrambledWordEl.textContent = "✅ All words completed!";
    endGame();
    return;
  }

  shuffleWithWorker(currentWord, (shuffled) => {
    scrambledWord = shuffled;
    scrambledWordEl.textContent = scrambledWord;
  });
}

// ======== Timer ========
function startTimer() {
  timerEl.textContent = timeLeft;
  timerInterval = setInterval(() => {
    timeLeft--;
    timerEl.textContent = timeLeft;
    if (timeLeft <= 0) {
      clearInterval(timerInterval);
      endGame();
    }
  }, 1000);
}

// ======== Score & Level ========
function updateScore() {
  score += 10;
  scoreEl.textContent = score;

  if (score >= 100) level = "Hard";
  else if (score >= 50) level = "Medium";
  else level = "Easy";

  levelEl.textContent = level;
}

// ======== Answer Handling ========
document.getElementById("answer-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const guess = userInput.value.trim().toLowerCase();
  userInput.value = "";

  if (guess === currentWord.toLowerCase()) {
    feedbackEl.textContent = "✅ Correct!";
    updateScore();
    updateScrambledWord();
  } else {
    feedbackEl.textContent = "❌ Incorrect!";
  }

  setTimeout(() => {
    feedbackEl.textContent = "";
  }, 1500);
});

// ======== End Game ========
function endGame() {
  scrambledWordEl.textContent = "⏱️ Time's Up!";
  userInput.disabled = true;
  document.querySelector("#answer-form button").disabled = true;

  const result = `Score: ${score}, Level reached: ${level}`;
  history.push(result);
  updateHistory();

  restartContainer.style.display = "block";
}

// ======== Restart Game ========
restartBtn.addEventListener("click", () => {
  restartContainer.style.display = "none";
  initGame();
  userInput.focus();
});

// ======== History Tracker ========
function updateHistory() {
  historyList.innerHTML = "";
  history.slice(-5).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    historyList.appendChild(li);
  });
}

// ======== Game Initialization ========
function initGame() {
  score = 0;
  timeLeft = 60;
  level = "Easy";
  scoreEl.textContent = score;
  levelEl.textContent = level;
  timerEl.textContent = timeLeft;
  userInput.disabled = false;
  userInput.value = "";
  document.querySelector("#answer-form button").disabled = false;

  unusedWords = {
    Easy: [...wordBank.Easy],
    Medium: [...wordBank.Medium],
    Hard: [...wordBank.Hard]
  };

  updateScrambledWord();
  clearInterval(timerInterval);
  startTimer();
  userInput.focus();
}

// ======== On Load ========
window.onload = () => {
  const savedUser = localStorage.getItem("spellraceUser");
  if (!savedUser) {
    window.location.href = "login.html";
  } else {
    initGame();
    if (gameStarted) return;
    gameStarted = true;
  }
};

// ======== Back to Lobby ========
function goBackToLobby() {
  window.location.href = "lobby.html";
}
