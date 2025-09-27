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
let score = 0;
let timeLeft = 60;
let level = "Easy";
let history = [];
let timerInterval = null;
let gameStarted = false;

const scrambleWorker = new Worker("worker.js");
const user = localStorage.getItem("spellraceUser") || "Guest";
const roomId = localStorage.getItem("matchmakingRoom") || "defaultRoom";

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
const restartContainer = document.getElementById("restart-container");

// ======== Firebase: Room & Leaderboard ========
function joinRoom() {
  const playerRef = firebase.database().ref(`lobbies/${roomId}/players/${user}`);
  playerRef.set({ score: 0 });
  playerRef.onDisconnect().remove();

  firebase.database().ref(`lobbies/${roomId}/ready/${user}`).onDisconnect().remove();

  firebase.database().ref(`lobbies/${roomId}/players`).on("value", (snapshot) => {
    const playersList = document.getElementById("players-list");
    if (!playersList) return;

    const playersArray = [];
    snapshot.forEach((child) => {
      playersArray.push({
        name: child.key,
        score: child.val().score || 0
      });
    });

    playersArray.sort((a, b) => b.score - a.score);
    playersList.innerHTML = "";

    playersArray.forEach(player => {
      const li = document.createElement("li");
      li.textContent = `${player.name}: ${player.score} pts`;
      playersList.appendChild(li);
    });
  });
}

function updatePlayerScore() {
  firebase.database().ref(`lobbies/${roomId}/players/${user}/score`).set(score);
}

// ======== Word Handling ========
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
  updatePlayerScore();
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

// ======== Game End ========
function endGame() {
  scrambledWordEl.textContent = "⏱️ Time's Up!";
  userInput.disabled = true;
  document.querySelector("#answer-form button").disabled = true;

  const result = `Score: ${score}, Level reached: ${level}`;
  history.push(result);
  updateHistory();

  localStorage.setItem("finalScore", score);

  // Show countdown
  let countdown = 15;
  const roomStatus = document.createElement("p");
  roomStatus.id = "room-status";
  roomStatus.style.marginTop = "20px";
  roomStatus.style.fontSize = "1.1rem";
  roomStatus.style.fontWeight = "bold";
  roomStatus.textContent = `Returning to matchmaking in ${countdown} seconds...`;
  document.querySelector("main").appendChild(roomStatus);

  const interval = setInterval(() => {
    countdown--;
    roomStatus.textContent = `Returning to matchmaking in ${countdown} seconds...`;

    if (countdown <= 0) {
      clearInterval(interval);

      // Reset room status so others don’t get auto-redirected
      firebase.database().ref(`lobbies/${roomId}/status`).set("waiting");

      // Clean up user entry
      firebase.database().ref(`lobbies/${roomId}/players/${user}`).remove();
      firebase.database().ref(`lobbies/${roomId}/ready/${user}`).remove();

      window.location.href = "matchmaking.html";
    }
  }, 1000);
}



// ======== History Update ========
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
  console.log("✅ Multiplayer initGame() triggered!");

  // Reset game state
  score = 0;
  timeLeft = 60;
  level = "Easy";
  gameStarted = true;

  scoreEl.textContent = score;
  levelEl.textContent = level;
  timerEl.textContent = timeLeft;
  userInput.disabled = false;
  userInput.value = "";
  document.querySelector("#answer-form button").disabled = false;
  userInput.focus();

  unusedWords = {
    Easy: [...wordBank.Easy],
    Medium: [...wordBank.Medium],
    Hard: [...wordBank.Hard]
  };

  joinRoom();
  updateScrambledWord();
  clearInterval(timerInterval);
  startTimer();
}

// ======== Button Actions ========
function markReady() {
  firebase.database().ref(`lobbies/${roomId}/ready/${user}`).set(true);
  document.getElementById("ready-btn").disabled = true;
}

function goToLobby() {
  firebase.database().ref(`lobbies/${roomId}/players/${user}`).remove();
  firebase.database().ref(`lobbies/${roomId}/ready/${user}`).remove();
  window.location.href = "lobby.html";
}

function goBackToLogin() {
  window.location.href = "login.html";
}

// ======== On Load ========
window.onload = () => {
  const savedUser = localStorage.getItem("spellraceUser");
  if (!savedUser) {
    window.location.href = "login.html";
    return;
  }

  if (!gameStarted) {
    initGame();
  }
};
