# Parallel and Distributed Computing Project – Multiplayer Game Platform

## 📌 Overview
This project is a **Parallel and Distributed Computing (PAD)** showcase implemented as a **web‑based multiplayer game platform**. It demonstrates:
- **Parallelism in the browser** via **Web Workers** (`worker.js`) to keep the UI responsive while heavy logic runs off the main thread.
- **Distributed, real‑time coordination** using **Firebase** (for auth + hosting + real‑time state).
- **Multi‑user orchestration** patterns: **login → lobby → matchmaking → multiplayer room**.

> This README explains the architecture, setup, and (by request) a **step‑by‑step sequence of how the lobby & matchmaking** operate across pages and scripts.

---

## 🚀 Features
- 🏠 **Lobby system** — browse or create rooms, see who’s online.
- 🔄 **Matchmaking** — auto‑pairing/queueing logic that funnels players into a shared room.
- 🎮 **Single‑player and multiplayer** pages to test both modes.
- ⚡ **Web Worker parallelism** — compute‑heavy tasks done in `worker.js` so animations/inputs stay smooth.
- ☁️ **Firebase integration** — auth + hosting + realtime sync (room entries, player status, etc.).

---

## 📂 Project Structure
```
PAD_project/
│── .firebaserc                  # Firebase config
│── .gitignore
│── firebase.json                # Firebase Hosting settings
│── index.html                   # Landing page
│── login.html                   # Sign in / identify player
│── lobby.html                   # Room list / create / join
│── matchmaking.html             # Auto-match flow (queue)
│── multiplayer.html             # In-room multiplayer view
│── start.html                   # Single-player entry
│── startmultiplayer.html        # Alt entry to multiplayer
│── script.js                    # Core game logic (single)
│── scriptmultiplayer.js         # Multiplayer logic (client)
│── worker.js                    # Web Worker for parallel tasks
│── style.css                    # Styles
│── assets/
│   └── images/
│       └── AWS_logo.jpg
```

---

## 🛠️ Setup & Deployment

### 1) Clone
```bash
git clone https://github.com/your-username/PAD_project.git
cd PAD_project
```

### 2) Install Firebase CLI
```bash
npm install -g firebase-tools
firebase login
```

### 3) Initialize & Deploy
> If this is a new Firebase project, run:
```bash
firebase init
```
Make sure **Hosting** is enabled and `public` directory matches your setup (commonly `.`).  
To deploy:
```bash
firebase deploy
```

> Optional (Local Dev): You can use **Firebase Emulators** for Auth/Firestore/RTDB to iterate locally.

---

## 🧭 Pages & Scripts — End‑to‑End Flow

### 0) Landing (`index.html`)
- Provides entry points to **Login**, **Single‑player**, and **Multiplayer** flows.

### 1) Login (`login.html`)
- Initializes/requests auth (e.g., anonymous or provider‑based).
- On success, navigates to **`lobby.html`** with a known `playerId` / profile (stored in memory or browser storage).

### 2) Lobby (`lobby.html`)
**Purpose:** Discoverability and manual control.
- Shows **rooms list** (available / in‑progress), and a **Create Room** action.
- **Join Room**: if capacity allows, moves the player into that room and navigates to **`multiplayer.html`**.
- **Create Room**: writes a new room doc (or RTDB node) with metadata:
  - `roomId`, `status` (`open|matching|in_game`), `players` array, `capacity`, timestamps.
- **Leave Lobby**: logs user offline or detaches presence handlers.

**Concurrency Notes:**
- Use transactional writes or security rules to prevent **over‑join** when two players click at once.
- Track **presence** (onDisconnect cleanup) so abandoned rooms don’t linger as “full”.

### 3) Matchmaking (`matchmaking.html`)
**Purpose:** Automatic pairing / queue.
- Player enters a **queue** collection/node (e.g., `{ playerId, queuedAt }`).
- A **matcher** (client‑side or via Cloud Function) tries to **pair players** in FIFO order:
  1. Take two waiting players.
  2. Create a **room** with both as members.
  3. Update queue entries to `matched` and store `roomId`.
  4. Redirect both clients to **`multiplayer.html?roomId=...`**.

**Race Conditions & Handling:**
- Use **atomic updates** (e.g., RTDB `transaction` or Firestore `runTransaction`) when claiming players from the queue.
- If a player disconnects mid‑queue, remove their queue entry with presence listeners.

### 4) Multiplayer (`multiplayer.html` + `scriptmultiplayer.js`)
**Purpose:** The synchronized game room.
- **Subscribe** to room state updates (players, positions, scores, phase).
- **Publish** local inputs or actions (debounced or at tick rate).
- **Lockstep or Client‑Auth Hybrid:** If using lockstep, each tick:
  - Collect inputs from all players.
  - Advance deterministic state (ideally inside the Worker).
  - Emit the new authoritative snapshot.
- **Reconciliation:** If using client‑predicted movement, reconcile on snapshot arrival.

**Parallelism with `worker.js`:**
- Offload **simulation steps, pathfinding, A* computations, large loops, or physics** to the Worker:
  ```js
  // main thread
  const worker = new Worker('worker.js');
  worker.postMessage({ type: 'TICK', payload: currentInputs });
  worker.onmessage = (e) => {
    const { nextState } = e.data;
    render(nextState);
  };
  ```
- Keep the **main thread** for **DOM rendering, input, animations**.

### 5) Single‑player (`start.html` + `script.js`)
- Runs the same core game logic **locally** (optionally still using the Worker for heavy computation).
- Useful for debugging gameplay independent of networking.

---

## 🗃️ Suggested Data Model (Firestore/RTDB)
> Adapt names/structure to your implementation.

**Rooms**
```json
rooms/{roomId} : {
  "status": "open | matching | in_game | finished",
  "capacity": 2,
  "players": [
    {"id": "p1", "name": "Alice", "ready": true},
    {"id": "p2", "name": "Bob", "ready": false}
  ],
  "createdAt": 1690000000,
  "updatedAt": 1690000300,
  "state": { "tick": 420, "scores": {"p1": 10, "p2": 12} }
}
```

**Queue**
```json
queue/{playerId} : {
  "queuedAt": 1690000123,
  "status": "waiting | matched | cancelled",
  "roomId": "abc123"  // set when matched
}
```

**Presence**
```json
presence/{playerId} : {
  "online": true,
  "lastSeen": 1690000456
}
```

---

## 🔐 Security & Fair‑Play
- **Rules**: Restrict writes to a player’s own profile/inputs; validate room capacity & membership.
- **Server Authority**: For competitive modes, consider moving **authoritative state** to Cloud Functions or a trusted server to prevent cheating.
- **Rate Limiting**: Throttle client updates to protect bandwidth and avoid flooding.

---

## ⚙️ Tech Stack
- **Frontend**: HTML, CSS, JavaScript
- **Parallelism**: Web Workers
- **Backend**: Firebase (Auth, Hosting, Realtime DB/Firestore)
- **Deployment**: Firebase Hosting

---

## 📌 Future Enhancements
- WebRTC for **peer‑to‑peer** low‑latency data channels.
- **Spectator mode** and **replays**.
- **Leaderboards** and season resets.
- **Cloud Functions** as authoritative matchmaker.

---

## 👨‍💻 Contributors
- Jericho Lampano (Lead Developer, Cloud Integrator)  
- Jesse Rey Isidro (Fontend Developer)
- Alexis J.V Magno (Backend Developer)
- John Paul Caya (Project Architect)