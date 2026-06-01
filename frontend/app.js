const state = {
  token: localStorage.getItem("noc_token"),
  username: localStorage.getItem("noc_username"),
  roles: JSON.parse(localStorage.getItem("noc_roles") || "[]"),
  selectedAlertId: null,
  selectedRecommendationId: null,
  feedbackType: "Helpful",
  chatSessionId: null,
  refreshTimer: null,
};

const $ = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", () => {
  bindEvents();
  if (state.token) {
    showApp();
    loadAlerts();
    startAutoRefresh();
  } else {
    showLogin();
  }
});

function bindEvents() {
  $("login-form").addEventListener("submit", login);
  $("logout-btn").addEventListener("click", logout);
  $("refresh-btn").addEventListener("click", loadAlerts);
  ["severity-filter", "operator-filter", "circle-filter", "server-filter"].forEach((id) => {
    $(id).addEventListener("change", loadAlerts);
    $(id).addEventListener("keyup", debounce(loadAlerts, 350));
  });
  $("helpful-btn").addEventListener("click", () => setFeedbackType("Helpful"));
  $("not-helpful-btn").addEventListener("click", () => setFeedbackType("Not Helpful"));
  $("feedback-form").addEventListener("submit", submitFeedback);
  $("chat-form").addEventListener("submit", submitChat);
}

async function login(event) {
  event.preventDefault();
  $("login-error").textContent = "";
  try {
    const response = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: $("username").value.trim(),
        password: $("password").value,
      }),
    });
    if (!response.ok) throw new Error("Login failed");
    const data = await response.json();
    state.token = data.session_token;
    state.username = data.username;
    state.roles = data.roles || [];
    localStorage.setItem("noc_token", state.token);
    localStorage.setItem("noc_username", state.username);
    localStorage.setItem("noc_roles", JSON.stringify(state.roles));
    showApp();
    loadAlerts();
    startAutoRefresh();
  } catch (error) {
    $("login-error").textContent = "Unable to login. Check credentials or LDAP settings.";
  }
}

function logout() {
  localStorage.removeItem("noc_token");
  localStorage.removeItem("noc_username");
  localStorage.removeItem("noc_roles");
  state.token = null;
  state.username = null;
  state.roles = [];
  state.selectedAlertId = null;
  state.selectedRecommendationId = null;
  clearInterval(state.refreshTimer);
  showLogin();
}

function showLogin() {
  $("login-view").classList.remove("hidden");
  $("app-view").classList.add("hidden");
}

function showApp() {
  $("login-view").classList.add("hidden");
  $("app-view").classList.remove("hidden");
  $("session-label").textContent = `${state.username || "operator"} | ${state.roles.join(", ") || "noc-viewer"}`;
  const canOperate = hasRole("noc-operator") || hasRole("noc-admin");
  $("feedback-form").classList.toggle("hidden", !canOperate);
  $("chat-form").classList.toggle("hidden", !canOperate);
  $("readonly-feedback").classList.toggle("hidden", canOperate);
  $("readonly-chat").classList.toggle("hidden", canOperate);
}

function hasRole(role) {
  return state.roles.includes(role);
}

async function api(path, options = {}) {
  const headers = {
    ...(options.headers || {}),
    Authorization: `Bearer ${state.token}`,
  };
  const response = await fetch(path, { ...options, headers });
  if (response.status === 401) {
    logout();
    throw new Error("Session expired");
  }
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
}

async function loadAlerts() {
  if (!state.token) return;
  const params = new URLSearchParams();
  params.set("severity", $("severity-filter").value || "CRITICAL");
  setParam(params, "operator", $("operator-filter").value);
  setParam(params, "circle", $("circle-filter").value);
  setParam(params, "server_type", $("server-filter").value);
  const data = await api(`/api/v1/alerts?${params.toString()}`);
  renderAlertList(data.items || []);
  $("refresh-status").textContent = `Updated ${new Date().toLocaleTimeString()}`;
}

function setParam(params, key, value) {
  const cleaned = (value || "").trim();
  if (cleaned) params.set(key, cleaned);
}

function renderAlertList(alerts) {
  $("alert-count").textContent = String(alerts.length);
  const list = $("alert-list");
  list.textContent = "";
  if (!alerts.length) {
    list.innerHTML = '<div class="empty">No alerts match the current filters.</div>';
    return;
  }
  alerts.forEach((alert) => {
    const row = document.createElement("div");
    row.className = `alert-row ${alert.id === state.selectedAlertId ? "active" : ""}`;
    row.tabIndex = 0;
    row.innerHTML = `
      <strong>${escapeHtml(alert.node_name || "Unknown node")}</strong>
      <span class="severity-critical">${escapeHtml(alert.severity)}</span>
      <span class="badge">${escapeHtml(alert.status || "ACTIVE")}</span>
      <div class="muted">${formatTime(alert.timestamp)} | ${escapeHtml(alert.operator || "-")} / ${escapeHtml(alert.circle || "-")} / ${escapeHtml(alert.server_type || "-")}</div>
    `;
    row.addEventListener("click", () => loadAlertDetail(alert.id));
    row.addEventListener("keyup", (event) => {
      if (event.key === "Enter") loadAlertDetail(alert.id);
    });
    list.appendChild(row);
  });
}

async function loadAlertDetail(alertId) {
  state.selectedAlertId = alertId;
  state.chatSessionId = null;
  const [detail, ai, feedback, chat] = await Promise.all([
    api(`/api/v1/alerts/${alertId}`),
    api(`/api/v1/ai/recommendation/${alertId}`),
    api(`/api/v1/feedback/${alertId}`),
    api(`/api/v1/chat/${alertId}`),
  ]);
  renderDetail(detail.alert, detail.timeline || []);
  renderRecommendation(ai.recommendation);
  renderFeedback(feedback.items || []);
  renderChat(chat.items || []);
  renderAlertListSelection();
}

function renderAlertListSelection() {
  document.querySelectorAll(".alert-row").forEach((row) => row.classList.remove("active"));
}

function renderDetail(alert, timeline) {
  $("empty-detail").classList.add("hidden");
  $("alert-detail").classList.remove("hidden");
  $("detail-title").textContent = alert.node ? alert.node.name : "Unknown node";
  $("detail-meta").textContent = `${alert.severity} | ${formatTime(alert.last_event_time || alert.first_event_time)} | ${alert.uei || ""}`;
  $("detail-status").textContent = alert.status || "ACTIVE";
  $("detail-summary").textContent = alert.summary || "No summary available.";
  const node = alert.node || {};
  $("node-details").innerHTML = `
    <dt>Operator</dt><dd>${escapeHtml(node.operator || "-")}</dd>
    <dt>Circle</dt><dd>${escapeHtml(node.circle || "-")}</dd>
    <dt>Server type</dt><dd>${escapeHtml(node.server_type || "-")}</dd>
    <dt>IP address</dt><dd>${escapeHtml(node.ip_address || "-")}</dd>
  `;
  const timelineEl = $("timeline");
  timelineEl.textContent = "";
  if (!timeline.length) {
    timelineEl.innerHTML = '<li class="muted">No lifecycle history yet.</li>';
  } else {
    timeline.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = `${formatTime(item.created_at)}: ${item.from_status || "new"} -> ${item.to_status}`;
      timelineEl.appendChild(li);
    });
  }
}

function renderRecommendation(recommendation) {
  state.selectedRecommendationId = recommendation ? recommendation.id : null;
  const box = $("ai-box");
  if (!recommendation) {
    box.textContent = "No AI recommendation generated yet.";
    return;
  }
  const rec = recommendation.recommendation || {};
  box.innerHTML = `
    <strong>${escapeHtml(rec.summary || "Recommendation available")}</strong>
    <p>Confidence: ${recommendation.confidence_score ?? rec.confidence_score ?? "n/a"}</p>
    <p>Probable causes:</p>
    ${listHtml(rec.probable_causes)}
    <p>Troubleshooting steps:</p>
    ${listHtml(rec.troubleshooting_steps)}
    <p>Suggested next checks:</p>
    ${listHtml(rec.suggested_next_checks)}
  `;
}

function renderFeedback(items) {
  const history = $("feedback-history");
  history.textContent = "";
  if (!items.length) {
    history.innerHTML = '<p class="muted">No feedback yet.</p>';
    return;
  }
  items.forEach((item) => {
    const p = document.createElement("p");
    p.textContent = `${item.feedback_type || "-"} | ${item.resolution_status || "-"} | ${item.user_id}`;
    history.appendChild(p);
  });
}

function renderChat(items) {
  const history = $("chat-history");
  history.textContent = "";
  if (!items.length) {
    history.innerHTML = '<div class="muted">No chat messages yet.</div>';
    return;
  }
  items.forEach(addChatMessage);
}

function addChatMessage(item) {
  const div = document.createElement("div");
  div.className = "chat-message";
  div.innerHTML = `<div class="chat-role">${escapeHtml(item.role)}</div><div>${escapeHtml(item.message || "")}</div>`;
  $("chat-history").appendChild(div);
}

function setFeedbackType(type) {
  state.feedbackType = type;
  $("helpful-btn").classList.toggle("secondary", type !== "Helpful");
  $("not-helpful-btn").classList.toggle("secondary", type !== "Not Helpful");
}

async function submitFeedback(event) {
  event.preventDefault();
  if (!state.selectedAlertId || !state.selectedRecommendationId) return;
  await api("/api/v1/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      alert_id: state.selectedAlertId,
      ai_recommendation_id: state.selectedRecommendationId,
      feedback_type: state.feedbackType,
      resolution_status: $("resolution-status").value,
      comments: sanitizeClientText($("feedback-comments").value),
    }),
  });
  $("feedback-comments").value = "";
  const feedback = await api(`/api/v1/feedback/${state.selectedAlertId}`);
  renderFeedback(feedback.items || []);
}

async function submitChat(event) {
  event.preventDefault();
  if (!state.selectedAlertId) return;
  const input = $("chat-question");
  const question = sanitizeClientText(input.value.trim());
  if (!question) return;
  addChatMessage({ role: "user", message: question });
  input.value = "";
  const response = await api("/api/v1/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      alert_id: state.selectedAlertId,
      question,
      session_id: state.chatSessionId,
    }),
  });
  state.chatSessionId = response.session_id;
  addChatMessage({ role: "assistant", message: response.response_text });
}

function sanitizeClientText(value) {
  return value
    .replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, "[IP]")
    .replace(/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, "[EMAIL]")
    .replace(/\b(token|secret|password|passwd|api[_-]?key|authorization)\b\s*[:=]\s*[^\s,;]+/gi, "$1=[REDACTED]");
}

function listHtml(items) {
  const list = Array.isArray(items) ? items : [];
  if (!list.length) return '<p class="muted">None listed.</p>';
  return `<ol>${list.map((item) => `<li>${escapeHtml(String(item))}</li>`).join("")}</ol>`;
}

function formatTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function startAutoRefresh() {
  clearInterval(state.refreshTimer);
  state.refreshTimer = setInterval(loadAlerts, 20000);
}

function debounce(fn, delay) {
  let timer;
  return () => {
    clearTimeout(timer);
    timer = setTimeout(fn, delay);
  };
}
