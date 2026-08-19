let currentCustomerId = null;
let currentDashboardData = null;
let categoryChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

// Helper for quick filling demo account chips
window.quickFillCustomer = function(custId) {
  document.getElementById('loginCustomerId').value = custId;
  const select = document.getElementById('loginCustomerSelect');
  if (select) select.value = custId;
  document.getElementById('loginPassword').value = '1234';
};

async function initApp() {
  setupEventListeners();
  await loadCustomerLoginDropdown();

  const savedCustId = sessionStorage.getItem('loggedInCustomerId');
  if (savedCustId) {
    currentCustomerId = savedCustId;
    await showDashboardPage(currentCustomerId);
  } else {
    showLoginPage();
  }
}

function showLoginPage() {
  document.getElementById('loginPage').classList.remove('hidden');
  document.getElementById('dashboardPage').classList.add('hidden');
  document.getElementById('navUserControls').style.display = 'none';
}

async function showDashboardPage(customerId) {
  document.getElementById('loginPage').classList.add('hidden');
  document.getElementById('dashboardPage').classList.remove('hidden');
  document.getElementById('navUserControls').style.display = 'flex';
  await loadCustomerDashboard(customerId);
}

function setupEventListeners() {
  // Login Form submit
  document.getElementById('loginForm').addEventListener('submit', handleLoginSubmit);

  // Login dropdown select sync with input box
  const loginSelect = document.getElementById('loginCustomerSelect');
  loginSelect.addEventListener('change', (e) => {
    if (e.target.value) {
      document.getElementById('loginCustomerId').value = e.target.value;
    }
  });

  // Logout button
  document.getElementById('logoutBtn').addEventListener('click', handleLogout);

  // Refresh button
  document.getElementById('refreshTxnBtn').addEventListener('click', () => {
    if (currentCustomerId) loadCustomerDashboard(currentCustomerId);
  });

  // Tab controls
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const targetTab = btn.getAttribute('data-tab');
      if (targetTab === 'products') document.getElementById('tabProducts').classList.add('active');
      if (targetTab === 'offers') document.getElementById('tabOffers').classList.add('active');
      if (targetTab === 'baseline') document.getElementById('tabBaseline').classList.add('active');
    });
  });

  // Add Transaction Modal
  const txnModal = document.getElementById('txnModal');
  document.getElementById('addTxnBtn').addEventListener('click', () => {
    document.getElementById('txnDate').value = new Date().toISOString().split('T')[0];
    txnModal.classList.add('open');
  });
  document.getElementById('closeTxnModal').addEventListener('click', () => txnModal.classList.remove('open'));
  document.getElementById('cancelTxnBtn').addEventListener('click', () => txnModal.classList.remove('open'));

  // Transaction form submit
  document.getElementById('addTxnForm').addEventListener('submit', handleAddTransaction);

  // Reason Modal
  const reasonModal = document.getElementById('reasonModal');
  document.getElementById('closeReasonModal').addEventListener('click', () => reasonModal.classList.remove('open'));

  // Chat Form Submit
  document.getElementById('chatForm').addEventListener('submit', handleChatSubmit);
}

// Fetch Customers List for Login Dropdown
async function loadCustomerLoginDropdown() {
  try {
    const res = await fetch('/api/customers');
    const data = await res.json();
    if (data.success && data.customers.length > 0) {
      const select = document.getElementById('loginCustomerSelect');
      select.innerHTML = '<option value="">-- Select from Customer List --</option>' +
        data.customers.map(c => `
          <option value="${c.Customer_ID}">
            ${c.Customer_ID} - ${c.Full_Name} (${c.City})
          </option>
        `).join('');

      document.getElementById('loginCustomerId').value = data.customers[0].Customer_ID;
      select.value = data.customers[0].Customer_ID;
    }
  } catch (err) {
    console.error('Failed to load customer list for login:', err);
  }
}

// Handle Login Submission
async function handleLoginSubmit(e) {
  e.preventDefault();
  const customerIdInput = document.getElementById('loginCustomerId').value.trim();
  const passwordInput = document.getElementById('loginPassword').value;
  const errorDiv = document.getElementById('loginError');

  errorDiv.classList.add('hidden');
  errorDiv.innerText = '';

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customerId: customerIdInput,
        password: passwordInput
      })
    });

    const data = await res.json();
    if (data.success) {
      currentCustomerId = data.customerId;
      sessionStorage.setItem('loggedInCustomerId', currentCustomerId);
      await showDashboardPage(currentCustomerId);
    } else {
      errorDiv.innerText = data.error || 'Login failed. Please check Customer ID and password.';
      errorDiv.classList.remove('hidden');
    }
  } catch (err) {
    console.error('Login error:', err);
    errorDiv.innerText = 'Network or server error during login.';
    errorDiv.classList.remove('hidden');
  }
}

// Handle Logout
function handleLogout() {
  sessionStorage.removeItem('loggedInCustomerId');
  currentCustomerId = null;
  showLoginPage();
}

// 2. Fetch & Render Customer Dashboard
async function loadCustomerDashboard(customerId) {
  try {
    const res = await fetch(`/api/customer/${customerId}/dashboard`);
    const data = await res.json();
    if (!data.success) {
      alert(`Error loading dashboard: ${data.error}`);
      return;
    }

    currentDashboardData = data;
    renderProfile(data.customer, data.behavior);
    renderFinancialOverview(data.behavior);
    renderRiskProfile(data.riskProfile);
    renderRecommendations(data.recommendations);
    renderTransactionsTable(data.recentTransactions, data.recentEvents);
  } catch (err) {
    console.error('Dashboard error:', err);
  }
}

// Render Profile Card
function renderProfile(cust, behavior) {
  document.getElementById('navCustId').innerText = cust.Customer_ID;
  document.getElementById('navCustName').innerText = cust.Full_Name;

  document.getElementById('customerAvatar').innerText = cust.Full_Name ? cust.Full_Name.charAt(0) : 'C';
  document.getElementById('custName').innerText = cust.Full_Name;
  document.getElementById('custDetails').innerText = `${cust.Customer_ID} • ${cust.Occupation} • ${cust.City}, ${cust.State}`;

  const badges = document.getElementById('custBadges');
  badges.innerHTML = `
    <span class="pill-tag">${cust.Customer_Segment || 'Standard'}</span>
    <span class="pill-tag">${cust.Loyalty_Tier || 'Blue'} Tier</span>
    <span class="pill-tag">${cust.KYC_Status === 'Verified' ? '✓ KYC Verified' : 'KYC Pending'}</span>
    ${cust.Credit_Card_Holder ? `<span class="pill-tag">${cust.Credit_Card_Type} Card</span>` : ''}
  `;

  document.getElementById('valIncome').innerText = `₹${cust.Monthly_Income.toLocaleString()}`;
  document.getElementById('valCibil').innerText = cust.CIBIL_Score;
  document.getElementById('valSpend').innerText = `₹${behavior.dynamicTotalSpend.toLocaleString()}`;
  document.getElementById('valSavings').innerText = `${(cust.Savings_Ratio * 100).toFixed(0)}%`;
}

// Render Financial Overview & Chart
function renderFinancialOverview(behavior) {
  document.getElementById('topCategoryPill').innerText = `Top Category: ${behavior.topCategory}`;

  const spendList = document.getElementById('categorySpendList');
  spendList.innerHTML = behavior.sortedCategories.map(c => `
    <div class="cat-item">
      <span class="cat-name">${c.category}</span>
      <span class="cat-amt">₹${c.amount.toLocaleString()} (${c.percentage}%)</span>
    </div>
  `).join('');

  // Render Chart.js
  const ctx = document.getElementById('categoryChart').getContext('2d');
  if (categoryChartInstance) {
    categoryChartInstance.destroy();
  }

  const labels = behavior.sortedCategories.map(c => c.category);
  const dataValues = behavior.sortedCategories.map(c => c.amount);

  categoryChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: dataValues,
        backgroundColor: [
          '#00f2fe', '#7928ca', '#ff0080', '#00f5a0', '#f59e0b',
          '#3b82f6', '#ec4899', '#8b5cf6', '#10b981', '#6366f1'
        ],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      cutout: '70%'
    }
  });
}

// Render Risk Profile
function renderRiskProfile(risk) {
  const badge = document.getElementById('riskStatusBadge');
  const metrics = document.getElementById('riskMetrics');

  if (!risk) {
    badge.className = 'status-badge status-green';
    badge.innerText = 'Low Risk';
    metrics.innerHTML = '<div class="metric-box"><span class="metric-label">Fraud Score</span><span class="metric-value">0</span></div>';
    return;
  }

  const isHighRisk = risk.Fraud_Flag || risk.Fraud_Risk_Score > 60;
  badge.className = isHighRisk ? 'status-badge status-red' : 'status-badge status-green';
  badge.innerText = isHighRisk ? '⚠ High Risk Flagged' : '✓ Normal Account';

  metrics.innerHTML = `
    <div class="metric-box">
      <span class="metric-label">Fraud Risk Score</span>
      <span class="metric-value ${isHighRisk ? 'warning-val' : 'success-val'}">${risk.Fraud_Risk_Score} / 100</span>
    </div>
    <div class="metric-box">
      <span class="metric-label">Device Trust</span>
      <span class="metric-value">${risk.Device_Trust_Score} / 100</span>
    </div>
    <div class="metric-box">
      <span class="metric-label">Takeover Risk</span>
      <span class="metric-value">${risk.Account_Takeover_Risk} / 100</span>
    </div>
    <div class="metric-box">
      <span class="metric-label">Security Awareness</span>
      <span class="metric-value highlight-cibil">${risk.Security_Awareness_Score}</span>
    </div>
  `;
}

// Render Recommendations
function renderRecommendations(recs) {
  document.getElementById('prodCount').innerText = recs.topProducts ? recs.topProducts.length : 0;
  document.getElementById('offerCount').innerText = recs.topOffers ? recs.topOffers.length : 0;

  // Products
  const prodContainer = document.getElementById('productsList');
  if (!recs.topProducts || recs.topProducts.length === 0) {
    prodContainer.innerHTML = '<div class="empty-state">No eligible product recommendations.</div>';
  } else {
    prodContainer.innerHTML = recs.topProducts.map(p => `
      <div class="rec-item-card">
        <div class="rec-card-top">
          <div>
            <div class="rec-type-badge">${p.type}</div>
            <h4 class="rec-title">${p.name}</h4>
          </div>
          <div class="score-pill">${p.score} Score</div>
        </div>

        <ul class="rec-bullet-reasons">
          ${p.explanation.reasons.slice(0, 2).map(r => `<li>${r}</li>`).join('')}
        </ul>

        <div class="rec-footer">
          <span class="status-badge status-green">${p.eligibilityStatus}</span>
          <span class="why-link" onclick="openReasonModal('${p.id}', '${p.name.replace(/'/g, "\\'")}')">Why Recommended? &rarr;</span>
        </div>
      </div>
    `).join('');
  }

  // Offers
  const offerContainer = document.getElementById('offersList');
  if (!recs.topOffers || recs.topOffers.length === 0) {
    offerContainer.innerHTML = '<div class="empty-state">No eligible offer recommendations.</div>';
  } else {
    offerContainer.innerHTML = recs.topOffers.map(o => `
      <div class="rec-item-card">
        <div class="rec-card-top">
          <div>
            <div class="rec-type-badge">${o.category} Offer</div>
            <h4 class="rec-title">${o.name}</h4>
          </div>
          <div class="score-pill">${o.score} Score</div>
        </div>

        <ul class="rec-bullet-reasons">
          ${o.explanation.reasons.slice(0, 2).map(r => `<li>${r}</li>`).join('')}
        </ul>

        <div class="rec-footer">
          <span class="status-badge status-green">${o.eligibilityStatus}</span>
          <span class="why-link" onclick="openReasonModal('${o.id}', '${o.name.replace(/'/g, "\\'")}')">Why Recommended? &rarr;</span>
        </div>
      </div>
    `).join('');
  }

  // Baseline
  const b = recs.baseline || {};
  document.getElementById('baselineContainer').innerHTML = `
    <div class="baseline-item">
      <div class="baseline-label">Baseline Product</div>
      <div class="baseline-val">${b.recommendedProduct || 'None'}</div>
    </div>
    <div class="baseline-item">
      <div class="baseline-label">Baseline Credit Card</div>
      <div class="baseline-val">${b.recommendedCreditCard || 'None'}</div>
    </div>
    <div class="baseline-item">
      <div class="baseline-label">Baseline Reward Offer</div>
      <div class="baseline-val">${b.recommendedRewardOffer || 'None'}</div>
    </div>
    <div class="baseline-item">
      <div class="baseline-label">Next Best Action</div>
      <div class="baseline-val highlight-cibil">${b.nextBestAction || 'None'}</div>
    </div>
  `;
}

// Open Reason Modal
function openReasonModal(itemId, itemName) {
  const recs = currentDashboardData ? currentDashboardData.recommendations : null;
  if (!recs) return;

  let item = recs.topProducts.find(p => p.id === itemId);
  if (!item) item = recs.topOffers.find(o => o.id === itemId);

  const titleEl = document.getElementById('reasonModalTitle');
  const contentEl = document.getElementById('reasonModalContent');

  if (item) {
    titleEl.innerText = `Why Recommended: ${itemName}`;
    contentEl.innerHTML = `
      <p style="margin-bottom: 12px;"><strong>Calculated Relevance Score:</strong> <span class="score-pill">${item.score} / 100</span></p>
      <p style="margin-bottom: 12px;"><strong>Eligibility Status:</strong> <span class="status-badge status-green">${item.eligibilityStatus}</span></p>
      <h4 style="margin-top: 14px; margin-bottom: 8px;">Factual Rationale (Data-Backed):</h4>
      <ul style="margin-left: 20px; margin-bottom: 14px;">
        ${item.explanation.reasons.map(r => `<li style="margin-bottom: 6px;">${r}</li>`).join('')}
      </ul>
    `;
  } else {
    titleEl.innerText = itemName;
    contentEl.innerHTML = '<p>Detailed explanation available via AI Chat query.</p>';
  }

  document.getElementById('reasonModal').classList.add('open');
}

// Render Transactions Table
function renderTransactionsTable(txns, events) {
  const tbody = document.getElementById('txnTableBody');
  if (!txns || txns.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center">No transactions recorded yet.</td></tr>';
    return;
  }

  tbody.innerHTML = txns.map(t => `
    <tr>
      <td>${t.Transaction_Date}</td>
      <td><strong>${t.Merchant_Name}</strong></td>
      <td><span class="pill-tag">${t.Merchant_Category}</span></td>
      <td>${t.Transaction_Channel}</td>
      <td class="cat-amt">₹${Number(t.Transaction_Amount).toLocaleString()}</td>
      <td><span class="status-badge ${t.Transaction_Status === 'Success' ? 'status-green' : 'status-red'}">${t.Transaction_Status}</span></td>
    </tr>
  `).join('');
}

// 3. Submit Transaction Handler
async function handleAddTransaction(e) {
  e.preventDefault();

  const amount = document.getElementById('txnAmount').value;
  const merchant = document.getElementById('txnMerchant').value;
  const category = document.getElementById('txnCategory').value;
  const channel = document.getElementById('txnChannel').value;
  const date = document.getElementById('txnDate').value;

  try {
    const res = await fetch('/api/transactions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        Customer_ID: currentCustomerId,
        Transaction_Amount: amount,
        Merchant_Name: merchant,
        Merchant_Category: category,
        Transaction_Channel: channel,
        Transaction_Date: date
      })
    });

    const data = await res.json();
    if (data.success) {
      document.getElementById('txnModal').classList.remove('open');
      document.getElementById('addTxnForm').reset();
      
      // Dynamic refresh
      await loadCustomerDashboard(currentCustomerId);
      alert(`Transaction of ₹${amount} added successfully! Customer profile & recommendations updated dynamically.`);
    } else {
      alert(`Failed to add transaction: ${data.error}`);
    }
  } catch (err) {
    console.error('Add transaction error:', err);
  }
}

// 4. AI Assistant Chat Handler
async function handleChatSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  if (!message) return;

  input.value = '';
  appendUserMessage(message);
  await sendChatMessage(message);
}

function sendQuickPrompt(promptText) {
  appendUserMessage(promptText);
  sendChatMessage(promptText);
}

function appendUserMessage(msg) {
  const container = document.getElementById('chatMessages');
  const userDiv = document.createElement('div');
  userDiv.className = 'message user-msg';
  userDiv.innerHTML = `<div class="msg-content">${escapeHtml(msg)}</div>`;
  container.appendChild(userDiv);
  container.scrollTop = container.scrollHeight;
}

async function sendChatMessage(message) {
  const container = document.getElementById('chatMessages');
  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'message bot-msg';
  loadingDiv.innerHTML = '<div class="msg-content"><em>Thinking & querying customer data...</em></div>';
  container.appendChild(loadingDiv);
  container.scrollTop = container.scrollHeight;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customerId: currentCustomerId,
        message
      })
    });

    const data = await res.json();
    container.removeChild(loadingDiv);

    const botDiv = document.createElement('div');
    botDiv.className = 'message bot-msg';

    botDiv.innerHTML = `
      <div class="msg-content">${formatMarkdown(data.reply)}</div>
    `;
    container.appendChild(botDiv);
    container.scrollTop = container.scrollHeight;

  } catch (err) {
    container.removeChild(loadingDiv);
    console.error('Chat error:', err);
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.innerText = text;
  return div.innerHTML;
}

function formatMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}
