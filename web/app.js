const messagesEl = document.getElementById("messages");
const sessionsEl = document.getElementById("sessions");
const formEl = document.getElementById("composer");
const inputEl = document.getElementById("input");
const statusEl = document.getElementById("status");
const providerBadgeEl = document.getElementById("provider-badge");
const sessionIdEl = document.getElementById("session-id");
const newChatBtn = document.getElementById("new-chat");

let currentSessionId = null;

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderMessage(role, content, meta = "") {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.innerHTML = `<strong>${role}</strong><br>${escapeHtml(content)}${meta ? `<div class="meta">${escapeHtml(meta)}</div>` : ""}`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function clearMessages() {
  messagesEl.innerHTML = "";
}

function setSessionId(sessionId) {
  currentSessionId = sessionId;
  sessionIdEl.textContent = `Session: ${sessionId || "-"}`;
}

async function loadHealth() {
  const res = await fetch("/api/health");
  const data = await res.json();
  statusEl.textContent = `status: ${data.status} / model: ${data.model}`;
  providerBadgeEl.textContent = `provider: ${data.provider}`;
}

async function loadSessions() {
  const res = await fetch("/api/sessions");
  const data = await res.json();
  sessionsEl.innerHTML = "";

  for (const session of data.sessions) {
    const btn = document.createElement("button");
    btn.className = "session-btn";
    if (session.session_id === currentSessionId) {
      btn.classList.add("active");
    }

    btn.textContent = `${session.title} (${new Date(session.created_at).toLocaleString()})`;
    btn.addEventListener("click", async () => {
      setSessionId(session.session_id);
      await loadMessages(session.session_id);
      await loadSessions();
    });
    sessionsEl.appendChild(btn);
  }
}

async function loadMessages(sessionId) {
  if (!sessionId) {
    clearMessages();
    return;
  }

  const res = await fetch(`/api/messages?session_id=${encodeURIComponent(sessionId)}`);
  if (!res.ok) {
    clearMessages();
    return;
  }

  const data = await res.json();
  clearMessages();
  for (const msg of data.messages) {
    renderMessage(msg.role, msg.content, msg.created_at);
  }
}

async function sendMessage(text) {
  renderMessage("user", text);

  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: currentSessionId,
      message: text,
    }),
  });

  const data = await res.json();
  if (!res.ok) {
    renderMessage("assistant", `Error: ${data.error || "unknown"}`);
    return;
  }

  setSessionId(data.session_id);
  const citationText = data.citations.length ? `citations: ${data.citations.join(", ")}` : "";
  renderMessage("assistant", data.answer, citationText);

  await loadSessions();
}

newChatBtn.addEventListener("click", async () => {
  setSessionId(null);
  clearMessages();
  await loadSessions();
});

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = inputEl.value.trim();
  if (!text) {
    return;
  }

  inputEl.value = "";
  await sendMessage(text);
});

inputEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    formEl.requestSubmit();
  }
});

async function boot() {
  await loadHealth();
  await loadSessions();
}

boot().catch((err) => {
  statusEl.textContent = `boot error: ${String(err)}`;
});
