// ─── AgriForce WebSocket Manager ────────────────────────────────────────────

function initNotificationSocket(userId) {
  const token = getAuthToken();
  const ws = new WebSocket(
    `${WS_BASE}/notifications/${userId}?token=${token}`
  );

  ws.onopen = () => {
    console.log(`[WS] Notification socket connected for user ${userId}`);
  };

  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.count !== undefined) updateNotificationBadge(data.count);
      if (data.message) appendNotificationToPanel(data.message, data.type || "info");
    } catch (err) {
      console.warn("[WS] Failed to parse notification message:", err);
    }
  };

  ws.onerror = (err) => {
    console.error("[WS] Notification socket error:", err);
  };

  ws.onclose = () => {
    console.log("[WS] Notification socket closed — reconnecting in 3s");
    setTimeout(() => initNotificationSocket(userId), 3000);
  };

  return ws;
}

function initJobAlertSocket(workerId) {
  const token = getAuthToken();
  const ws = new WebSocket(
    `${WS_BASE}/job-alerts/${workerId}?token=${token}`
  );

  ws.onopen = () => {
    console.log(`[WS] Job alert socket connected for worker ${workerId}`);
  };

  ws.onmessage = (e) => {
    try {
      const job = JSON.parse(e.data);
      prependJobAlertCard(job);
      showToast(`New job: ${job.cropType || "Job"} in ${job.district || "your area"}`, "info");
    } catch (err) {
      console.warn("[WS] Failed to parse job alert message:", err);
    }
  };

  ws.onerror = (err) => {
    console.error("[WS] Job alert socket error:", err);
  };

  ws.onclose = () => {
    console.log("[WS] Job alert socket closed — reconnecting in 3s");
    setTimeout(() => initJobAlertSocket(workerId), 3000);
  };

  return ws;
}

function prependJobAlertCard(job) {
  const container = document.getElementById("jobs-list");
  if (!container) return;

  const card = document.createElement("article");
  card.className = "job-card alert-job-card";
  card.innerHTML = `
    <div class="job-card-header">
      <div>
        <h3 class="job-crop">${job.cropType || "General Labour"}</h3>
        <span class="job-district">
          <i data-lucide="map-pin"></i> ${job.district || "—"}
        </span>
      </div>
      <span class="badge badge-new">New</span>
    </div>
    <div class="job-card-meta">
      <span><i data-lucide="calendar"></i> ${job.startDate || "Flexible"}</span>
      <span><i data-lucide="users"></i> ${job.workersNeeded || 1} workers</span>
      <span><i data-lucide="indian-rupee"></i> ₹${job.dailyWage || "—"}/day</span>
    </div>
    <button class="btn btn-primary btn-sm w-100 mt-2"
      onclick="applyForJob('${job.id}', CURRENT_WORKER_ID)">
      Apply Now
    </button>
  `;
  container.prepend(card);
  if (typeof lucide !== "undefined") lucide.createIcons();
}
