// ─── AgriForce Application Logic ────────────────────────────────────────────

// Initialize Lucide icons on load
document.addEventListener("DOMContentLoaded", () => {
  if (typeof lucide !== "undefined") {
    lucide.createIcons();
  }
});

// Navigation
function handleGetStarted() {
  window.location.href = "register.html";
}

// Landing Page Animations
function animateCounters() {
  const counters = document.querySelectorAll('.counter-value');
  counters.forEach(counter => {
    const target = +counter.getAttribute('data-target');
    const increment = target / 50; // 50 frames
    let current = 0;
    
    const updateCounter = () => {
      current += increment;
      if (current < target) {
        counter.innerText = Math.ceil(current) + '%';
        requestAnimationFrame(updateCounter);
      } else {
        counter.innerText = target + '%';
      }
    };
    updateCounter();
  });
}

function initTestimonialCarousel() {
  // DOM only carousel logic
  let currentIndex = 0;
  const items = document.querySelectorAll('.testimonial-item');
  if (items.length === 0) return;
  
  setInterval(() => {
    items[currentIndex].classList.remove('active');
    currentIndex = (currentIndex + 1) % items.length;
    items[currentIndex].classList.add('active');
  }, 5000);
}

// Authentication
function toggleAuthTab(tab) {
  document.querySelectorAll('.auth-tab').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.auth-pane').forEach(el => el.classList.remove('active'));
  
  const tabBtn = document.querySelector(`.auth-tab[data-tab="${tab}"]`);
  const pane = document.getElementById(`pane-${tab}`);
  
  if (tabBtn) tabBtn.classList.add('active');
  if (pane) pane.classList.add('active');
}

// NOTE: decodeJwtPayload is now provided by getAuthUser() in config.js

async function validateLoginForm(formData) {
  const submitBtn = document.getElementById('login-submit-btn');
  if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Logging in…'; }
  try {
    const data = Object.fromEntries(formData.entries());
    const res = await apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    const token = res.access_token || res.token;
    if (!token) throw new Error('No token received from server');
    setAuthToken(token);

    // Decode role from JWT payload (never trust a UI-visible field alone)
    const user = getAuthUser();
    const role = (user && user.role) || res.role;
    sessionStorage.setItem(ROLE_KEY, role);

    showToast('Login successful! Redirecting…', 'success');
    setTimeout(() => redirectByRole(role), 800);
  } catch (error) {
    showToast(error.message, 'error');
    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Login'; }
  }
}

async function validateRegistrationForm(formData) {
  const submitBtn = document.getElementById('submit-btn');
  if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Creating account…'; }
  try {
    const data = Object.fromEntries(formData.entries());
    
    // Skills handling for worker
    if (data.role === 'WORKER') {
      const skillsSelect = document.getElementById('worker-skills');
      if (skillsSelect) {
        data.skills = Array.from(skillsSelect.selectedOptions).map(opt => opt.value);
      }
    }

    const res = await apiFetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    // Directly log in after registration
    const token = res.access_token || res.token;
    if (token) {
      setAuthToken(token);
      const user = getAuthUser();
      const role = (user && user.role) || res.role;
      sessionStorage.setItem(ROLE_KEY, role);
      showToast('Registration successful! Taking you to your dashboard…', 'success');
      setTimeout(() => redirectByRole(role), 1200);
    } else {
      showToast('Registration successful! Please login.', 'success');
      setTimeout(() => { window.location.href = 'login.html'; }, 1500);
    }
  } catch (error) {
    showToast(error.message, 'error');
    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Create Account'; }
  }
}

async function requestOTP(phone) {
  if (!phone || phone.trim().length < 6) {
    showToast("Please enter a valid phone number first", "warning");
    return;
  }
  try {
    const res = await apiFetch('/auth/request-otp', {
      method: 'POST',
      body: JSON.stringify({ phone })
    });
    document.getElementById('otp-section').style.display = 'block';

    // Development mode: backend returns the OTP in the response
    if (res && res.dev_otp) {
      const otpInput = document.getElementById('reg-otp');
      if (otpInput) otpInput.value = res.dev_otp;
      showToast(`[DEV] Your OTP is: ${res.dev_otp}`, "info");
    } else {
      showToast("OTP sent successfully", "success");
    }
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function verifyOTP(phone, otp) {
  try {
    await apiFetch('/auth/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ phone, otp })
    });
    showToast("OTP verified", "success");
    document.getElementById('otp-verified-badge').style.display = 'inline-block';
    document.getElementById('submit-btn').disabled = false;
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function logoutUser() {
  try {
    await apiFetch('/auth/logout', { method: 'POST' });
  } catch (e) {
    console.error(e);
  } finally {
    setAuthToken(null);
    sessionStorage.removeItem('agriforce_role');
    window.location.href = 'login.html';
  }
}

// Farmer Dashboard
async function renderDemandForecastChart(data) {
  const ctx = document.getElementById('forecastChart');
  if (!ctx) return;
  
  if (window.forecastChartInstance) {
    window.forecastChartInstance.destroy();
  }

  // Fallback data if none provided via API
  const chartData = data || {
    labels: ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10', 'W11', 'W12'],
    demand: [10, 15, 20, 45, 60, 55, 30, 20, 15, 10, 5, 5]
  };

  window.forecastChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartData.labels,
      datasets: [{
        label: 'Labour Demand Forecast',
        data: chartData.demand,
        borderColor: '#2d6a4f',
        backgroundColor: 'rgba(45, 106, 79, 0.1)',
        tension: 0.4,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

async function loadRecommendedWorkers(farmerId) {
  showSkeletonLoader('recommended-workers-panel');
  try {
    const workers = await apiFetch(`/workers/recommended/${farmerId}`);
    const panel = document.getElementById('recommended-workers-panel');
    hideSkeletonLoader('recommended-workers-panel');
    
    if (!workers || workers.length === 0) {
      panel.innerHTML = '<div class="text-center p-4 text-muted">No recommended workers found.</div>';
      return;
    }
    
    panel.innerHTML = workers.map(w => `
      <div class="card mb-2">
        <div class="flex justify-between items-center">
          <div>
            <h4>${w.name}</h4>
            <div class="gap-2 mt-2">
              ${(w.skills || []).map(s => `<span class="badge badge-gray">${s}</span>`).join('')}
            </div>
            <p class="text-muted mt-2"><i data-lucide="map-pin"></i> ${w.distance}km away • ₹${w.dailyWage}/day</p>
          </div>
          <button class="btn btn-primary btn-sm" onclick="applyForJob('DIRECT_HIRE', '${w.id}')">Hire</button>
        </div>
      </div>
    `).join('');
    if (typeof lucide !== "undefined") lucide.createIcons();
  } catch (error) {
    hideSkeletonLoader('recommended-workers-panel');
    console.error(error);
  }
}

async function loadSubsidyAlerts(region, crop) {
  try {
    const alerts = await apiFetch(`/subsidies/alerts?region=${region}&crop=${crop}`);
    const panel = document.getElementById('subsidy-alerts-panel');
    if (!panel) return;
    
    if (!alerts || alerts.length === 0) {
      panel.innerHTML = '<p class="text-muted">No urgent alerts.</p>';
      return;
    }
    
    panel.innerHTML = alerts.map(a => `
      <div class="alert-banner mb-2 p-2 flex justify-between items-center" style="background: rgba(244, 162, 97, 0.1); border-left: 4px solid var(--color-accent); border-radius: 4px;">
        <div>
          <strong>${a.schemeName}</strong>
          <span class="badge badge-amber ml-2">Deadline: ${a.deadlineDays} days</span>
        </div>
        <button class="btn btn-outline btn-sm" onclick="window.location.href='subsidies.html'">View</button>
      </div>
    `).join('');
  } catch (error) {
    console.error(error);
  }
}

// Worker Dashboard
async function calculateProfileCompletion(workerId) {
  try {
    const res = await apiFetch(`/workers/${workerId}/profile-completion`);
    const bar = document.getElementById('profile-progress-bar');
    const text = document.getElementById('profile-progress-text');
    if (bar) bar.style.width = `${res.percentage}%`;
    if (text) text.innerText = `${res.percentage}% Completed`;
    
    const prompt = document.getElementById('profile-prompt');
    if (prompt && res.percentage < 80) {
      prompt.style.display = 'block';
    }
  } catch (error) {
    console.error(error);
  }
}

async function fetchAvailableJobs(filters = {}) {
  showSkeletonLoader('available-jobs-panel');
  try {
    const qs = new URLSearchParams(filters).toString();
    const jobs = await apiFetch(`/jobs/available?${qs}`);
    const panel = document.getElementById('available-jobs-panel');
    hideSkeletonLoader('available-jobs-panel');
    
    if (!jobs || jobs.length === 0) {
      panel.innerHTML = `
        <div class="text-center p-4">
          <p class="text-muted">No jobs match your criteria.</p>
          <button class="btn btn-outline mt-2" onclick="document.getElementById('job-filters').reset(); fetchAvailableJobs();">Clear Filters</button>
        </div>`;
      return;
    }
    
    panel.innerHTML = jobs.map(job => `
      <div class="card mb-4">
        <div class="flex justify-between">
          <h3>${job.cropType} Harvesting</h3>
          <span class="badge badge-green">₹${job.wage}/day</span>
        </div>
        <p class="text-muted mt-2"><i data-lucide="map-pin"></i> ${job.district} • <i data-lucide="calendar"></i> ${job.dates}</p>
        <p class="mt-2"><i data-lucide="users"></i> ${job.workersNeeded} workers needed</p>
        <button id="apply-btn-${job.id}" class="btn btn-primary mt-4 w-100" onclick="applyForJob('${job.id}', CURRENT_WORKER_ID, this)">Apply</button>
      </div>
    `).join('');
    if (typeof lucide !== "undefined") lucide.createIcons();
  } catch (error) {
    hideSkeletonLoader('available-jobs-panel');
    console.error(error);
  }
}

async function loadMyApplications(workerId) {
  try {
    const apps = await apiFetch(`/applications/worker/${workerId}`);
    const tbody = document.querySelector('#my-apps-table tbody');
    if (!tbody) return;
    
    if (!apps || apps.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No applications found.</td></tr>';
      return;
    }
    
    const statusClass = {
      'PENDING': 'badge-amber',
      'ACCEPTED': 'badge-green',
      'REJECTED': 'badge-red'
    };
    
    tbody.innerHTML = apps.map(app => `
      <tr>
        <td>${app.jobTitle}</td>
        <td>${app.farmerName}</td>
        <td>${app.appliedDate}</td>
        <td><span class="badge ${statusClass[app.status]}">${app.status}</span></td>
      </tr>
    `).join('');
  } catch (error) {
    console.error(error);
  }
}

async function renderEarningsChart(workerId, period) {
  const ctx = document.getElementById('earningsChart');
  if (!ctx) return;
  
  if (window.earningsChartInstance) {
    window.earningsChartInstance.destroy();
  }

  try {
    const data = await apiFetch(`/workers/${workerId}/earnings?period=${period}`).catch(() => null);
    
    const chartData = data || {
      labels: ['Jan', 'Feb', 'Mar'],
      earnings: [4500, 6200, 5100]
    };

    window.earningsChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: chartData.labels,
        datasets: [{
          label: 'Earnings (₹)',
          data: chartData.earnings,
          backgroundColor: '#52b788',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      }
    });
  } catch (error) {
    console.error(error);
  }
}

async function applyForJob(jobId, workerId, btnEl) {
  try {
    if (btnEl) btnEl.disabled = true;
    await apiFetch('/applications/apply', {
      method: 'POST',
      body: JSON.stringify({ jobId, workerId })
    });
    showToast("Successfully applied for the job!", "success");
    if (btnEl) btnEl.innerText = "Applied";
  } catch (error) {
    if (btnEl) btnEl.disabled = false;
    showToast(error.message, "error");
  }
}

// Post Job
function goToStep(stepNumber) {
  document.querySelectorAll('.step-content').forEach(el => el.style.display = 'none');
  document.getElementById(`step-${stepNumber}`).style.display = 'block';
  
  document.querySelectorAll('.step-indicator').forEach((el, index) => {
    if (index + 1 <= stepNumber) {
      el.classList.add('active');
    } else {
      el.classList.remove('active');
    }
  });
}

function validateStep(stepNumber) {
  // Add validation logic here before allowing next step
  goToStep(stepNumber + 1);
}

async function autofillPeakSeason(cropType) {
  try {
    const res = await apiFetch(`/crops/peak-season/${cropType}`);
    const startInput = document.getElementById('job-start-date');
    const endInput = document.getElementById('job-end-date');
    if (startInput && res.startDate) startInput.value = res.startDate;
    if (endInput && res.endDate) endInput.value = res.endDate;
    showToast(`Dates autofilled for ${cropType} peak season`, "info");
  } catch (error) {
    console.error(error);
  }
}

async function fetchLocationData(state, district) {
  try {
    const taluks = await apiFetch(`/locations?state=${state}&district=${district}`);
    const select = document.getElementById('taluk-select');
    if (!select) return;
    
    select.innerHTML = '<option value="">Select Taluk</option>' + 
      taluks.map(t => `<option value="${t.id}">${t.name}</option>`).join('');
  } catch (error) {
    console.error(error);
  }
}

async function submitJobPost(formData) {
  try {
    const data = Object.fromEntries(formData.entries());
    
    // Skills multi-select
    const skillsSelect = document.getElementById('req-skills');
    if (skillsSelect) {
      data.skills = Array.from(skillsSelect.selectedOptions).map(opt => opt.value);
    }
    
    await apiFetch('/jobs/create', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    
    document.getElementById('post-job-form').style.display = 'none';
    document.getElementById('success-state').style.display = 'block';
    // Minimal confetti effect
    import('https://cdn.skypack.dev/canvas-confetti').then(module => {
      module.default();
    });
  } catch (error) {
    showToast(error.message, "error");
  }
}

// Job Management (Farmer)
async function editJobPost(jobId) {
  window.location.href = `post-job.html?edit=${jobId}`;
}

async function closeJobPost(jobId) {
  try {
    await apiFetch(`/jobs/${jobId}/close`, { method: 'PATCH' });
    showToast("Job post closed", "success");
    // Reload table row status
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function deleteJobPost(jobId) {
  if (!confirm("Are you sure you want to delete this job post?")) return;
  try {
    await apiFetch(`/jobs/${jobId}`, { method: 'DELETE' });
    showToast("Job post deleted", "success");
    // Remove row
  } catch (error) {
    showToast(error.message, "error");
  }
}

// Equipment Rental
async function applyEquipmentFilters(filters) {
  try {
    const qs = new URLSearchParams(filters).toString();
    const equipment = await apiFetch(`/equipment?${qs}`);
    const grid = document.getElementById('equipment-grid');
    if (!grid) return;
    
    if (!equipment || equipment.length === 0) {
      grid.innerHTML = '<div class="text-center w-100 p-4"><p class="text-muted">No equipment found matching filters.</p></div>';
      return;
    }
    
    grid.innerHTML = equipment.map(eq => `
      <div class="card flex-col justify-between">
        <img src="${eq.image || 'assets/images/placeholder.svg'}" alt="${eq.name}" loading="lazy" style="height: 150px; object-fit: cover; border-radius: 4px;" class="mb-4">
        <div>
          <h3>${eq.name}</h3>
          <span class="badge badge-gray">${eq.type}</span>
          <p class="mt-2"><i data-lucide="map-pin"></i> ${eq.district}</p>
          <p class="font-bold text-primary mt-2">₹${eq.dailyRate}/day</p>
        </div>
        <div class="mt-4 flex justify-between items-center">
          <span class="badge ${eq.available ? 'badge-green' : 'badge-red'}">${eq.available ? 'AVAILABLE' : 'BOOKED'}</span>
          <button class="btn btn-outline btn-sm" onclick="openEquipmentModal('${eq.id}')">View Details</button>
        </div>
      </div>
    `).join('');
    if (typeof lucide !== "undefined") lucide.createIcons();
  } catch (error) {
    console.error(error);
  }
}

async function openEquipmentModal(equipmentId) {
  try {
    const eq = await apiFetch(`/equipment/${equipmentId}`).catch(() => ({
      id: equipmentId, name: "Sample Tractor", type: "Heavy", dailyRate: 1500, description: "Good condition"
    }));
    
    document.getElementById('modal-eq-name').innerText = eq.name;
    document.getElementById('modal-eq-desc').innerText = eq.description;
    document.getElementById('modal-eq-price').innerText = `₹${eq.dailyRate}/day`;
    document.getElementById('equipment-modal').style.display = 'flex';
  } catch (error) {
    showToast(error.message, "error");
  }
}

function closeEquipmentModal() {
  const modal = document.getElementById('equipment-modal');
  if (modal) modal.style.display = 'none';
}

async function submitRentalBooking(bookingData) {
  try {
    await apiFetch('/equipment/book', {
      method: 'POST',
      body: JSON.stringify(bookingData)
    });
    showToast("Booking request sent to provider", "success");
    closeEquipmentModal();
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function contactEquipmentProvider(providerId) {
  try {
    const provider = await apiFetch(`/equipment/provider/${providerId}`);
    window.location.href = `tel:${provider.phone}`;
  } catch (error) {
    console.error(error);
  }
}

// Subsidies
async function fetchSubsidySchemes(region, crop) {
  try {
    const schemes = await apiFetch(`/subsidies?region=${region}&crop=${crop}`);
    const container = document.getElementById('subsidies-container');
    if (!container) return;
    
    if (!schemes || schemes.length === 0) {
      container.innerHTML = `
        <div class="text-center p-6 card">
          <p class="text-muted">No schemes found for your region and crop type.</p>
          <button class="btn btn-outline mt-4">Adjust Filters</button>
        </div>`;
      return;
    }
    
    container.innerHTML = schemes.map(s => `
      <div class="card mb-4">
        <div class="flex justify-between items-start">
          <div>
            <h3>${s.name}</h3>
            <p class="text-muted">${s.ministry}</p>
          </div>
          <span class="badge badge-amber">Deadline: ${s.deadline}</span>
        </div>
        <p class="mt-4">${s.description}</p>
        <div class="mt-4 gap-2 flex">
          ${(s.eligibleCrops || []).map(c => `<span class="badge badge-gray">${c}</span>`).join('')}
        </div>
        <div class="mt-6 flex gap-4">
          <button class="btn btn-outline" onclick="checkSubsidyEligibility({}, '${s.id}')">Check My Eligibility</button>
          <button class="btn btn-primary" onclick="redirectToSchemePortal('${s.url}')">Apply Now</button>
        </div>
        <div id="eligibility-result-${s.id}" class="mt-4"></div>
      </div>
    `).join('');
  } catch (error) {
    console.error(error);
  }
}

async function checkSubsidyEligibility(farmerProfile, schemeId) {
  try {
    const res = await apiFetch(`/subsidies/check-eligibility`, {
      method: 'POST',
      body: JSON.stringify({ farmerProfile, schemeId })
    });
    const resultDiv = document.getElementById(`eligibility-result-${schemeId}`);
    if (!resultDiv) return;
    
    resultDiv.innerHTML = `
      <div class="p-4 rounded mt-4" style="background: var(--color-bg);">
        <h4 class="mb-2">Eligibility Check</h4>
        <ul style="list-style: none; padding: 0;">
          ${res.criteria.map(c => `
            <li class="flex items-center gap-2 mb-1">
              <i data-lucide="${c.met ? 'check-circle' : 'x-circle'}" style="color: ${c.met ? 'var(--color-success)' : 'var(--color-error)'}; width: 16px;"></i>
              ${c.name}
            </li>
          `).join('')}
        </ul>
      </div>
    `;
    if (typeof lucide !== "undefined") lucide.createIcons();
  } catch (error) {
    showToast(error.message, "error");
  }
}

function redirectToSchemePortal(url) {
  if (url) window.open(url, '_blank', 'noopener,noreferrer');
}

// Admin
async function approveUser(userId) {
  try {
    await apiFetch(`/admin/users/${userId}/approve`, { method: 'PATCH' });
    showToast("User approved", "success");
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function deactivateUser(userId) {
  try {
    await apiFetch(`/admin/users/${userId}/deactivate`, { method: 'PATCH' });
    showToast("User deactivated", "warning");
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function viewUserProfile(userId) {
  try {
    const profile = await apiFetch(`/admin/users/${userId}`);
    // show modal with profile details
    console.log(profile);
  } catch (error) {
    console.error(error);
  }
}

async function exportReport(type, range) {
  try {
    const res = await fetch(`${API_BASE}/admin/reports/export?type=${type}&range=${range}`, {
      headers: { "Authorization": `Bearer ${getAuthToken()}` }
    });
    if (!res.ok) throw new Error("Export failed");
    
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agriforce_${type}_report.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    showToast(error.message, "error");
  }
}
