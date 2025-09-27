// worker.js
self.onmessage = function (e) {
  const word = e.data;
  let shuffled = word;
  const arr = word.split("");

  while (shuffled === word) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    shuffled = arr.join("");
  }

  self.postMessage(shuffled);
};
