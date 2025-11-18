const sendBtn = document.getElementById('send-btn');
const userInput = document.getElementById('user-input');
const chatBox = document.getElementById('chat-box');

// ---------------- SAVE MESSAGE ----------------
function addMessage(text, sender, save = true) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add(sender === "user" ? "user-message" : "bot-message");
  messageDiv.textContent = text;

  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;

  if (save) {
    const history = JSON.parse(localStorage.getItem("cu_chat_history")) || [];
    history.push({ text, sender });
    localStorage.setItem("cu_chat_history", JSON.stringify(history));
  }
}

// ---------------- SEND MESSAGE ----------------
sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});

function sendMessage() {
  const message = userInput.value.trim();
  if (message === "") return;

  addMessage(message, "user");
  userInput.value = "";

  // show typing indicator
  document.getElementById("typing-indicator").style.display = "block";

  // send to backend
  fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      history: JSON.parse(localStorage.getItem("cu_chat_history")) || []
    })
  })
    .then(res => res.json())
    .then(data => {
      document.getElementById("typing-indicator").style.display = "none";
      addMessage(data.answer, "bot");
    })
    .catch(() => {
      document.getElementById("typing-indicator").style.display = "none";
      addMessage("⚠️ Error contacting server.", "bot");
    });
}

// ---------------- LOAD HISTORY BUTTON ----------------
document.getElementById("load-history").addEventListener("click", () => {
  chatBox.innerHTML = "";

  const history = JSON.parse(localStorage.getItem("cu_chat_history")) || [];

  if (history.length === 0) {
    addMessage("No previous chat found.", "bot", false);
    return;
  }

  history.forEach(msg => {
    addMessage(msg.text, msg.sender, false);
  });
});

// ---------------- CLEAR HISTORY BUTTON ----------------
document.getElementById("clear-history").addEventListener("click", () => {
  localStorage.removeItem("cu_chat_history");
  chatBox.innerHTML = "";
  addMessage("Chat history cleared.", "bot", false);
});
