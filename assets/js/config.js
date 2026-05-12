// ─── AgriForce Global Config ───────────────────────────────────────────────
const APP_NAME = "AgriForce";
const API_BASE = "http://localhost:8000/api/v1";
const WS_BASE  = "ws://localhost:8000/ws";

// ── Token persistence — sessionStorage survives page navigations but clears on tab close ──
const TOKEN_KEY = 'agriforce_token';
const ROLE_KEY  = 'agriforce_role';

function getAuthToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

function setAuthToken(token) {
  if (token) {
    sessionStorage.setItem(TOKEN_KEY, token);
  } else {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(ROLE_KEY);
  }
}

/** Returns decoded JWT payload fields (role, sub, exp) — no library needed. */
function getAuthUser() {
  const token = getAuthToken();
  if (!token) return null;
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(base64));
  } catch {
    return null;
  }
}

/**
 * Call at the top of any protected page.
 * If there is no valid token, instantly redirects to login.html.
 */
function requireAuth() {
  const token = getAuthToken();
  if (!token) {
    window.location.replace('login.html');
    return false;
  }
  // Check expiry
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    if (payload.exp && Date.now() / 1000 > payload.exp) {
      setAuthToken(null); // clear expired token
      window.location.replace('login.html');
      return false;
    }
  } catch { /* ignore decode errors — server will reject the token */ }
  return true;
}

// Helper: authenticated fetch wrapper
async function apiFetch(endpoint, options = {}) {
  const token = getAuthToken();
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    ...options.headers,
  };
  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

// Dark/Light mode (JS-variable only, no localStorage)
let isDarkMode = false;
function toggleDarkMode() {
  isDarkMode = !isDarkMode;
  document.body.classList.toggle("dark-mode", isDarkMode);
  const icon = document.getElementById("theme-icon");
  if (icon) icon.setAttribute("data-lucide", isDarkMode ? "sun" : "moon");
  if (typeof lucide !== "undefined") lucide.createIcons();
}

// Notification badge update
function updateNotificationBadge(count) {
  document.querySelectorAll(".notif-badge").forEach(el => {
    el.textContent = count > 99 ? "99+" : count;
    el.style.display = count > 0 ? "flex" : "none";
  });
}

// Append notification to panel
function appendNotificationToPanel(message, type = "info") {
  const panel = document.getElementById("notif-panel");
  if (!panel) return;
  const icons = { info: "info", warning: "alert-triangle", success: "check-circle", error: "x-circle" };
  const item = document.createElement("div");
  item.className = `notif-item notif-${type}`;
  item.innerHTML = `
    <i data-lucide="${icons[type] || 'bell'}" class="notif-icon"></i>
    <div class="notif-body">
      <p class="notif-message">${message}</p>
      <span class="notif-time">Just now</span>
    </div>
  `;
  panel.prepend(item);
  if (typeof lucide !== "undefined") lucide.createIcons();
}

// Skeleton loaders
function showSkeletonLoader(panelId) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  panel.dataset.originalContent = panel.innerHTML;
  panel.innerHTML = `
    <div class="skeleton-wrapper">
      <div class="skeleton skeleton-title"></div>
      <div class="skeleton skeleton-text"></div>
      <div class="skeleton skeleton-text short"></div>
      <div class="skeleton skeleton-block"></div>
    </div>
  `;
}

function hideSkeletonLoader(panelId) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  if (panel.dataset.originalContent !== undefined) {
    panel.innerHTML = panel.dataset.originalContent;
    delete panel.dataset.originalContent;
  }
}

// Utility: show inline field error
function showFieldError(fieldId, message) {
  const field = document.getElementById(fieldId);
  if (!field) return;
  let errEl = field.parentElement.querySelector(".field-error");
  if (!errEl) {
    errEl = document.createElement("span");
    errEl.className = "field-error";
    field.parentElement.appendChild(errEl);
  }
  errEl.textContent = message;
  field.classList.add("is-invalid");
}

function clearFieldError(fieldId) {
  const field = document.getElementById(fieldId);
  if (!field) return;
  const errEl = field.parentElement.querySelector(".field-error");
  if (errEl) errEl.textContent = "";
  field.classList.remove("is-invalid");
}

// Redirect by role
function redirectByRole(role) {
  const routes = {
    FARMER: "farmer-dashboard.html",
    WORKER: "worker-dashboard.html",
    ADMIN: "admin.html",
    EQUIPMENT_PROVIDER: "provider-dashboard.html",
  };
  window.location.href = routes[role] || "index.html";
}

// Toast notification
function showToast(message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast-item toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add("show"));
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
