
(() => {
  'use strict';

  const PAGE_SIZE = 10;
  const pages = { partners: 1, restaurants: 1, orders: 1 };
  const totals = { partners: 0, restaurants: 0, orders: 0 };
  const totalPages = { partners: 1, restaurants: 1, orders: 1 };
let searchTimer;
let franchiseeSearchTimer;
let franchiseeOptions = [];
  let dispatchRiders = [];
  const operationsApi = '/api/admin/delivery-operations';

  const $ = (id) => document.getElementById(id);

  function escape(value) {
    if (typeof escapeHtml === 'function') return escapeHtml(value ?? '');
    return String(value ?? '').replace(/[&<>"']/g, (char) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;',
      '"': '&quot;', "'": '&#39;'
    })[char]);
  }

  function message(id, text, isError = false) {
    const element = $(id);
    if (!element) return;
    element.textContent = text;
    element.style.color = isError ? '#b42318' : '';
  }

  async function request(path) {
    if (typeof apiRequest !== 'function') {
      throw new Error('The existing app.js API helper was not found.');
    }
    return apiRequest(path, { credentials: 'same-origin' });
  }

  function queryString(values) {
    const params = new URLSearchParams();
    Object.entries(values).forEach(([key, value]) => {
      if (value !== '' && value !== null && value !== undefined) {
        params.set(key, String(value));
      }
    });
    return params.toString();
  }

  function getSearch(id) {
    return $(id)?.value?.trim() || '';
  }

  function showValue(value) {
    return escape(value ?? '—');
  }

  function money(value) {
    const amount = Number(value ?? 0);
    if (typeof formatCurrency === 'function' && Number.isFinite(amount)) {
      return escape(formatCurrency(amount));
    }
    return Number.isFinite(amount) ? amount.toFixed(2) : '—';
  }

  function dateValue(value) {
    if (!value) return '—';
    if (typeof formatDateTime === 'function') {
      return escape(formatDateTime(value));
    }
    return showValue(value);
  }

  function updatePagination(key, labelId, previousId, nextId) {
    const label = $(labelId);
    const previous = $(previousId);
    const next = $(nextId);

    if (label) {
      label.textContent =
        `Page ${pages[key]} of ${totalPages[key]} · ${totals[key]} records`;
    }
    if (previous) previous.disabled = pages[key] <= 1;
    if (next) next.disabled = pages[key] >= totalPages[key];
  }
function renderFranchiseeOptions(searchTerm = '') {
  const select = $('deliveryPartnerFranchiseeFilter');
  if (!select) return;

  const selectedValue = select.value;
  const search = searchTerm.trim().toLowerCase();

  let filteredItems = franchiseeOptions.filter(item =>
    String(item.name || '').toLowerCase().includes(search)
  );

  // Preserve the currently selected franchisee.
  const selectedItem = franchiseeOptions.find(
    item => String(item.id) === selectedValue
  );

  if (
    selectedItem &&
    !filteredItems.some(item => String(item.id) === selectedValue)
  ) {
    filteredItems.unshift(selectedItem);
  }

  select.innerHTML =
    '<option value="">All Franchisees</option>' +
    filteredItems.map(item => `
      <option value="${escape(item.id)}">
        ${escape(item.name)}
      </option>
    `).join('');

  select.value = selectedValue;
}

function renderOnboardingFranchiseeOptions() {
  const select = $('newRiderFranchisee');
  if (!select) return;
  const selectedValue = select.value;
  select.innerHTML = '<option value="">Select franchisee</option>' +
    franchiseeOptions.map((item) => `
      <option value="${escape(item.id)}">${escape(item.name)}</option>
    `).join('');
  select.value = selectedValue;
}

async function loadFranchiseeOptions() {
  try {
    const items = await request(
      '/api/admin/delivery-partners/franchisee-options'
    );

    franchiseeOptions = items || [];

    renderFranchiseeOptions(
      getSearch('deliveryPartnerFranchiseeSearch')
    );
    renderOnboardingFranchiseeOptions();

  } catch (error) {
    message(
      'deliveryPartnersMessage',
      error.message || 'Unable to load franchisees.',
      true
    );
  }
}

async function loadRiderOptions() {
  const select = $('deliveryPartnerRiderFilter');
  if (!select) return;

  const franchiseeId = getSearch('deliveryPartnerFranchiseeFilter');

  const params = queryString({
    franchisee_id: franchiseeId
  });

  try {
    const items = await request(
      `/api/admin/delivery-partners/rider-options?${params}`
    );

    select.innerHTML =
      '<option value="">All Riders</option>' +
      (items || []).map(item => `
        <option value="${escape(item.rider_id)}">
          ${escape(item.rider_id)}
        </option>
      `).join('');

  } catch (error) {
    message(
      'deliveryPartnersMessage',
      error.message || 'Unable to load Rider IDs.',
      true
    );
  }
}

async function loadPartners() {
  const body = $('deliveryPartnersTableBody');
  if (!body) return;

const franchiseeId = getSearch('deliveryPartnerFranchiseeFilter');
const riderId = getSearch('deliveryPartnerRiderFilter');


  const params = queryString({
  franchisee_id: franchiseeId,
  rider_id: riderId,
  search: getSearch('deliveryPartnerSearch'),
  status: getSearch('deliveryPartnerStatus'),
  verification_status: getSearch('deliveryPartnerVerification'),
  page: pages.partners,
  page_size: PAGE_SIZE
});

  body.innerHTML = '<tr><td colspan="10">Loading delivery partners…</td></tr>';
  message('deliveryPartnersMessage', '');

  try {
    const data = await request(`/api/admin/delivery-partners?${params}`);
    const items = data.items || [];

    totals.partners = Number(data.total || 0);
    totalPages.partners = Math.max(1, Number(data.total_pages || 1));


body.innerHTML = items.length ? items.map((item) => `
  <tr>
    <td>${showValue(item.franchisee_name)}</td>
    <td>${showValue(item.partner_id)}</td>
    <td>${showValue(item.rider_id)}</td>
    <td>${showValue(item.full_name)}</td>
    <td>${showValue(item.mobile_number)}</td>
    <td>${showValue(item.vehicle_type)}${item.vehicle_number ? ` / ${showValue(item.vehicle_number)}` : ''}</td>
    <td>${showValue(item.city)}</td>
    <td>${showValue(item.status)}</td>
    <td>${showValue(item.verification_status)}</td>
    <td>
      <select
        class="rider-status-update"
        id="riderStatus-${escape(item.partner_id)}">
        ${['ACTIVE', 'INACTIVE', 'PENDING', 'SUSPENDED'].map(status =>
          `<option value="${status}" ${item.status === status ? 'selected' : ''}>${status}</option>`
        ).join('')}
      </select>

      <select
        class="rider-verification-update"
        id="riderVerification-${escape(item.partner_id)}">
        ${['PENDING', 'VERIFIED', 'REJECTED'].map(status =>
          `<option value="${status}" ${item.verification_status === status ? 'selected' : ''}>${status}</option>`
        ).join('')}
      </select>

      <button
        type="button"
        class="secondary-btn rider-update-btn"
        data-partner-id="${escape(item.partner_id)}"
        data-franchisee-id="${escape(item.franchisee_id)}">
        Update
      </button>
      ${item.status !== 'ACTIVE' || item.verification_status !== 'VERIFIED' ? `
        <button
          type="button"
          class="secondary-btn rider-approve-btn"
          data-partner-id="${escape(item.partner_id)}"
          data-franchisee-id="${escape(item.franchisee_id)}">
          Approve
        </button>
      ` : ''}
    </td>
  </tr>
`).join('') : '<tr><td colspan="10">No delivery partners found.</td></tr>';

    updatePagination(
      'partners', 'deliveryPartnersPaginationLabel',
      'deliveryPartnersPrevious', 'deliveryPartnersNext'
    );
  } catch (error) {
    body.innerHTML = '<tr><td colspan="10">Could not load delivery partners.</td></tr>';
    message('deliveryPartnersMessage', error.message || 'Request failed.', true);
  }
}

async function loadRestaurants() {
  const body = $('restaurantsTableBody');
  if (!body) return;

  const params = queryString({
    search: getSearch('restaurantSearch'),
    status: getSearch('restaurantStatus'),
    page: pages.restaurants,
    page_size: PAGE_SIZE
  });

  body.innerHTML = '<tr><td colspan="7">Loading restaurants…</td></tr>';
  message('restaurantsMessage', '');

  try {
    const data = await request(`/api/admin/restaurants?${params}`);
    const items = data.items || [];

    totals.restaurants = Number(data.total || 0);
    totalPages.restaurants = Math.max(1, Number(data.total_pages || 1));

    body.innerHTML = items.length ? items.map((item) => `
      <tr>
        <td>${showValue(item.name)}</td>
        <td>${showValue(item.phone)}</td>
        <td>${showValue(item.email)}</td>
        <td>${showValue(item.city)}</td>
        <td>${showValue(item.status)}</td>
        <td>${item.is_active ? 'Yes' : 'No'}</td>
        <td>
          <select class="restaurant-status-update"
                  id="restaurantStatus-${escape(item.id)}">
            <option value="ACTIVE" ${item.status === 'ACTIVE' ? 'selected' : ''}>ACTIVE</option>
            <option value="OFFLINE" ${item.status === 'OFFLINE' ? 'selected' : ''}>OFFLINE</option>
            <option value="INACTIVE" ${item.status === 'INACTIVE' ? 'selected' : ''}>INACTIVE</option>
            <option value="PENDING" ${item.status === 'PENDING' ? 'selected' : ''}>PENDING</option>
            <option value="APPROVED" ${item.status === 'APPROVED' ? 'selected' : ''}>APPROVED</option>
            <option value="REJECTED" ${item.status === 'REJECTED' ? 'selected' : ''}>REJECTED</option>
          </select>
          <button type="button"
                  class="secondary-btn restaurant-update-btn"
                  data-restaurant-id="${escape(item.id)}">
            Update
          </button>
        </td>
      </tr>
    `).join('') : '<tr><td colspan="7">No restaurants found.</td></tr>';

    updatePagination(
      'restaurants', 'restaurantsPaginationLabel',
      'restaurantsPrevious', 'restaurantsNext'
    );
  } catch (error) {
    body.innerHTML = '<tr><td colspan="7">Could not load restaurants.</td></tr>';
    message('restaurantsMessage', error.message || 'Request failed.', true);
  }
}

async function updateRider(partnerId, franchiseeId) {
  const statusInput = $(`riderStatus-${partnerId}`);
  const verificationInput = $(`riderVerification-${partnerId}`);

  if (!statusInput || !verificationInput || !franchiseeId) {
    message('deliveryPartnersMessage', 'Missing partner or franchisee details.', true);
    return;
  }

  try {
    message('deliveryPartnersMessage', 'Updating delivery partner...');

    await apiRequest(
      `/api/admin/delivery-partners/${encodeURIComponent(partnerId)}/status?franchisee_id=${encodeURIComponent(franchiseeId)}`,
      {
        method: 'PATCH',
        body: JSON.stringify({
          status: statusInput.value,
        })
      }
    );

    await apiRequest(
      `/api/admin/delivery-partners/${encodeURIComponent(partnerId)}/verification?franchisee_id=${encodeURIComponent(franchiseeId)}`,
      {
        method: 'PATCH',
        body: JSON.stringify({
          verification_status: verificationInput.value
        })
      }
    );

    message('deliveryPartnersMessage', 'Delivery partner updated successfully.');
    await loadPartners();

  } catch (error) {
    message(
      'deliveryPartnersMessage',
      error.message || 'Unable to update delivery partner.',
      true
    );
  }
}

async function createRiderOnboarding(event) {
  event.preventDefault();
  try {
    await apiRequest('/api/admin/delivery-partners', {
      method: 'POST',
      body: JSON.stringify({
        franchisee_id: $('newRiderFranchisee').value,
        full_name: getSearch('newRiderName'),
        mobile_number: getSearch('newRiderMobile'),
        email: getSearch('newRiderEmail') || null,
        vehicle_type: getSearch('newRiderVehicleType') || null,
        vehicle_number: getSearch('newRiderVehicleNumber') || null,
        city: getSearch('newRiderCity') || null,
        service_area: $('newRiderServiceArea').value.trim() || null
      })
    });
    $('riderOnboardingForm').reset();
    message('deliveryPartnersMessage', 'Rider onboarding submitted for approval.');
    await loadPartners();
  } catch (error) {
    message('deliveryPartnersMessage', error.message || 'Unable to submit rider onboarding.', true);
  }
}

async function approveRider(partnerId, franchiseeId) {
  try {
    await apiRequest(
      `/api/admin/delivery-partners/${encodeURIComponent(partnerId)}/approve?franchisee_id=${encodeURIComponent(franchiseeId)}`,
      { method: 'PATCH' }
    );
    message('deliveryPartnersMessage', 'Rider onboarding approved.');
    await loadPartners();
    await loadDispatchRiders();
    await loadDispatchOrders();
  } catch (error) {
    message('deliveryPartnersMessage', error.message || 'Unable to approve rider.', true);
  }
}


async function updateRestaurantStatus(restaurantId) {
  const statusInput = $(`restaurantStatus-${restaurantId}`);

  if (!statusInput) return;

  const newStatus = statusInput.value;

  try {
    message('restaurantsMessage', 'Updating restaurant status...');

    await apiRequest(`/api/admin/restaurants/${encodeURIComponent(restaurantId)}`, {
      method: 'PUT',
      body: JSON.stringify({
        status: newStatus
      })
    });

    message('restaurantsMessage', 'Restaurant status updated successfully.');
    await loadRestaurants();

  } catch (error) {
    message(
      'restaurantsMessage',
      error.message || 'Unable to update restaurant status.',
      true
    );
  }
}


  async function loadOrders() {
    const body = $('moduleOrdersTableBody');
    if (!body) return;

    const params = queryString({
      search: getSearch('moduleOrderSearch'),
      status: getSearch('moduleOrderStatus'),
      page: pages.orders,
      page_size: PAGE_SIZE
    });

    body.innerHTML = '<tr><td colspan="9">Loading orders…</td></tr>';
    message('moduleOrdersMessage', '');

    try {
      const data = await request(`/api/admin/orders?${params}`);
      const items = data.items || [];
      totals.orders = Number(data.total || 0);
      totalPages.orders = Math.max(1, Number(data.total_pages || 1));

      body.innerHTML = items.length ? items.map((item) => `
        <tr>
          <td>${showValue(item.order_id)}</td>
          <td>${showValue(item.customer_id)}</td>
          <td>${showValue(item.restaurant_id)}</td>
          <td>${showValue(item.delivery_partner_name)}</td>
          <td>${money(item.total_amount ?? item.grand_total ?? item.amount)}</td>
          <td>
            <input
              type="number"
              min="0"
              step="0.01"
              aria-label="Delivery fee for order ${escape(item.order_id)}"
              id="orderFee-${escape(item.order_id)}"
              value="${escape(item.delivery_charge ?? 0)}"
            />
            <button
              type="button"
              class="secondary-btn order-fee-update-btn"
              data-order-id="${escape(item.order_id)}"
            >Save fee</button>
          </td>
          <td>${showValue(item.order_status ?? item.status)}</td>
          <td>${dateValue(item.created_at)}</td>
          <td>
  <select
    class="order-status-update"
    id="orderStatus-${escape(item.order_id)}"
  >
    <option value="PLACED" ${(item.order_status ?? item.status) === 'PLACED' ? 'selected' : ''}>PLACED</option>
    <option value="CONFIRMED" ${(item.order_status ?? item.status) === 'CONFIRMED' ? 'selected' : ''}>CONFIRMED</option>
    <option value="PREPARING" ${(item.order_status ?? item.status) === 'PREPARING' ? 'selected' : ''}>PREPARING</option>
    <option value="READY_FOR_PICKUP" ${(item.order_status ?? item.status) === 'READY_FOR_PICKUP' ? 'selected' : ''}>READY_FOR_PICKUP</option>
    <option value="OUT_FOR_DELIVERY" ${(item.order_status ?? item.status) === 'OUT_FOR_DELIVERY' ? 'selected' : ''}>OUT_FOR_DELIVERY</option>
    <option value="DELIVERED" ${(item.order_status ?? item.status) === 'DELIVERED' ? 'selected' : ''}>DELIVERED</option>
    <option value="CANCELLED" ${(item.order_status ?? item.status) === 'CANCELLED' ? 'selected' : ''}>CANCELLED</option>
    <option value="REJECTED" ${(item.order_status ?? item.status) === 'REJECTED' ? 'selected' : ''}>REJECTED</option>
  </select>

  <button
    type="button"
    class="secondary-btn order-update-btn"
    data-order-id="${escape(item.order_id)}"
  >
    Update
  </button>
</td>
        </tr>
      `).join('') : '<tr><td colspan="9">No orders found.</td></tr>';

      updatePagination(
        'orders', 'moduleOrdersPaginationLabel',
        'moduleOrdersPrevious', 'moduleOrdersNext'
      );
    } catch (error) {
      body.innerHTML = '<tr><td colspan="9">Could not load orders.</td></tr>';
      message('moduleOrdersMessage', error.message || 'Request failed.', true);
    }
  }

  async function updateDeliveryFee(orderId) {
    const feeInput = $(`orderFee-${orderId}`);
    const fee = Number(feeInput?.value);
    if (!feeInput || !Number.isFinite(fee) || fee < 0) {
      message('moduleOrdersMessage', 'Enter a valid non-negative delivery fee.', true);
      return;
    }

    try {
      await apiRequest(`/api/admin/orders/${encodeURIComponent(orderId)}`, {
        method: 'PUT',
        body: JSON.stringify({ delivery_charge: fee })
      });
      message('moduleOrdersMessage', 'Delivery fee updated.');
      await loadOrders();
    } catch (error) {
      message('moduleOrdersMessage', error.message || 'Unable to update delivery fee.', true);
    }
  }

  async function loadDispatchSettings() {
    message('dispatchMessage', '');
    try {
      const settings = await request(`${operationsApi}/settings`);
      message('dispatchMessage', '');
      $('dispatchMode').value = settings.configured ? settings.dispatch_mode : '';
      $('maxActiveOrders').value = settings.configured ? settings.max_active_orders : '';
      if (!settings.configured) {
        message('dispatchMessage', 'Choose and save the dispatch rule and rider order limit to configure operations.');
      }
    } catch (error) {
      message('dispatchMessage', error.message || 'Unable to load dispatch settings.', true);
    }
  }

  async function loadDispatchRiders() {
    message('dispatchMessage', '');
    message('payoutsMessage', '');
    message('ticketsMessage', '');
    dispatchRiders = [];
    try {
      dispatchRiders = await request(`${operationsApi}/riders`) || [];
      message('dispatchMessage', '');
      message('payoutsMessage', '');
      message('ticketsMessage', '');
      const options = dispatchRiders.map((rider) => `
        <option value="${escape(rider.rider_id)}">
          ${escape(rider.full_name)} · #${escape(rider.rider_id)}
        </option>
      `).join('');
      $('payoutRider').innerHTML = '<option value="">Select rider</option>' + options;
      $('ticketRider').innerHTML = '<option value="">No rider linked</option>' + options;
    } catch (error) {
      $('payoutRider').innerHTML = '<option value="">Select rider</option>';
      $('ticketRider').innerHTML = '<option value="">No rider linked</option>';
      message('dispatchMessage', error.message || 'Unable to load approved riders.', true);
      message('payoutsMessage', error.message || 'Unable to load approved riders.', true);
      message('ticketsMessage', error.message || 'Unable to load approved riders.', true);
    }
  }

  async function loadDispatchOrders() {
    const body = $('dispatchOrdersTableBody');
    if (!body) return;
    message('dispatchMessage', '');
    body.innerHTML = '<tr><td colspan="5">Loading active deliveries…</td></tr>';
    try {
      const orders = await request(`${operationsApi}/orders`);
      message('dispatchMessage', '');
      body.innerHTML = orders.length ? orders.map((order) => `
        <tr>
          <td>${showValue(order.order_id)}</td>
          <td>${showValue(order.order_status)}</td>
          <td>${order.rider_name ? `${showValue(order.rider_name)} · #${showValue(order.rider_id)}` : 'Unassigned'}</td>
          <td>${dateValue(order.created_at)}</td>
          <td>
            <select id="dispatchRider-${escape(order.order_id)}" aria-label="Reassign order ${escape(order.order_id)}">
              <option value="">Select approved rider</option>
              ${dispatchRiders.map((rider) => `
                <option value="${escape(rider.rider_id)}" ${Number(order.rider_id) === Number(rider.rider_id) ? 'selected' : ''}>
                  ${escape(rider.full_name)} · #${escape(rider.rider_id)}
                </option>
              `).join('')}
            </select>
            <button type="button" class="secondary-btn order-reassign-btn" data-order-id="${escape(order.order_id)}">Reassign</button>
          </td>
        </tr>
      `).join('') : '<tr><td colspan="5">No active deliveries need dispatch.</td></tr>';
    } catch (error) {
      body.innerHTML = '<tr><td colspan="5">Could not load active deliveries.</td></tr>';
      message('dispatchMessage', error.message || 'Unable to load active deliveries.', true);
    }
  }

  async function reassignOrder(orderId) {
    const riderId = $(`dispatchRider-${orderId}`)?.value;
    if (!riderId) {
      message('dispatchMessage', 'Select an approved rider before reassigning.', true);
      return;
    }
    try {
      await apiRequest(`${operationsApi}/orders/${encodeURIComponent(orderId)}/reassign`, {
        method: 'PATCH',
        body: JSON.stringify({ rider_id: Number(riderId) })
      });
      message('dispatchMessage', `Order ${orderId} reassigned successfully.`);
      await loadDispatchOrders();
      await loadOrders();
    } catch (error) {
      message('dispatchMessage', error.message || 'Unable to reassign order.', true);
    }
  }

  async function saveDispatchSettings(event) {
    event.preventDefault();
    const maxActiveOrders = Number($('maxActiveOrders').value);
    if (!Number.isInteger(maxActiveOrders) || maxActiveOrders < 1) {
      message('dispatchMessage', 'Maximum active orders must be a positive whole number.', true);
      return;
    }
    try {
      const settings = await apiRequest(`${operationsApi}/settings`, {
        method: 'PUT',
        body: JSON.stringify({
          dispatch_mode: $('dispatchMode').value,
          max_active_orders: maxActiveOrders
        })
      });
      $('dispatchMode').value = settings.dispatch_mode;
      $('maxActiveOrders').value = settings.max_active_orders;
      message('dispatchMessage', 'Dispatch settings saved.');
    } catch (error) {
      message('dispatchMessage', error.message || 'Unable to save dispatch settings.', true);
    }
  }

  async function loadPayouts() {
    const body = $('payoutsTableBody');
    if (!body) return;
    message('payoutsMessage', '');
    body.innerHTML = '<tr><td colspan="7">Loading payouts…</td></tr>';
    try {
      const payouts = await request(`${operationsApi}/payouts`);
      message('payoutsMessage', '');
      body.innerHTML = payouts.length ? payouts.map((payout) => `
        <tr>
          <td>${showValue(payout.payout_id)}</td>
          <td>${showValue(payout.rider_name)} · #${showValue(payout.rider_id)}</td>
          <td>${money(payout.amount)}</td>
          <td>${showValue(payout.period_start)} – ${showValue(payout.period_end)}</td>
          <td>${showValue(payout.status)}</td>
          <td>${showValue(payout.reference)}</td>
          <td>${payout.status === 'PENDING' ? `
            <button type="button" class="secondary-btn payout-paid-btn" data-payout-id="${escape(payout.payout_id)}">Mark paid</button>
          ` : (payout.paid_at ? dateValue(payout.paid_at) : showValue(payout.paid_by))}</td>
        </tr>
      `).join('') : '<tr><td colspan="7">No rider payouts recorded.</td></tr>';
    } catch (error) {
      body.innerHTML = '<tr><td colspan="7">Could not load payouts.</td></tr>';
      message('payoutsMessage', error.message || 'Unable to load payouts.', true);
    }
  }

  async function createPayout(event) {
    event.preventDefault();
    try {
      await apiRequest(`${operationsApi}/payouts`, {
        method: 'POST',
        body: JSON.stringify({
          rider_id: Number($('payoutRider').value),
          amount: Number($('payoutAmount').value),
          period_start: $('payoutPeriodStart').value,
          period_end: $('payoutPeriodEnd').value,
          reference: getSearch('payoutReference') || null
        })
      });
      $('payoutForm').reset();
      message('payoutsMessage', 'Rider payout recorded.');
      await loadPayouts();
    } catch (error) {
      message('payoutsMessage', error.message || 'Unable to record payout.', true);
    }
  }

  async function markPayoutPaid(payoutId) {
    try {
      await apiRequest(`${operationsApi}/payouts/${encodeURIComponent(payoutId)}/paid`, {
        method: 'PATCH'
      });
      message('payoutsMessage', 'Payout marked as paid.');
      await loadPayouts();
    } catch (error) {
      message('payoutsMessage', error.message || 'Unable to update payout.', true);
    }
  }

  async function loadSupportTickets() {
    const body = $('ticketsTableBody');
    if (!body) return;
    message('ticketsMessage', '');
    body.innerHTML = '<tr><td colspan="8">Loading support tickets…</td></tr>';
    try {
      const tickets = await request(`${operationsApi}/support-tickets`);
      message('ticketsMessage', '');
      body.innerHTML = tickets.length ? tickets.map((ticket) => `
        <tr>
          <td>${showValue(ticket.ticket_id)}</td>
          <td title="${escape(ticket.description)}">${showValue(ticket.subject)}</td>
          <td>${ticket.rider_id ? `${showValue(ticket.rider_name)} · #${showValue(ticket.rider_id)}` : '—'}</td>
          <td>${showValue(ticket.order_id)}</td>
          <td>${showValue(ticket.priority)}</td>
          <td>${showValue(ticket.status)}</td>
          <td>${dateValue(ticket.created_at)}</td>
          <td>
            <select id="ticketStatus-${escape(ticket.ticket_id)}">
              ${['OPEN', 'IN_PROGRESS', 'RESOLVED'].map((status) =>
                `<option value="${status}" ${ticket.status === status ? 'selected' : ''}>${status.replace('_', ' ')}</option>`
              ).join('')}
            </select>
            <button type="button" class="secondary-btn ticket-update-btn" data-ticket-id="${escape(ticket.ticket_id)}">Update</button>
          </td>
        </tr>
      `).join('') : '<tr><td colspan="8">No support tickets recorded.</td></tr>';
    } catch (error) {
      body.innerHTML = '<tr><td colspan="8">Could not load support tickets.</td></tr>';
      message('ticketsMessage', error.message || 'Unable to load support tickets.', true);
    }
  }

  async function createSupportTicket(event) {
    event.preventDefault();
    try {
      await apiRequest(`${operationsApi}/support-tickets`, {
        method: 'POST',
        body: JSON.stringify({
          rider_id: $('ticketRider').value ? Number($('ticketRider').value) : null,
          order_id: $('ticketOrderId').value.trim() || null,
          subject: getSearch('ticketSubject'),
          description: $('ticketDescription').value.trim(),
          priority: $('ticketPriority').value
        })
      });
      $('supportTicketForm').reset();
      $('ticketPriority').value = 'NORMAL';
      message('ticketsMessage', 'Support ticket created.');
      await loadSupportTickets();
    } catch (error) {
      message('ticketsMessage', error.message || 'Unable to create support ticket.', true);
    }
  }

  async function updateSupportTicket(ticketId) {
    try {
      await apiRequest(`${operationsApi}/support-tickets/${encodeURIComponent(ticketId)}`, {
        method: 'PATCH',
        body: JSON.stringify({
          status: $(`ticketStatus-${ticketId}`).value
        })
      });
      message('ticketsMessage', 'Support ticket updated.');
      await loadSupportTickets();
    } catch (error) {
      message('ticketsMessage', error.message || 'Unable to update support ticket.', true);
    }
  }

  async function updateOrderStatus(orderId) {
  const statusInput = $(`orderStatus-${orderId}`);

  if (!statusInput) return;

  const newStatus = statusInput.value;

  try {
    message('moduleOrdersMessage', 'Updating order status...');

    await apiRequest(
      `/api/admin/orders/${encodeURIComponent(orderId)}`,
      {
        method: 'PUT',
        body: JSON.stringify({
          order_status: newStatus
        })
      }
    );

    message('moduleOrdersMessage', 'Order status updated successfully.');
    await loadOrders();

  } catch (error) {
    message(
      'moduleOrdersMessage',
      error.message || 'Unable to update order status.',
      true
    );
  }
}

  async function loadReports() {
    const container = $('module44ReportsOverview');
    if (!container) return;

    container.textContent = 'Loading reports…';
    message('module44ReportsMessage', '');

    try {
      const data = await request('/api/admin/reports/summary');
      const overview = data.overview || {};
      const platform = data.platform || {};
      const statuses = data.order_status || [];

      const cards = [
        ['Total Orders', overview.total_orders],
        ['Active Orders', overview.active_orders],
        ['Delivered Orders', overview.delivered_orders],
        ['Cancelled Orders', overview.cancelled_orders],
        ['Total Revenue', money(overview.total_revenue)],
        ['Average Order Value', money(overview.average_order_value)],
        ['Customers', platform.customers],
        ['Restaurants', platform.restaurants],
        ['Delivery Partners', platform.delivery_partners]
      ];

      container.innerHTML = `
        <div class="module44-report-grid">
          ${cards.map(([label, value]) => `
            <div class="module44-report-card">
              <div>${escape(label)}</div>
              <strong>${typeof value === 'string' ? value : showValue(value ?? 0)}</strong>
            </div>
          `).join('')}
        </div>
        <h4>Orders by Status</h4>
        <ul>
          ${statuses.length
            ? statuses.map((item) =>
                `<li>${showValue(item.status)}: ${showValue(item.count)}</li>`
              ).join('')
            : '<li>No status summary available.</li>'}
        </ul>
      `;
    } catch (error) {
      container.textContent = 'Could not load reports.';
      message('module44ReportsMessage', error.message || 'Request failed.', true);
    }
  }

async function loadAll() {
  if (!$('deliveryManagementSection')) return;

  await loadFranchiseeOptions();
  await loadRiderOptions();
  await loadDispatchRiders();

  loadPartners();
  loadRestaurants();
  loadOrders();
  loadDispatchSettings();
  loadDispatchOrders();
  loadPayouts();
  loadSupportTickets();
  loadReports();
}

function bind() {
  const bindClick = (id, callback) => {
    $(id)?.addEventListener('click', callback);
  };

  bindClick('refreshDeliveryPartnersButton', loadPartners);
  bindClick('refreshRestaurantsButton', loadRestaurants);
  bindClick('refreshModuleOrdersButton', loadOrders);
  bindClick('refreshDispatchButton', async () => {
    await loadDispatchRiders();
    await loadDispatchOrders();
    await loadDispatchSettings();
  });
  bindClick('refreshPayoutsButton', loadPayouts);
  bindClick('refreshTicketsButton', loadSupportTickets);
  bindClick('module44ReportsRefreshButton', loadReports);
  $('dispatchSettingsForm')?.addEventListener('submit', saveDispatchSettings);
  $('riderOnboardingForm')?.addEventListener('submit', createRiderOnboarding);
  $('payoutForm')?.addEventListener('submit', createPayout);
  $('supportTicketForm')?.addEventListener('submit', createSupportTicket);

  $('restaurantsTableBody')?.addEventListener('click', (event) => {
    const button = event.target.closest('.restaurant-update-btn');

    if (button) {
      updateRestaurantStatus(button.dataset.restaurantId);
    }
  });

  $('moduleOrdersTableBody')?.addEventListener('click', (event) => {
  const statusButton = event.target.closest('.order-update-btn');
  const feeButton = event.target.closest('.order-fee-update-btn');

  if (statusButton) {
updateOrderStatus(statusButton.dataset.orderId);
  } else if (feeButton) {
updateDeliveryFee(feeButton.dataset.orderId);
  }
});
$('deliveryPartnersTableBody')?.addEventListener('click', (event) => {
  const updateButton = event.target.closest('.rider-update-btn');
  const approveButton = event.target.closest('.rider-approve-btn');

  if (updateButton) {
    updateRider(
  updateButton.dataset.partnerId,
  updateButton.dataset.franchiseeId
);
  } else if (approveButton) {
approveRider(
  approveButton.dataset.partnerId,
  approveButton.dataset.franchiseeId
);
  }
});
$('dispatchOrdersTableBody')?.addEventListener('click', (event) => {
  const button = event.target.closest('.order-reassign-btn');
  if (button) reassignOrder(button.dataset.orderId);
});
$('payoutsTableBody')?.addEventListener('click', (event) => {
  const button = event.target.closest('.payout-paid-btn');
  if (button) markPayoutPaid(button.dataset.payoutId);
});
$('ticketsTableBody')?.addEventListener('click', (event) => {
  const button = event.target.closest('.ticket-update-btn');
  if (button) updateSupportTicket(button.dataset.ticketId);
});

    const bindSearch = (id, key, callback) => {
      $(id)?.addEventListener('input', () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
          pages[key] = 1;
          callback();
        }, 350);
      });
      $(id)?.addEventListener('change', () => {
        pages[key] = 1;
        callback();
      });
    };

    bindSearch('deliveryPartnerSearch', 'partners', loadPartners);
    bindSearch('deliveryPartnerStatus', 'partners', loadPartners);
    bindSearch('deliveryPartnerVerification', 'partners', loadPartners);
$('deliveryPartnerFranchiseeSearch')?.addEventListener('input', () => {
  clearTimeout(franchiseeSearchTimer);

  franchiseeSearchTimer = setTimeout(async () => {
    const search = getSearch('deliveryPartnerFranchiseeSearch').toLowerCase();

    const franchisee = franchiseeOptions.find(item => {
      const name = String(item.name || '').toLowerCase();

      return name.includes(search) ||
        (search.includes('bengaluru') && name.includes('bangalore')) ||
        (search.includes('bangalore') && name.includes('bengaluru'));
    });

    const select = $('deliveryPartnerFranchiseeFilter');

    if (!search) {
      select.value = '';
      pages.partners = 1;
      await loadRiderOptions();
      await loadPartners();
      return;
    }

    if (franchisee) {
      select.value = String(franchisee.id);
      pages.partners = 1;
      await loadRiderOptions();
      await loadPartners();
    } else {
      select.value = '';
      $('deliveryPartnersTableBody').innerHTML =
        '<tr><td colspan="10">No matching franchisee found.</td></tr>';
    }
  }, 300);
});

    bindSearch('deliveryPartnerRiderFilter', 'partners', loadPartners);
    bindSearch('restaurantSearch', 'restaurants', loadRestaurants);
    bindSearch('restaurantStatus', 'restaurants', loadRestaurants);
    bindSearch('moduleOrderSearch', 'orders', loadOrders);
    bindSearch('moduleOrderStatus', 'orders', loadOrders);

    bindClick('deliveryPartnersPrevious', () => {
      if (pages.partners > 1) {
        pages.partners--;
        loadPartners();
      }
    });
    bindClick('deliveryPartnersNext', () => {
      if (pages.partners < totalPages.partners) {
        pages.partners++;
        loadPartners();
      }
    });
    bindClick('restaurantsPrevious', () => {
      if (pages.restaurants > 1) {
        pages.restaurants--;
        loadRestaurants();
      }
    });
    bindClick('restaurantsNext', () => {
      if (pages.restaurants < totalPages.restaurants) {
        pages.restaurants++;
        loadRestaurants();
      }
    });
    bindClick('moduleOrdersPrevious', () => {
      if (pages.orders > 1) {
        pages.orders--;
        loadOrders();
      }
    });
    bindClick('moduleOrdersNext', () => {
      if (pages.orders < totalPages.orders) {
        pages.orders++;
        loadOrders();
      }
    });

    document.querySelector(
      '[data-section="deliveryManagementSection"]'
    )?.addEventListener('click', loadAll);
  }

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    bind();
    loadAll();
  });
} else {
  bind();
  loadAll();
}
})();
