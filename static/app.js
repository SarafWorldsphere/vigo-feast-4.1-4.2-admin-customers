const state = {
  token: localStorage.getItem('vigo_admin_token') || '',
  otpSent: false,
  otpExpiresAt: null,
  otpTimer: null,
  customerPage: 1,
  customerTotalPages: 0,
  customerDetailId: null,
  customerDetail: null,
  customerFilters: {
    search: '',
    status: 'all',
    joined_from: '',
    joined_to: '',
  },
  customerOrderList: null,
  adminProfile: null,
  quickSearchTimer: null,
  quickSearchRequest: 0,
};

const loginView = document.getElementById('loginView');
const dashboardView = document.getElementById('dashboardView');
const kpiGrid = document.getElementById('kpiGrid');
const authMessage = document.getElementById('authMessage');
const modal = document.getElementById('kpiModal');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');
const passwordLoginForm = document.getElementById('passwordLoginForm');
const otpLoginForm = document.getElementById('otpLoginForm');
const otpVerifyBlock = document.getElementById('otpVerifyBlock');
const verifyOtpButton = document.getElementById('verifyOtpButton');
const sendOtpButton = document.getElementById('sendOtpButton');
const customerSummaryGrid = document.getElementById('customerSummaryGrid');
const customerTableBody = document.getElementById('customerTableBody');
const customerListMessage = document.getElementById('customerListMessage');
const customerDetailPanel = document.getElementById('customerDetailPanel');
const customerDetailMessage = document.getElementById('customerDetailMessage');
const customerEditForm = document.getElementById('customerEditForm');
const notificationWrapper = document.getElementById('notificationWrapper');
const notificationsPanel = document.getElementById('notificationsPanel');
const notificationsList = document.getElementById('notificationsList');
let currentKpiDetail = null;

function setMessage(text, success = false) {
  authMessage.textContent = text || '';
  authMessage.classList.toggle('success', success);
}

function toggleTabs(activeTab) {
  const tabs = document.querySelectorAll('.tab-button');
  const forms = document.querySelectorAll('.auth-form');
  tabs.forEach((tab) => tab.classList.toggle('active', tab.dataset.tab === activeTab));
  forms.forEach((form) => form.classList.toggle('active', form.id === (activeTab === 'password' ? 'passwordLoginForm' : 'otpLoginForm')));
}

document.querySelectorAll('.tab-button').forEach((button) => {
  button.addEventListener('click', () => toggleTabs(button.dataset.tab));
});

function showDashboard() {
  loginView.classList.add('hidden');
  dashboardView.classList.remove('hidden');
}

function showLogin() {
  loginView.classList.remove('hidden');
  dashboardView.classList.add('hidden');
}

function handleExpiredSession() {
  state.token = '';
  localStorage.removeItem('vigo_admin_token');
  showLogin();
  setMessage('Your session has expired. Please sign in again.');
}

function setActiveSection(sectionId) {
  if (sectionId !== 'customersSection' && state.customerDetailId !== null) {
    closeCustomerDetail();
  }
  document.querySelectorAll('.nav-item[data-section]').forEach((item) => {
    item.classList.toggle('active', item.dataset.section === sectionId);
  });
  document.querySelectorAll('.dashboard-section, .customers-section').forEach((section) => {
    section.classList.toggle('hidden', section.id !== sectionId);
  });
}

async function apiRequest(url, options = {}, auth = true) {
  const headers = { ...(options.headers || {}) };
  if (!headers['Content-Type'] && options.body && typeof options.body === 'string') {
    headers['Content-Type'] = 'application/json';
  }
  if (auth && state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(url, { ...options, headers });
  if (response.status === 401 && auth) {
    handleExpiredSession();
    const error = new Error('Your session has expired. Please sign in again.');
    error.sessionExpired = true;
    throw error;
  }
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) {
    const message = typeof payload === 'object' && payload ? (payload.detail || payload.message || 'Request failed') : payload;
    throw new Error(message);
  }
  return payload;
}

passwordLoginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    username: document.getElementById('username').value.trim(),
    password: document.getElementById('password').value,
  };

  try {
    setMessage('');
    const response = await apiRequest('/admin/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }, false);
    state.token = response.token;
    localStorage.setItem('vigo_admin_token', state.token);
    setMessage('Login successful', true);
    showDashboard();
    await loadDashboard();
  } catch (error) {
    setMessage(error.message);
  }
});

otpLoginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const mobile_number = document.getElementById('otpMobile').value.trim();
  try {
    setMessage('');
    const language = document.getElementById('otpLanguage').value;
    const response = await apiRequest('/admin/login/otp', {
      method: 'POST',
      body: JSON.stringify({ mobile_number, language }),
    }, false);
    state.otpSent = true;
    startOtpCountdown(Number(response.expires_in_seconds) || 600);
    otpVerifyBlock.classList.remove('hidden');
    verifyOtpButton.classList.remove('hidden');
    if (response.otp_code) {
      setMessage(`Development OTP: ${response.otp_code}`, true);
    } else {
      setMessage('OTP sent successfully', true);
    }
  } catch (error) {
    setMessage(error.message);
  }
});

function startOtpCountdown(seconds) {
  if (state.otpTimer) window.clearInterval(state.otpTimer);
  state.otpExpiresAt = Date.now() + seconds * 1000;
  const countdown = document.querySelector('.countdown');
  const update = () => {
    const remaining = Math.max(0, Math.ceil((state.otpExpiresAt - Date.now()) / 1000));
    countdown.textContent = `${String(Math.floor(remaining / 60)).padStart(2, '0')}:${String(remaining % 60).padStart(2, '0')}`;
    if (remaining === 0) {
      state.otpSent = false;
      window.clearInterval(state.otpTimer);
      state.otpTimer = null;
    }
  };
  update();
  state.otpTimer = window.setInterval(update, 1000);
}

verifyOtpButton.addEventListener('click', async () => {
  const mobile_number = document.getElementById('otpMobile').value.trim();
  const code = [...document.querySelectorAll('.otp-digit')].map((input) => input.value).join('');
  if (!state.otpSent || !mobile_number || code.length !== 6) {
    setMessage('Please send and complete the OTP first');
    return;
  }

  try {
    const response = await apiRequest('/admin/login/verify', {
      method: 'POST',
      body: JSON.stringify({ mobile_number, otp_code: code }),
    }, false);
    state.token = response.token;
    localStorage.setItem('vigo_admin_token', state.token);
    setMessage('OTP verified successfully', true);
    showDashboard();
    await loadDashboard();
  } catch (error) {
    setMessage(error.message);
  }
});

document.getElementById('resendOtpButton').addEventListener('click', () => {
  const mobile_number = document.getElementById('otpMobile').value.trim();
  if (!mobile_number) {
    setMessage('Enter your mobile number first');
    return;
  }
  document.querySelectorAll('.otp-digit').forEach((input) => { input.value = ''; });
  otpLoginForm.dispatchEvent(new Event('submit'));
});

function formatValue(item) {
  if (item.unit === 'amount' || item.currency === 'INR') {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(item.value);
  }
  if (typeof item.value === 'number') {
    return item.value.toLocaleString();
  }
  return item.value;
}

function formatPercentChange(value, period) {
  if (value === null || value === undefined) return `No previous-period baseline ${period}`;
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value}% ${period}`;
}

async function loadDashboard() {
  try {
    const [response, adminProfile] = await Promise.all([
      apiRequest('/admin/dashboard'),
      apiRequest('/admin/me'),
    ]);
    state.adminProfile = adminProfile;
    renderAdminProfile(adminProfile);
    const cards = response.kpis || [];
    kpiGrid.innerHTML = cards.map((card) => `
      <article class="kpi-card ${card.key === 'todays_revenue' ? 'teal' : ''}" data-key="${card.key}">
        <div class="kpi-label">${card.title}</div>
        <div class="kpi-value">${formatValue(card)}</div>
        <div class="kpi-trend">${card.change_vs_last_week !== undefined ? `New customers: ${formatPercentChange(card.change_vs_last_week, 'vs last week')}` : (card.change_in_last_hour !== undefined || card.change_vs_last_hour !== undefined ? formatPercentChange(card.change_in_last_hour ?? card.change_vs_last_hour, 'in last hour') : card.change_vs_yesterday !== undefined ? formatPercentChange(card.change_vs_yesterday, 'vs yesterday') : 'Live')}</div>
        <div class="kpi-source"><strong>Source:</strong>${card.source_table}</div>
        <button class="kpi-open" type="button" data-open-kpi="${escapeHtml(card.key)}">Open</button>
      </article>
    `).join('');

    renderDashboardSupportingData(response);
  } catch (error) {
    if (error.sessionExpired) return;
    setMessage(error.message);
  }
}

function renderLineChart(points, valueKey, label, formatLabel, options = {}) {
  if (!points.length) return '<p class="customer-empty-detail">No data available.</p>';
  const width = 720;
  const height = 220;
  const left = 48;
  const right = 12;
  const top = options.showValueLabels ? 30 : 16;
  const bottom = 34;
  const max = Math.max(1, ...points.map((point) => Number(point[valueKey]) || 0));
  const axisStep = Math.max(1, Math.ceil(max / 4));
  const axisMax = axisStep * 4;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const coords = points.map((point, index) => {
    const x = points.length === 1
      ? left + plotWidth / 2
      : left + (plotWidth * index) / (points.length - 1);
    const value = Number(point[valueKey]) || 0;
    const y = top + plotHeight - (plotHeight * value) / axisMax;
    return { x, y, label: formatLabel(point), value, point };
  });
  const line = coords.map(({ x, y }) => `${x},${y}`).join(' ');
  const tickEvery = options.showAllXLabels ? 1 : Math.max(1, Math.ceil(points.length / 6));
  const ticks = coords
    .map((point, index) => ({ ...point, index }))
    .filter((point) => point.index % tickEvery === 0 || point.index === points.length - 1)
    .map((point) => `<text x="${point.x}" y="${height - 8}" text-anchor="middle">${escapeHtml(point.label)}</text>`)
    .join('');
  const dots = coords
    .map(({ x, y, value, point }) => {
      const isToday = options.highlightToday && point.is_today;
      const revenue = options.revenueKey
        ? `; revenue ${formatCurrency(Number(point[options.revenueKey]) || 0)}`
        : '';
      const valueLabelText = options.valueLabel || valueKey;
      const title = `${value.toLocaleString()} ${valueLabelText}${revenue}`;
      const valueLabel = options.showValueLabels
        ? `<text class="line-chart-value" x="${x}" y="${y - 9}" text-anchor="middle">${value.toLocaleString()}</text>`
        : '';
      return `
        <g>
          <circle class="${isToday ? 'today' : ''}" cx="${x}" cy="${y}" r="${isToday ? 6 : 4}">
            <title>${escapeHtml(title)}</title>
          </circle>
          ${valueLabel}
        </g>
      `;
    })
    .join('');
  const grid = Array.from({ length: 5 }, (_, index) => {
    const value = axisMax - axisStep * index;
    const y = top + (plotHeight * index) / 4;
    return `
      <line class="line-chart-grid" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}"></line>
      <text class="line-chart-axis-label" x="${left - 8}" y="${y + 3}" text-anchor="end">${value.toLocaleString()}</text>
    `;
  }).join('');
  return `
    <svg class="line-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(label)}">
      <title>${escapeHtml(label)}</title>
      ${grid}
      <polyline points="${line}"></polyline>
      ${dots}${ticks}
    </svg>
  `;
}

function shortDateLabel(point) {
  const date = new Date(`${point.date}T00:00:00`);
  return Number.isNaN(date.getTime())
    ? point.date
    : date.toLocaleDateString(undefined, { month: 'numeric', day: 'numeric' });
}

function shortHourLabel(point) {
  const date = new Date(point.hour);
  return Number.isNaN(date.getTime())
    ? point.hour
    : date.toLocaleTimeString(undefined, { hour: 'numeric' });
}

function renderDashboardSupportingData(data) {
  document.getElementById('ordersLast7DaysChart').innerHTML = renderLineChart(
    data.orders_last_7_days || [],
    'order_count',
    'Orders - last 7 days',
    shortDateLabel,
    {
      showAllXLabels: true,
      showValueLabels: true,
      highlightToday: true,
      revenueKey: 'revenue',
      valueLabel: 'orders',
    },
  );
  const activity = data.recent_activity || [];
  document.getElementById('recentAdminActivity').innerHTML = activity.length
    ? activity.map((item) => `
        <article class="activity-item">
          <strong>${escapeHtml(item.description || item.action || 'Admin activity')}</strong>
          ${item.description ? '' : `<p>${escapeHtml(item.entity_name || item.entity_type || '')}</p>`}
          <small>${escapeHtml(item.admin_name || 'Admin')}</small>
          <time>${escapeHtml(formatDateTime(item.created_at))}</time>
        </article>
      `).join('')
    : '<p class="customer-empty-detail">No recent admin activity.</p>';
}

kpiGrid.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-open-kpi]');
  if (!button) return;
  try {
    const detail = await apiRequest(
      `/admin/dashboard/kpi/${encodeURIComponent(button.dataset.openKpi)}`,
    );
    renderDetail(detail);
  } catch (error) {
    if (!error.sessionExpired) setMessage(error.message);
  }
});

function openDashboardKpi(cardKey) {
  return apiRequest(`/admin/dashboard/kpi/${encodeURIComponent(cardKey)}`)
    .then(renderDetail);
}

function renderDetail(detail, notificationFocus = null) {
  modalTitle.textContent = detail.title || 'KPI Details';
  currentKpiDetail = detail;
  const rows = detail.data || [];
  const exportButton = document.getElementById('modalExportButton');
  exportButton.classList.toggle('hidden', detail.visualization !== 'live_orders');

  if (['total_customers', 'inactive_customers', 'new_this_week'].includes(detail.key)) {
    renderCustomerKpiList(detail);
  } else if (detail.key === 'average_customer_rating') {
    renderCustomerFeedbackList(detail, notificationFocus);
  } else if (detail.visualization === 'customer_orders') {
    renderCustomerOrderList(detail);
  } else if (detail.visualization === 'live_orders') {
    modalBody.innerHTML = `
      <p class="detail-total">${Number(detail.count || 0).toLocaleString()}</p>
      <h4>Orders by status</h4>
      ${renderStatusBreakdown(detail.status_breakdown || [])}
      <h4>Orders per hour</h4>
      <div class="detail-chart">${renderLineChart(detail.orders_per_hour || [], 'order_count', 'Live orders per hour', shortHourLabel)}</div>
      <h4>Current live orders</h4>
      ${renderTable(rows, [
        ['order_id', 'Order'],
        ['customer_name', 'Customer'],
        ['restaurant_id', 'Restaurant'],
        ['amount', 'Amount'],
        ['order_status', 'Status'],
        ['delivery_eta', 'ETA'],
      ], notificationFocus?.type === 'order' ? {
        targetKey: 'order_id',
        targetId: notificationFocus.id,
        targetType: 'order',
      } : {})}
    `;
  } else if (detail.visualization === 'todays_revenue') {
    modalBody.innerHTML = `
      <p><strong>Today's revenue:</strong> ${escapeHtml(formatCurrency(detail.total || 0))}</p>
      <h4>Revenue by hour</h4>
      <div class="detail-chart">${renderLineChart(detail.hourly_revenue || [], 'revenue', 'Revenue by hour', shortHourLabel)}</div>
      <h4>Payments</h4>
      ${renderTable(rows, [
        ['payment_id', 'Payment'],
        ['order_id', 'Order'],
        ['method', 'Method'],
        ['amount', 'Amount'],
        ['payment_status', 'Status'],
        ['transaction_ref', 'Transaction'],
        ['created_at', 'Paid at'],
      ])}
    `;
  } else if (!rows.length) {
    modalBody.innerHTML = '<p>No records found</p>';
  } else {
    const headers = Object.keys(rows[0]);
    const hasCustomerLinks = rows.some((row) => row.customer_id !== null && row.customer_id !== undefined);
    const tHead = '<thead><tr>' + headers.map((header) => `<th>${escapeHtml(header.replace(/_/g, ' '))}</th>`).join('') +
      (hasCustomerLinks ? '<th>Customer</th>' : '') + '</tr></thead>';
    const tBody = '<tbody>' + rows.map((row) => {
      const isTarget = notificationFocus?.type === 'feedback'
        && String(row.feedback_id) === String(notificationFocus.id);
      const targetAttrs = isTarget
        ? ` class="notification-highlight" data-notification-target="feedback:${escapeHtml(notificationFocus.id)}"`
        : '';
      return '<tr' + targetAttrs + '>' +
        headers.map((header) => `<td data-label="${escapeHtml(header.replace(/_/g, ' '))}">${header === 'email' ? formatEmail(row[header] ?? '') : formatModalCell(row[header])}</td>`).join('') +
        (hasCustomerLinks
          ? `<td>${row.customer_id === null || row.customer_id === undefined ? '' : `<button class="link-btn" type="button" data-open-customer="${escapeHtml(row.customer_id)}">View / edit</button>`}</td>`
          : '') + '</tr>';
    }).join('') + '</tbody>';
    modalBody.innerHTML = '<div class="table-wrap"><table>' + tHead + tBody + '</table></div>';
  }
  let notificationTarget = null;
  if (notificationFocus) {
    notificationTarget = notificationFocus.id
      ? modalBody.querySelector(
        `[data-notification-target="${notificationFocus.type}:${notificationFocus.id}"]`,
      )
      : null;
    modalBody.insertAdjacentHTML('afterbegin', notificationContextMarkup(!notificationTarget));
  }
  modal.classList.remove('hidden');
  modal.setAttribute('aria-hidden', 'false');
  if (notificationTarget) highlightNotificationTarget(notificationTarget);
}

function renderCustomerKpiList(detail) {
  const isInactive = detail.key === 'inactive_customers';
  const hasCustomerFilters = detail.key === 'total_customers';
  const rows = detail.data || [];
  const page = Number(detail.page || 1);
  const pageSize = Number(detail.page_size || 25);
  const total = Number(detail.count || 0);
  const totalPages = Number(detail.total_pages || 0);
  const first = total ? (page - 1) * pageSize + 1 : 0;
  const last = Math.min(page * pageSize, total);
  const headers = isInactive
    ? ['Customer', 'Customer ID', 'Orders', 'Cancelled', 'Mobile', 'Action']
    : ['Customer', 'Customer ID', 'Joined', 'Orders', 'Cancelled', 'Mobile'];
  const customerRows = rows.map((row) => `
    <tr>
      <td data-label="Customer">${escapeHtml(row.name)}</td>
      <td data-label="Customer ID">#${escapeHtml(row.customer_id)}</td>
      ${isInactive ? '' : `<td data-label="Joined">${escapeHtml(formatDate(row.created_at))}</td>`}
      <td data-label="Orders">${Number(row.order_count || 0).toLocaleString()}</td>
      <td data-label="Cancelled">${Number(row.cancelled_order_count || 0).toLocaleString()}</td>
      <td data-label="Mobile">${escapeHtml(row.mobile || '-')}</td>
      ${isInactive ? `<td data-label="Action"><button class="link-btn" type="button" data-reactivate-customer="${escapeHtml(row.customer_id)}">Reactivate</button></td>` : ''}
    </tr>
  `).join('');
  modalBody.innerHTML = `
    <form id="customerKpiSearchForm" class="customer-order-search ${hasCustomerFilters ? 'customer-kpi-filters' : ''}">
      <label>
        <span>Search customers</span>
        <input id="customerKpiSearch" type="search" maxlength="200" value="${escapeHtml(detail.search || '')}" />
      </label>
      ${hasCustomerFilters ? `
        <label>
          <span>Status</span>
          <select id="customerKpiStatus">
            <option value="all" ${detail.status === 'all' ? 'selected' : ''}>All customers</option>
            <option value="active" ${detail.status === 'active' ? 'selected' : ''}>Active</option>
            <option value="inactive" ${detail.status === 'inactive' ? 'selected' : ''}>Inactive</option>
          </select>
        </label>
        <label>
          <span>Joined from</span>
          <input id="customerKpiJoinedFrom" type="date" value="${escapeHtml(detail.joined_from || '')}" />
        </label>
        <label>
          <span>Joined to</span>
          <input id="customerKpiJoinedTo" type="date" value="${escapeHtml(detail.joined_to || '')}" />
        </label>
      ` : ''}
      <button class="secondary-btn" type="submit">Search</button>
    </form>
    ${rows.length
      ? `<div class="table-wrap"><table><thead><tr>${headers.map((header) => `<th>${header}</th>`).join('')}</tr></thead><tbody>${customerRows}</tbody></table></div>`
      : '<p>No customers found.</p>'}
    <div class="customer-pagination">
      <span>${first}-${last} of ${total.toLocaleString()} customers</span>
      <div>
        <button class="secondary-btn" type="button" data-customer-kpi-page="${page - 1}" ${page <= 1 ? 'disabled' : ''}>Previous</button>
        <button class="secondary-btn" type="button" data-customer-kpi-page="${page + 1}" ${page >= totalPages ? 'disabled' : ''}>Next</button>
      </div>
    </div>
  `;
}

function renderCustomerFeedbackList(detail, notificationFocus = null) {
  const rows = detail.data || [];
  const page = Number(detail.page || 1);
  const pageSize = Number(detail.page_size || 25);
  const total = Number(detail.count || 0);
  const totalPages = Number(detail.total_pages || 0);
  const first = total ? (page - 1) * pageSize + 1 : 0;
  const last = Math.min(page * pageSize, total);
  const feedbackRows = rows.map((row) => {
    const isTarget = notificationFocus?.type === 'feedback'
      && String(row.feedback_id) === String(notificationFocus.id);
    const targetAttrs = isTarget
      ? ` class="notification-highlight" data-notification-target="feedback:${escapeHtml(notificationFocus.id)}"`
      : '';
    return `
      <tr${targetAttrs}>
        <td data-label="Customer">${escapeHtml(row.customer_name || 'Customer unavailable')}</td>
        <td data-label="Order">#${escapeHtml(row.order_id)}</td>
        <td data-label="Rating">${Number(row.rating).toLocaleString()}</td>
        <td data-label="Comments">${formatModalCell(row.comments)}</td>
        <td data-label="Date">${escapeHtml(formatDateTime(row.created_at))}</td>
      </tr>
    `;
  }).join('');
  modalBody.innerHTML = `
    <p class="detail-total">${Number(detail.average_rating || 0).toFixed(1)} / 5</p>
    <p>${Number(detail.overall_review_count || 0).toLocaleString()} reviews</p>
    <form id="customerRatingSearchForm" class="customer-order-search">
      <label>
        <span>Search reviews</span>
        <input id="customerRatingSearch" type="search" maxlength="200" value="${escapeHtml(detail.search || '')}" />
      </label>
      <button class="secondary-btn" type="submit">Search</button>
    </form>
    ${rows.length
      ? `<div class="table-wrap"><table>
          <thead><tr><th>Customer</th><th>Order</th><th>Rating</th><th>Comments</th><th>Date</th></tr></thead>
          <tbody>${feedbackRows}</tbody>
        </table></div>`
      : '<p>No matching reviews found.</p>'}
    <div class="customer-pagination">
      <span>${first}-${last} of ${total.toLocaleString()} reviews</span>
      <div>
        <button class="secondary-btn" type="button" data-customer-kpi-page="${page - 1}" ${page <= 1 ? 'disabled' : ''}>Previous</button>
        <button class="secondary-btn" type="button" data-customer-kpi-page="${page + 1}" ${page >= totalPages ? 'disabled' : ''}>Next</button>
      </div>
    </div>
  `;
}

function customerKpiQuery(page, form = null) {
  const query = new URLSearchParams({
    page: String(page),
    page_size: String(currentKpiDetail?.page_size || 25),
  });
  const search = form?.querySelector('#customerKpiSearch, #customerRatingSearch')?.value
    ?? currentKpiDetail?.search;
  if (search) query.set('search', search.trim());

  if (currentKpiDetail?.key === 'total_customers') {
    const status = form?.querySelector('#customerKpiStatus')?.value
      ?? currentKpiDetail.status;
    const joinedFrom = form?.querySelector('#customerKpiJoinedFrom')?.value
      ?? currentKpiDetail.joined_from;
    const joinedTo = form?.querySelector('#customerKpiJoinedTo')?.value
      ?? currentKpiDetail.joined_to;
    if (status) query.set('status', status);
    if (joinedFrom) query.set('joined_from', joinedFrom);
    if (joinedTo) query.set('joined_to', joinedTo);
  }
  return query;
}

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(Number(amount) || 0);
}

function renderStatusBreakdown(statuses) {
  const max = Math.max(1, ...statuses.map((item) => Number(item.count) || 0));
  if (!statuses.length) return '<p>No live orders by status.</p>';
  return `<div class="status-breakdown">${statuses.map((item) => `
    <div class="status-breakdown-row">
      <span>${escapeHtml(item.status)}</span>
      <div class="status-breakdown-track" aria-label="${escapeHtml(item.status)}">
        <div class="status-breakdown-bar" style="width:${(Number(item.count) / max) * 100}%"></div>
      </div>
      <strong>${Number(item.count).toLocaleString()}</strong>
    </div>
  `).join('')}</div>`;
}

function renderTable(rows, columns, options = {}) {
  if (!rows.length) return '<p>No records found.</p>';
  return `<div class="table-wrap"><table><thead><tr>${columns
    .map(([, label]) => `<th>${escapeHtml(label)}</th>`).join('')}</tr></thead><tbody>${rows
    .map((row) => {
      const isTarget = options.targetId !== undefined
        && String(row[options.targetKey]) === String(options.targetId);
      const targetAttrs = isTarget
        ? ` class="notification-highlight" data-notification-target="${escapeHtml(options.targetType)}:${escapeHtml(options.targetId)}"`
        : '';
      return `<tr${targetAttrs}>${columns.map(([key, label]) => {
      const value = key === 'amount' ? formatCurrency(row[key]) : row[key];
      const renderedValue = key === 'email' ? formatEmail(value ?? '') : formatModalCell(value);
      return `<td data-label="${escapeHtml(label)}">${renderedValue}</td>`;
      }).join('')}</tr>`;
    }).join('')}</tbody></table></div>`;
}

function notificationContextMarkup(unavailable) {
  return `
    <p class="notification-origin">From your notification</p>
    ${unavailable ? '<p class="notification-unavailable">This item is no longer available</p>' : ''}
  `;
}

function highlightNotificationTarget(target) {
  target.classList.add('notification-highlight');
  target.scrollIntoView({ behavior: 'smooth', block: 'center' });
  window.setTimeout(() => target.classList.remove('notification-highlight'), 4000);
}

document.getElementById('modalExportButton').addEventListener('click', () => {
  if (currentKpiDetail?.visualization !== 'live_orders') return;
  const columns = [
    ['order_id', 'Order'],
    ['customer_name', 'Customer'],
    ['restaurant_id', 'Restaurant'],
    ['amount', 'Amount'],
    ['order_status', 'Status'],
    ['delivery_eta', 'ETA'],
  ];
  const csv = [
    columns.map(([, label]) => label),
    ...currentKpiDetail.data.map((row) => columns.map(([key]) => row[key] ?? '')),
  ].map((record) => record.map((value) => `"${String(value).replace(/"/g, '""')}"`).join(',')).join('\r\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'live-orders.csv';
  document.body.appendChild(link);
  link.click();
  window.setTimeout(() => {
    link.remove();
    URL.revokeObjectURL(url);
  }, 1000);
});

function formatModalCell(value) {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'number') return value.toLocaleString();
  if (typeof value === 'string' && value.includes('T')) {
    const d = new Date(value);
    return escapeHtml(Number.isNaN(d.getTime()) ? value : d.toLocaleString());
  }
  return escapeHtml(typeof value === 'object' ? JSON.stringify(value) : value);
}

document.getElementById('modalCloseButton').addEventListener('click', () => {
  modal.classList.add('hidden');
  modal.setAttribute('aria-hidden', 'true');
});

modalBody.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-open-customer]');
  if (button) {
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
    await openCustomerDetail(Number(button.dataset.openCustomer));
    return;
  }
  const pageButton = event.target.closest('[data-order-page]');
  if (pageButton && state.customerOrderList) {
    await openCustomerOrderList(
      state.customerOrderList.orderType,
      state.customerOrderList.customerId,
      state.customerOrderList.search,
      Number(pageButton.dataset.orderPage),
      state.customerOrderList.highlightOrderId,
    );
    return;
  }
  const customerKpiPageButton = event.target.closest('[data-customer-kpi-page]');
  if (customerKpiPageButton && currentKpiDetail) {
    const query = customerKpiQuery(Number(customerKpiPageButton.dataset.customerKpiPage));
    try {
      const detail = await apiRequest(
        `/admin/customers/kpi/${encodeURIComponent(currentKpiDetail.key)}?${query.toString()}`,
      );
      renderDetail(detail);
    } catch (error) {
      modalBody.insertAdjacentHTML(
        'afterbegin',
        `<p class="notification-unavailable">${escapeHtml(error.message)}</p>`,
      );
    }
  }
});

modalBody.addEventListener('submit', async (event) => {
  if (
    ['customerKpiSearchForm', 'customerRatingSearchForm'].includes(event.target.id)
    && currentKpiDetail
  ) {
    event.preventDefault();
    const query = customerKpiQuery(1, event.target);
    try {
      const detail = await apiRequest(
        `/admin/customers/kpi/${encodeURIComponent(currentKpiDetail.key)}?${query.toString()}`,
      );
      renderDetail(detail);
    } catch (error) {
      modalBody.insertAdjacentHTML(
        'afterbegin',
        `<p class="notification-unavailable">${escapeHtml(error.message)}</p>`,
      );
    }
    return;
  }
  if (event.target.id !== 'customerOrderSearchForm' || !state.customerOrderList) return;
  event.preventDefault();
  await openCustomerOrderList(
    state.customerOrderList.orderType,
    state.customerOrderList.customerId,
    document.getElementById('customerOrderSearch').value.trim(),
    1,
  );
});

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[character]);
}

function formatDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
}

function formatEmail(value) {
  return escapeHtml(value).replace(/([@.])/g, '$1<wbr>');
}

function renderAdminProfile(profile) {
  const name = String(profile.full_name || '');
  const initials = name.trim().split(/\s+/).filter(Boolean).map((part) => part[0]).join('').toUpperCase();
  document.getElementById('adminAvatarInitials').textContent = initials;
  document.getElementById('adminMenuName').textContent = name;
  document.getElementById('adminMenuRole').textContent = profile.role || '';
}

function formatDateTime(value) {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

async function loadCustomerSummary() {
  const response = await apiRequest('/admin/customers/summary');
  const cards = response.kpis || [];
  customerSummaryGrid.innerHTML = cards.map((card) => {
    let trend = 'Live';
    if (card.key === 'total_customers') {
      trend = `${Number(card.new_this_week || 0).toLocaleString()} joined this week (${Number(card.new_last_week || 0).toLocaleString()} last week)`;
    } else if (card.key === 'inactive_customers') {
      trend = `${card.percentage}% of customers`;
    } else if (card.key === 'new_this_week') {
      trend = `${card.last_week} joined last week`;
    } else if (card.key === 'average_customer_rating') {
      trend = `${card.review_count} reviews`;
    } else if (card.key === 'total_orders') {
      trend = `${Number(card.today || 0).toLocaleString()} orders today`;
    } else if (card.key === 'cancelled_orders') {
      trend = `${Number(card.today || 0).toLocaleString()} cancelled today`;
    }
    const value = card.value === null || card.value === undefined
      ? '—'
      : card.key === 'average_customer_rating'
        ? `${Number(card.value).toFixed(1)} / 5`
        : Number(card.value).toLocaleString();
    return `
      <button class="kpi-card teal customer-kpi-card" type="button" data-key="${escapeHtml(card.key)}">
        <div class="kpi-label">${escapeHtml(card.title)}</div>
        <div class="kpi-value">${escapeHtml(value)}</div>
        <div class="kpi-trend">${escapeHtml(trend)}</div>
        <div class="kpi-source"><strong>Source:</strong>${escapeHtml(card.source_table)}</div>
        <span class="kpi-open">Open</span>
      </button>
    `;
  }).join('');
}

customerSummaryGrid.addEventListener('click', async (event) => {
  const card = event.target.closest('[data-key]');
  if (!card) return;
  try {
    if (['total_orders', 'cancelled_orders'].includes(card.dataset.key)) {
      await openCustomerOrderList(
        card.dataset.key === 'cancelled_orders' ? 'cancelled' : 'orders',
      );
      return;
    }
    const detail = await apiRequest(
      `/admin/customers/kpi/${encodeURIComponent(card.dataset.key)}`,
    );
    renderDetail(detail);
  } catch (error) {
    customerListMessage.textContent = `Unable to load customer KPI details: ${error.message}`;
  }
});

async function loadNotifications() {
  notificationsList.textContent = 'Loading notifications…';
  try {
    const response = await apiRequest('/admin/notifications');
    const localReadKey = response.local_read_key || '';
    notificationsList.dataset.localReadKey = localReadKey;
    let localReadIds = new Set();
    if (localReadKey) {
      try {
        const savedIds = JSON.parse(localStorage.getItem(localReadKey) || '[]');
        if (Array.isArray(savedIds)) localReadIds = new Set(savedIds.map(String));
      } catch {
        localReadIds = new Set();
      }
    }
    const items = response.items.map((notification) => {
      const id = notification.id ?? notification.notification_id;
      return {
        ...notification,
        id,
        is_read: localReadKey
          ? localReadIds.has(String(id))
          : notification.is_read,
      };
    });
    const unread = localReadKey
      ? items.filter((notification) => !notification.is_read).length
      : Number(response.unread_count || 0);
    const unreadBadge = document.getElementById('notificationUnreadCount');
    unreadBadge.textContent = unread.toLocaleString();
    unreadBadge.classList.toggle('hidden', unread === 0);
    notificationsList.innerHTML = items.length
      ? items.map((notification) => `
          <button class="notification-item ${notification.is_read ? '' : 'is-unread'}"
            type="button" data-notification-id="${escapeHtml(notification.id)}"
            data-notification-type="${escapeHtml(notification.notification_type)}"
            data-local-only="${localReadKey ? 'true' : 'false'}"
            data-target-module="${escapeHtml(notification.target?.module || '')}"
            data-target-customer-id="${escapeHtml(notification.target?.customer_id ?? '')}"
            data-target-order-id="${escapeHtml(notification.target?.order_id ?? '')}">
            <div class="notification-item-heading">
              <strong>${escapeHtml(notification.title)}</strong>
              <time>${escapeHtml(formatDate(notification.created_at))}</time>
            </div>
            <p>${escapeHtml(notification.message)}</p>
          </button>
        `).join('')
      : '<p class="notification-empty">No notifications.</p>';
  } catch (error) {
    notificationsList.textContent = `Unable to load notifications: ${error.message}`;
  }
}

function updateUnreadBadge(unreadCount) {
  const unread = Number(unreadCount || 0);
  const unreadBadge = document.getElementById('notificationUnreadCount');
  unreadBadge.textContent = unread.toLocaleString();
  unreadBadge.classList.toggle('hidden', unread === 0);
}

notificationsList.addEventListener('click', async (event) => {
  const notification = event.target.closest('[data-notification-id]');
  if (!notification) return;

  try {
    const result = notification.dataset.localOnly === 'true'
      ? { local_only: true }
      : await apiRequest(
        `/admin/notifications/${encodeURIComponent(notification.dataset.notificationId)}/read`,
        { method: 'POST' },
      );
    if (result.local_only && notificationsList.dataset.localReadKey) {
      const localReadKey = notificationsList.dataset.localReadKey;
      let readIds = new Set();
      try {
        const savedIds = JSON.parse(localStorage.getItem(localReadKey) || '[]');
        if (Array.isArray(savedIds)) readIds = new Set(savedIds.map(String));
      } catch {
        readIds = new Set();
      }
      readIds.add(notification.dataset.notificationId);
      localStorage.setItem(localReadKey, JSON.stringify([...readIds]));
      notification.classList.remove('is-unread');
      const unreadCount = notificationsList.querySelectorAll('.notification-item.is-unread').length;
      updateUnreadBadge(unreadCount);
    } else {
      updateUnreadBadge(result.unread_count);
    }
    notificationsPanel.classList.add('hidden');
    document.getElementById('notificationsButton').setAttribute('aria-expanded', 'false');

    const targetCustomerId = notification.dataset.targetCustomerId;
    if (notification.dataset.targetModule === 'customers' && targetCustomerId) {
      setActiveSection('customersSection');
      await openCustomerDetail(Number(targetCustomerId));
      return;
    }

    const reference = String(notification.dataset.notificationType || '')
      .trim()
      .toLowerCase()
      .match(/^(customer|inactive_customer|new_customer|order|cancelled_order|feedback|low_rating):(\d+)$/);
    if (!reference) {
      throw new Error('Unsupported notification type');
    }
    const type = reference[1];
    const itemId = reference[2];
    const notificationFocus = {
      type: ['inactive_customer', 'new_customer'].includes(type)
        ? 'customer'
        : type === 'low_rating'
          ? 'feedback'
          : type,
      id: itemId,
    };
    if (['customer', 'inactive_customer', 'new_customer'].includes(type)) {
      setActiveSection('customersSection');
      state.customerFilters = {
        search: '',
        status: 'all',
        joined_from: '',
        joined_to: '',
      };
      document.getElementById('customerSearch').value = '';
      document.getElementById('customerStatusFilter').value = 'all';
      document.getElementById('customerJoinedFrom').value = '';
      document.getElementById('customerJoinedTo').value = '';
      const customers = await loadCustomerSection({
        customerId: itemId,
      });
      if (customers === null) return;
      const target = itemId
        ? customerTableBody.querySelector(
          `[data-notification-target="customer:${itemId}"]`,
        )
        : null;
      customerListMessage.innerHTML = notificationContextMarkup(!target);
      if (target) highlightNotificationTarget(target);
    } else if (type === 'order') {
      setActiveSection('dashboardSection');
      await loadDashboard();
      const params = new URLSearchParams();
      if (itemId) params.set('order_id', itemId);
      const query = params.toString();
      const detail = await apiRequest(
        `/admin/dashboard/kpi/live_orders${query ? `?${query}` : ''}`,
      );
      renderDetail(detail, notificationFocus);
    } else if (type === 'cancelled_order') {
      setActiveSection('customersSection');
      const customers = await loadCustomerSection();
      if (customers === null) return;
      await openCustomerOrderList(
        'cancelled',
        null,
        itemId,
        1,
        itemId,
        'cancelled_order',
      );
    } else if (['feedback', 'low_rating'].includes(type)) {
      setActiveSection('customersSection');
      const customers = await loadCustomerSection();
      if (customers === null) return;
      const params = new URLSearchParams();
      if (itemId) params.set('feedback_id', itemId);
      const query = params.toString();
      const detail = await apiRequest(
        `/admin/customers/kpi/average_customer_rating${query ? `?${query}` : ''}`,
      );
      renderDetail(detail, notificationFocus);
    }
  } catch (error) {
    notificationsPanel.classList.remove('hidden');
    document.getElementById('notificationsButton').setAttribute('aria-expanded', 'true');
    notificationsList.textContent = `Unable to open notification: ${error.message}`;
  }
});

document.getElementById('notificationsButton').addEventListener('click', async () => {
  const isOpening = notificationsPanel.classList.contains('hidden');
  notificationsPanel.classList.toggle('hidden', !isOpening);
  document.getElementById('notificationsButton').setAttribute('aria-expanded', String(isOpening));
  if (isOpening) await loadNotifications();
});

document.getElementById('closeNotificationsButton').addEventListener('click', () => {
  notificationsPanel.classList.add('hidden');
  document.getElementById('notificationsButton').setAttribute('aria-expanded', 'false');
});

document.addEventListener('click', (event) => {
  if (!notificationWrapper.contains(event.target)) {
    notificationsPanel.classList.add('hidden');
    document.getElementById('notificationsButton').setAttribute('aria-expanded', 'false');
  }
});

const quickSearchInput = document.getElementById('quickSearchInput');
const quickSearchWrapper = document.getElementById('quickSearchWrapper');
const quickSearchResults = document.getElementById('quickSearchResults');

quickSearchInput.addEventListener('input', () => {
  if (state.quickSearchTimer) window.clearTimeout(state.quickSearchTimer);
  const query = quickSearchInput.value.trim();
  if (query.length < 2) {
    quickSearchResults.classList.add('hidden');
    quickSearchResults.innerHTML = '';
    quickSearchInput.setAttribute('aria-expanded', 'false');
    return;
  }
  state.quickSearchTimer = window.setTimeout(() => runQuickSearch(query), 250);
});

async function runQuickSearch(query) {
  const requestId = ++state.quickSearchRequest;
  quickSearchResults.classList.remove('hidden');
  quickSearchResults.innerHTML = '<p>Searching…</p>';
  quickSearchInput.setAttribute('aria-expanded', 'true');
  try {
    const response = await apiRequest(`/admin/quick-search?q=${encodeURIComponent(query)}`);
    if (requestId !== state.quickSearchRequest || quickSearchInput.value.trim() !== query) return;
    const customers = response.customers || [];
    const orders = response.orders || [];
    quickSearchResults.innerHTML = customers.length || orders.length
      ? `
        ${customers.length ? `<h3>Customers</h3>${customers.map((customer) => `
          <button class="quick-search-result" type="button" data-search-customer="${escapeHtml(customer.customer_id)}">
            <strong>${escapeHtml(customer.name)}</strong>
            <span>${escapeHtml(customer.mobile || '')}${customer.email ? ` · ${formatEmail(customer.email)}` : ''}</span>
          </button>
        `).join('')}` : ''}
        ${orders.length ? `<h3>Orders</h3>${orders.map((order) => `
          <button class="quick-search-result" type="button" data-search-order="${escapeHtml(order.order_id)}">
            <strong>Order #${escapeHtml(order.order_id)}</strong>
            <span>${escapeHtml(order.customer_name || '')} · ${escapeHtml(order.order_status || '')}</span>
          </button>
        `).join('')}` : ''}
      `
      : '<p>No results found</p>';
  } catch (error) {
    if (requestId === state.quickSearchRequest) {
      quickSearchResults.innerHTML = `<p class="notification-unavailable">${escapeHtml(error.message)}</p>`;
    }
  }
}

quickSearchResults.addEventListener('click', async (event) => {
  const customerButton = event.target.closest('[data-search-customer]');
  const orderButton = event.target.closest('[data-search-order]');
  closeQuickSearch();
  if (customerButton) {
    setActiveSection('customersSection');
    await openCustomerDetail(Number(customerButton.dataset.searchCustomer));
  } else if (orderButton) {
    const orderId = String(orderButton.dataset.searchOrder);
    setActiveSection('customersSection');
    await openCustomerOrderList('orders', null, orderId, 1, orderId);
  }
});

function closeQuickSearch() {
  quickSearchResults.classList.add('hidden');
  quickSearchInput.setAttribute('aria-expanded', 'false');
}

document.addEventListener('click', (event) => {
  if (!quickSearchWrapper.contains(event.target)) closeQuickSearch();
});

const adminMenuWrapper = document.getElementById('adminMenuWrapper');
const adminMenu = document.getElementById('adminMenu');
document.getElementById('adminAvatarButton').addEventListener('click', () => {
  const opening = adminMenu.classList.contains('hidden');
  adminMenu.classList.toggle('hidden', !opening);
  document.getElementById('adminAvatarButton').setAttribute('aria-expanded', String(opening));
});
document.addEventListener('click', (event) => {
  if (!adminMenuWrapper.contains(event.target)) {
    adminMenu.classList.add('hidden');
    document.getElementById('adminAvatarButton').setAttribute('aria-expanded', 'false');
  }
});
document.getElementById('adminMenuLogout').addEventListener('click', () => {
  document.getElementById('logoutButton').click();
});

function equalizeCustomerRows() {
  const rows = [...customerTableBody.rows];
  rows.forEach((row) => { row.style.height = ''; });
  if (window.matchMedia('(max-width: 920px)').matches || rows.length === 0) return;
  const height = Math.ceil(Math.max(...rows.map((row) => row.getBoundingClientRect().height)));
  rows.forEach((row) => { row.style.height = `${height}px`; });
}

const customerTableWrapper = document.querySelector('.customer-list-card .table-wrap');
if (customerTableWrapper && 'ResizeObserver' in window) {
  const customerTableResizeObserver = new ResizeObserver(() => {
    window.requestAnimationFrame(equalizeCustomerRows);
  });
  customerTableResizeObserver.observe(customerTableWrapper);
}

window.addEventListener('resize', () => {
  window.requestAnimationFrame(equalizeCustomerRows);
});

async function loadCustomers({ customerId = null } = {}) {
  customerListMessage.textContent = 'Loading customers…';
  const query = new URLSearchParams({
    page: String(customerId === null ? state.customerPage : 1),
    page_size: '25',
  });
  if (customerId === null) {
    query.set('status', state.customerFilters.status);
    Object.entries(state.customerFilters).forEach(([key, value]) => {
      if (value) query.set(key, value);
    });
  } else {
    query.set('focus_customer_id', String(customerId));
  }

  try {
    const response = await apiRequest(`/admin/customers?${query.toString()}`);
    if (customerId === null && state.customerPage > Math.max(response.total_pages, 1)) {
      state.customerPage = Math.max(response.total_pages, 1);
      await loadCustomers();
      return;
    }
    if (customerId !== null) state.customerPage = response.page;
    state.customerTotalPages = response.total_pages;
    customerListMessage.textContent = response.total
      ? `${Number(response.total).toLocaleString()} customer${response.total === 1 ? '' : 's'} found`
      : 'No customers match these filters';

    customerTableBody.innerHTML = response.items.map((customer) => {
      const active = customer.is_active === true;
      const isTarget = customerId !== null
        && String(customer.customer_id) === String(customerId);
      return `
        <tr${isTarget ? ` class="notification-highlight" data-notification-target="customer:${escapeHtml(customerId)}"` : ''}>
          <td data-label="Customer"><strong>${escapeHtml(customer.name)}</strong><small>#${escapeHtml(customer.customer_id)}</small></td>
          <td data-label="Mobile">${escapeHtml(customer.mobile || '—')}</td>
          <td data-label="Email">${formatEmail(customer.email || '—')}</td>
          <td data-label="Orders"><button class="link-btn customer-order-count" type="button" data-order-type="orders" data-customer-id="${escapeHtml(customer.customer_id)}">${Number(customer.order_count || 0).toLocaleString()}</button></td>
          <td data-label="Cancelled"><button class="link-btn customer-order-count" type="button" data-order-type="cancelled" data-customer-id="${escapeHtml(customer.customer_id)}">${Number(customer.cancelled_order_count || 0).toLocaleString()}</button></td>
          <td data-label="Loyalty points">${Number(customer.loyalty_points || 0).toLocaleString()}</td>
          <td data-label="Status"><span class="customer-status ${active ? 'is-active' : 'is-inactive'}">${active ? 'Active' : 'Inactive'}</span></td>
          <td data-label="Actions" class="customer-row-actions">
            <button class="link-btn" type="button" data-customer-action="view" data-customer-id="${escapeHtml(customer.customer_id)}">View / edit</button>
            <button class="link-btn" type="button" data-customer-action="status" data-customer-id="${escapeHtml(customer.customer_id)}" data-next-active="${!active}">${active ? 'Deactivate' : 'Activate'}</button>
            <button class="link-btn danger-link" type="button" data-customer-action="delete" data-customer-id="${escapeHtml(customer.customer_id)}">Delete</button>
          </td>
        </tr>
      `;
    }).join('');
    customerTableBody.querySelectorAll('[data-customer-action]').forEach((button) => {
      button.addEventListener('click', () => handleCustomerAction(button));
    });
    window.requestAnimationFrame(equalizeCustomerRows);

    const first = response.total ? (response.page - 1) * response.page_size + 1 : 0;
    const last = Math.min(response.page * response.page_size, response.total);
    document.getElementById('customerPaginationLabel').textContent =
      `${first}-${last} of ${Number(response.total).toLocaleString()}`;
    document.getElementById('customerPreviousPage').disabled = response.page <= 1;
    document.getElementById('customerNextPage').disabled =
      response.page >= response.total_pages || response.total_pages === 0;
    return response.items;
  } catch (error) {
    customerListMessage.textContent = `Unable to load customers: ${error.message}`;
    customerTableBody.innerHTML = '';
    document.getElementById('customerPaginationLabel').textContent = 'Customers unavailable';
    document.getElementById('customerPreviousPage').disabled = true;
    document.getElementById('customerNextPage').disabled = true;
    return null;
  }
}

customerTableBody.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-order-type][data-customer-id]');
  if (!button) return;
  await openCustomerOrderList(
    button.dataset.orderType,
    Number(button.dataset.customerId),
  );
});

async function openCustomerOrderList(
  orderType,
  customerId = null,
  search = '',
  page = 1,
  highlightOrderId = null,
  notificationType = null,
) {
  state.customerOrderList = {
    orderType,
    customerId,
    search,
    page,
    highlightOrderId,
    notificationType,
  };
  modalTitle.textContent = customerId === null
    ? (orderType === 'cancelled' ? 'Cancelled Orders' : 'Total Orders')
    : (orderType === 'cancelled' ? 'Customer Cancelled Orders' : 'Customer Orders');
  document.getElementById('modalExportButton').classList.add('hidden');
  modalBody.innerHTML = '<p>Loading orders…</p>';
  modal.classList.remove('hidden');
  modal.setAttribute('aria-hidden', 'false');

  const query = new URLSearchParams({
    order_type: orderType,
    page: String(page),
  });
  if (customerId !== null) query.set('customer_id', String(customerId));
  if (search) query.set('search', search);
  try {
    const response = await apiRequest(`/admin/customers/orders?${query.toString()}`);
    renderCustomerOrderList({
      ...response,
      key: 'customer_orders',
      title: modalTitle.textContent,
      visualization: 'customer_orders',
    });
    if (notificationType) {
      const notificationTarget = modalBody.querySelector(
        `[data-notification-target="${notificationType}:${highlightOrderId}"]`,
      );
      modalBody.insertAdjacentHTML(
        'afterbegin',
        notificationContextMarkup(!notificationTarget),
      );
      if (notificationTarget) highlightNotificationTarget(notificationTarget);
    }
  } catch (error) {
    modalBody.innerHTML = `<p class="notification-unavailable">Unable to load orders: ${escapeHtml(error.message)}</p>`;
  }
}

function renderCustomerOrderList(detail) {
  const orderType = detail.order_type || state.customerOrderList?.orderType || 'orders';
  const customerId = detail.customer_id ?? state.customerOrderList?.customerId ?? null;
  const search = state.customerOrderList?.search || '';
  const page = Number(detail.page || state.customerOrderList?.page || 1);
  const pageSize = Number(detail.page_size || 25);
  const total = Number(detail.total || 0);
  const items = detail.items || detail.data || [];
  const headers = [
    '<th>Order ID</th>',
    '<th>Customer</th>',
    '<th>Status</th>',
    ...(orderType === 'cancelled' ? ['<th>Cancellation status</th>'] : []),
    '<th>Amount</th>',
    '<th>Date</th>',
    '<th>Action</th>',
  ].join('');
  const rows = items.map((order) => `
    <tr class="${String(order.order_id) === String(state.customerOrderList?.highlightOrderId) ? 'quick-search-highlight' : ''}${String(order.order_id) === String(state.customerOrderList?.highlightOrderId) && state.customerOrderList?.notificationType ? ' notification-highlight' : ''}"${String(order.order_id) === String(state.customerOrderList?.highlightOrderId) && state.customerOrderList?.notificationType ? ` data-notification-target="${escapeHtml(state.customerOrderList.notificationType)}:${escapeHtml(order.order_id)}"` : ''}>
      <td data-label="Order ID">#${escapeHtml(order.order_id)}</td>
      <td data-label="Customer">${escapeHtml(order.customer_name || 'Customer unavailable')}</td>
      <td data-label="Status">${escapeHtml(order.order_status || '-')}</td>
      ${orderType === 'cancelled' ? `<td data-label="Cancellation status">${escapeHtml(order.cancellation_status || '-')}</td>` : ''}
      <td data-label="Amount">${escapeHtml(formatCurrency(order.amount || 0))}</td>
      <td data-label="Date">${escapeHtml(formatDate(order.date))}</td>
      <td data-label="Action">${order.customer_id == null ? '' : `<button class="link-btn" type="button" data-open-customer="${escapeHtml(order.customer_id)}">View / edit</button>`}</td>
    </tr>
  `).join('');
  const first = total ? (page - 1) * pageSize + 1 : 0;
  const last = Math.min(page * pageSize, total);
  const totalPages = Number(detail.total_pages || 0);
  modalBody.innerHTML = `
    <form id="customerOrderSearchForm" class="customer-order-search">
      <label>
        <span>Search by customer name or order ID</span>
        <input id="customerOrderSearch" type="search" maxlength="200" value="${escapeHtml(search)}" />
      </label>
      <button class="secondary-btn" type="submit">Search</button>
    </form>
    ${items.length
    ? `<div class="table-wrap"><table><thead><tr>${headers}</tr></thead><tbody>${rows}</tbody></table></div>`
    : '<p>No matching orders found.</p>'}
    <div class="customer-pagination">
      <span>${first}–${last} of ${total.toLocaleString()} orders</span>
      <div>
        <button class="secondary-btn" type="button" data-order-page="${page - 1}" ${page <= 1 ? 'disabled' : ''}>Previous</button>
        <button class="secondary-btn" type="button" data-order-page="${page + 1}" ${page >= totalPages ? 'disabled' : ''}>Next</button>
      </div>
    </div>
  `;
  state.customerOrderList = {
    orderType,
    customerId,
    search,
    page,
    highlightOrderId: state.customerOrderList?.highlightOrderId || null,
    notificationType: state.customerOrderList?.notificationType || null,
  };
}

document.getElementById('exportCustomersButton').addEventListener('click', async () => {
  try {
    const query = new URLSearchParams();
    Object.entries(state.customerFilters).forEach(([key, value]) => {
      if (value) query.set(key, value);
    });
    const response = await fetch(`/admin/customers/export.xlsx?${query.toString()}`, {
      headers: { Authorization: `Bearer ${state.token}` },
    });
    if (response.status === 401) {
      handleExpiredSession();
      throw new Error('Your session has expired. Please sign in again.');
    }
    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = errorText || 'Unable to export customers';
      try {
        errorMessage = JSON.parse(errorText).detail || errorMessage;
      } catch {
        // The server may return a non-JSON error response.
      }
      throw new Error(errorMessage);
    }
    const file = await response.blob();
    const url = URL.createObjectURL(file);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'customers.xlsx';
    document.body.appendChild(link);
    link.click();
    window.setTimeout(() => {
      link.remove();
      URL.revokeObjectURL(url);
    }, 1000);
  } catch (error) {
    customerListMessage.textContent = `Unable to export customers: ${error.message}`;
  }
});

async function handleCustomerAction(button) {
  const customerId = Number(button.dataset.customerId);
  try {
    if (button.dataset.customerAction === 'view') {
      await openCustomerDetail(customerId);
    } else if (button.dataset.customerAction === 'status') {
      await changeCustomerStatus(customerId, button.dataset.nextActive === 'true');
    } else if (button.dataset.customerAction === 'delete') {
      await deleteCustomer(customerId);
    }
  } catch (error) {
    customerListMessage.textContent = `Customer action failed: ${error.message}`;
  }
}

async function loadCustomerSection(options = {}) {
  customerListMessage.textContent = 'Loading customer data…';
  try {
    const [, customers] = await Promise.all([
      loadCustomerSummary(),
      loadCustomers(options),
    ]);
    return customers;
  } catch (error) {
    customerListMessage.textContent = `Unable to load customer summary: ${error.message}`;
    return null;
  }
}

async function refreshCustomerData() {
  await Promise.all([loadCustomers(), loadCustomerSummary()]);
}

async function openCustomerDetail(customerId) {
  customerDetailMessage.textContent = 'Loading customer details…';
  customerDetailPanel.classList.remove('hidden');
  document.getElementById('customerDetailBackdrop').classList.remove('hidden');
  window.requestAnimationFrame(() => customerDetailPanel.classList.add('is-open'));
  try {
    const detail = await apiRequest(`/admin/customers/${encodeURIComponent(customerId)}`);
    state.customerDetailId = customerId;
    state.customerDetail = detail;
    const customer = detail.customer;
    document.getElementById('customerDetailTitle').textContent = customer.name;
    document.getElementById('customerIdLabel').textContent = `Customer ID #${customer.customer_id}`;
    document.getElementById('customerAvatar').textContent =
      (customer.name || 'C').trim().charAt(0).toUpperCase();
    document.getElementById('customerEditName').value = customer.name || '';
    document.getElementById('customerEditMobile').value = customer.mobile || '';
    document.getElementById('customerEditEmail').value = customer.email || '';
    const addressSelect = document.getElementById('customerEditAddress');
    addressSelect.innerHTML = '<option value="">No default address</option>' +
      detail.addresses.map((address) =>
        `<option value="${escapeHtml(address.address_id)}">${escapeHtml(address.address_text)}</option>`
      ).join('');
    addressSelect.value = customer.default_address_id ?? '';
    const addressValue = document.getElementById('customerDefaultAddressValue');
    const updateAddressValue = () => {
      addressValue.textContent = addressSelect.selectedOptions[0]?.textContent || 'No default address';
    };
    addressSelect.onchange = updateAddressValue;
    updateAddressValue();
    document.getElementById('customerDetailStatusButton').textContent =
      customer.is_active ? 'Deactivate' : 'Activate';
    document.getElementById('customerStatusLabel').innerHTML =
      `<span class="customer-status ${customer.is_active ? 'is-active' : 'is-inactive'}">${customer.is_active ? 'Active' : 'Inactive'}</span>`;
    document.getElementById('customerMetrics').innerHTML = `
      <button class="customer-metric-card" type="button" data-customer-metric="orders">
        <span>Orders</span><strong>${Number(detail.metrics.order_count || 0).toLocaleString()}</strong>
      </button>
      <button class="customer-metric-card" type="button" data-customer-metric="cancelled_orders">
        <span>Cancelled orders</span><strong>${Number(detail.metrics.cancelled_order_count || 0).toLocaleString()}</strong>
      </button>
      <button class="customer-metric-card" type="button" data-customer-metric="loyalty_points">
        <span>Loyalty points</span><strong>${Number(detail.metrics.loyalty_points || 0).toLocaleString()}</strong>
      </button>
      <button class="customer-metric-card" type="button" data-customer-metric="average_rating">
        <span>Average rating</span><strong>${detail.metrics.average_rating == null ? '—' : `${Number(detail.metrics.average_rating).toFixed(1)} / 5`}</strong>
      </button>
    `;
    document.getElementById('customerAddresses').innerHTML = detail.addresses.length
      ? `<ul class="customer-address-list">${detail.addresses.map((address) =>
        `<li>${escapeHtml(address.address_text)}${address.address_id === customer.default_address_id ? ' <strong>(Default)</strong>' : ''}</li>`
      ).join('')}</ul>`
      : '<p class="customer-empty-detail">No saved addresses.</p>';
    document.getElementById('customerOrders').innerHTML = detail.orders.length
      ? `<div class="customer-order-cards">${detail.orders.map((order) => `
          <article class="customer-order-card">
            <p><strong>Order:</strong> #${escapeHtml(order.order_id)}</p>
            <p><strong>Status:</strong> ${escapeHtml(order.order_status || '-')}</p>
            <p><strong>Total:</strong> ${escapeHtml(formatCurrency(order.total_amount || 0))}</p>
            <p><strong>Placed:</strong> ${escapeHtml(formatDate(order.created_at))}</p>
          </article>
        `).join('')}</div>`
      : '<p class="customer-empty-detail">No recorded orders.</p>';
    document.getElementById('customerAuditTrail').innerHTML = detail.audit_trail.length
      ? detail.audit_trail.map((entry) => renderCustomerAuditEntry(entry, detail.addresses)).join('')
      : '<p class="customer-empty-detail">No recorded changes.</p>';
    customerDetailMessage.textContent = '';
  } catch (error) {
    customerDetailMessage.textContent = `Unable to load customer: ${error.message}`;
  }
}

function renderCustomerAuditEntry(entry, addresses = []) {
  const oldData = entry.old_data || {};
  const newData = entry.new_data || {};
  const fieldLabels = {
    name: 'Name',
    mobile: 'Mobile',
    email: 'Email',
    default_address_id: 'Default address',
    loyalty_points: 'Loyalty points',
    is_active: 'Status',
    is_deleted: 'Removed',
  };
  const addressLabels = new Map(
    addresses.map((address) => [String(address.address_id), address.address_text]),
  );
  const fields = Object.keys(fieldLabels).filter(
    (field) => JSON.stringify(oldData[field]) !== JSON.stringify(newData[field]),
  );
  const formatAuditValue = (field, value) => {
    if (field === 'is_active') return value ? 'Active' : 'Inactive';
    if (field === 'is_deleted') return value ? 'Yes' : 'No';
    if (field === 'default_address_id') {
      if (value === null || value === undefined || value === '') return 'None';
      return addressLabels.get(String(value)) || 'Address unavailable';
    }
    if (value === null || value === undefined || value === '') return 'None';
    return String(value);
  };
  const actionLabels = {
    'customer.updated': 'Customer updated',
    'customer.status_changed': 'Status changed',
    'customer.activated': 'Status changed',
    'customer.deactivated': 'Status changed',
    'customer.deleted': 'Customer removed',
  };
  const action = actionLabels[entry.action] || 'Customer updated';
  const changes = fields.map((field) => `
    <li>${fieldLabels[field]}: ${escapeHtml(formatAuditValue(field, oldData[field]))} → ${escapeHtml(formatAuditValue(field, newData[field]))}</li>
  `).join('');
  return `
    <article class="customer-audit-entry">
      <time>${escapeHtml(formatDateTime(entry.created_at))}</time>
      <strong>${escapeHtml(action)}</strong>
      ${changes ? `<ul>${changes}</ul>` : ''}
      <span>${escapeHtml(entry.changed_by_name || entry.added_by || 'Admin')}</span>
    </article>
  `;
}

function closeCustomerDetail() {
  customerDetailPanel.classList.remove('is-open');
  customerDetailPanel.classList.add('hidden');
  document.getElementById('customerDetailBackdrop').classList.add('hidden');
  state.customerDetailId = null;
  state.customerDetail = null;
}

document.getElementById('customerMetrics').addEventListener('click', async (event) => {
  const card = event.target.closest('[data-customer-metric]');
  if (!card || state.customerDetailId === null) return;

  try {
    if (['orders', 'cancelled_orders'].includes(card.dataset.customerMetric)) {
      await openCustomerOrderList(
        card.dataset.customerMetric === 'cancelled_orders' ? 'cancelled' : 'orders',
        state.customerDetailId,
      );
      return;
    }
    const detail = await apiRequest(
      `/admin/customers/${encodeURIComponent(state.customerDetailId)}/history/${encodeURIComponent(card.dataset.customerMetric)}`,
    );
    renderDetail(detail);
  } catch (error) {
    customerDetailMessage.textContent = `Unable to load customer history: ${error.message}`;
  }
});

async function changeCustomerStatus(customerId, isActive) {
  await apiRequest(`/admin/customers/${encodeURIComponent(customerId)}/status`, {
    method: 'PUT',
    body: JSON.stringify({ is_active: isActive }),
  });
  if (state.customerDetailId === customerId) {
    await openCustomerDetail(customerId);
  }
  await refreshCustomerData();
}

async function deleteCustomer(customerId) {
  if (!window.confirm('Remove this customer?')) return;
  await apiRequest(`/admin/customers/${encodeURIComponent(customerId)}`, { method: 'DELETE' });
  if (state.customerDetailId === customerId) {
    closeCustomerDetail();
  }
  await refreshCustomerData();
}

document.querySelectorAll('.nav-item[data-section]').forEach((button) => {
  button.addEventListener('click', async () => {
    setActiveSection(button.dataset.section);
    if (button.dataset.section === 'customersSection') await loadCustomerSection();
    if (button.dataset.section === 'dashboardSection') await loadDashboard();
  });
});

document.getElementById('customerFilters').addEventListener('submit', async (event) => {
  event.preventDefault();
  state.customerFilters = {
    search: document.getElementById('customerSearch').value.trim(),
    status: document.getElementById('customerStatusFilter').value,
    joined_from: document.getElementById('customerJoinedFrom').value,
    joined_to: document.getElementById('customerJoinedTo').value,
  };
  state.customerPage = 1;
  await loadCustomers();
});

document.getElementById('clearCustomerFiltersButton').addEventListener('click', async () => {
  document.getElementById('customerSearch').value = '';
  document.getElementById('customerStatusFilter').value = 'all';
  document.getElementById('customerJoinedFrom').value = '';
  document.getElementById('customerJoinedTo').value = '';
  state.customerFilters = {
    search: '',
    status: 'all',
    joined_from: '',
    joined_to: '',
  };
  state.customerPage = 1;
  await loadCustomers();
});

document.getElementById('customerPreviousPage').addEventListener('click', async () => {
  if (state.customerPage > 1) {
    state.customerPage -= 1;
    await loadCustomers();
  }
});

document.getElementById('customerNextPage').addEventListener('click', async () => {
  if (state.customerPage < state.customerTotalPages) {
    state.customerPage += 1;
    await loadCustomers();
  }
});

document.getElementById('refreshCustomersButton').addEventListener('click', async () => {
  document.getElementById('customerSearch').value = '';
  document.getElementById('customerStatusFilter').value = 'all';
  document.getElementById('customerJoinedFrom').value = '';
  document.getElementById('customerJoinedTo').value = '';
  state.customerFilters = {
    search: '',
    status: 'all',
    joined_from: '',
    joined_to: '',
  };
  state.customerPage = 1;
  await loadCustomerSection();
});

document.getElementById('cancelCustomerButton').addEventListener('click', closeCustomerDetail);
document.getElementById('closeCustomerDetailButton').addEventListener('click', closeCustomerDetail);
document.getElementById('customerDetailBackdrop').addEventListener('click', closeCustomerDetail);

document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  closeCustomerDetail();
  closeQuickSearch();
  adminMenu.classList.add('hidden');
  document.getElementById('adminAvatarButton').setAttribute('aria-expanded', 'false');
  modal.classList.add('hidden');
  modal.setAttribute('aria-hidden', 'true');
});

customerEditForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (state.customerDetailId === null) return;
  const payload = {
    name: document.getElementById('customerEditName').value.trim(),
    mobile: document.getElementById('customerEditMobile').value.trim() || null,
    email: document.getElementById('customerEditEmail').value.trim() || null,
    default_address_id: document.getElementById('customerEditAddress').value
      ? Number(document.getElementById('customerEditAddress').value)
      : null,
  };
  try {
    await apiRequest(`/admin/customers/${encodeURIComponent(state.customerDetailId)}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    customerDetailMessage.textContent = 'Customer changes saved.';
    await openCustomerDetail(state.customerDetailId);
    await refreshCustomerData();
  } catch (error) {
    customerDetailMessage.textContent = `Unable to save customer: ${error.message}`;
  }
});

document.getElementById('customerDetailStatusButton').addEventListener('click', async () => {
  if (!state.customerDetail) return;
  try {
    await changeCustomerStatus(
      state.customerDetailId,
      !state.customerDetail.customer.is_active,
    );
  } catch (error) {
    customerDetailMessage.textContent = `Unable to change status: ${error.message}`;
  }
});

document.getElementById('customerDetailDeleteButton').addEventListener('click', async () => {
  if (!state.customerDetailId) return;
  try {
    await deleteCustomer(state.customerDetailId);
  } catch (error) {
    customerDetailMessage.textContent = `Unable to remove customer: ${error.message}`;
  }
});

modalBody.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-reactivate-customer]');
  if (!button) return;
  try {
    await changeCustomerStatus(Number(button.dataset.reactivateCustomer), true);
    const key = currentKpiDetail?.key;
    if (key) {
      const query = new URLSearchParams({
        page: String(currentKpiDetail.page || 1),
        page_size: String(currentKpiDetail.page_size || 25),
      });
      if (currentKpiDetail.search) query.set('search', currentKpiDetail.search);
      const refreshed = await apiRequest(
        `/admin/customers/kpi/${encodeURIComponent(key)}?${query.toString()}`,
      );
      renderDetail(refreshed);
    }
  } catch (error) {
    modalBody.insertAdjacentHTML('afterbegin', `<p class="notification-unavailable">${escapeHtml(error.message)}</p>`);
  }
});

document.getElementById('logoutButton').addEventListener('click', async () => {
  const logoutButton = document.getElementById('logoutButton');
  const logoutMessage = document.getElementById('logoutMessage');
  logoutButton.disabled = true;
  logoutMessage.textContent = '';
  try {
    await apiRequest('/admin/logout', { method: 'POST' });
    state.token = '';
    localStorage.removeItem('vigo_admin_token');
    showLogin();
  } catch (error) {
    logoutMessage.textContent = `Unable to log out: ${error.message}`;
  } finally {
    logoutButton.disabled = false;
  }
});

document.querySelectorAll('.otp-digit').forEach((input, index, arr) => {
  input.addEventListener('input', (event) => {
    const value = event.target.value.replace(/\D/g, '').slice(0, 1);
    event.target.value = value;
    if (value && index < arr.length - 1) {
      arr[index + 1].focus();
    }
  });

  input.addEventListener('keydown', (event) => {
    if (event.key === 'Backspace' && !input.value && index > 0) {
      arr[index - 1].focus();
    }
  });
});

if (state.token) {
  showDashboard();
  loadDashboard();
}
