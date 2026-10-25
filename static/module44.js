
(() => {
  'use strict';

  const PAGE_SIZE = 10;
  const pages = { partners: 1, restaurants: 1, orders: 1 };
  const totals = { partners: 0, restaurants: 0, orders: 0 };
  const totalPages = { partners: 1, restaurants: 1, orders: 1 };
  let searchTimer;

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
    return apiRequest(path);
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

  async function loadPartners() {
    const body = $('deliveryPartnersTableBody');
    if (!body) return;

    const franchiseeId = getSearch('module44FranchiseeId');
    if (!franchiseeId) {
      body.innerHTML =
        '<tr><td colspan="8">Enter a Franchisee UUID to load delivery partners.</td></tr>';
      message('deliveryPartnersMessage', 'Franchisee ID is required.');
      totals.partners = 0;
      totalPages.partners = 1;
      updatePagination(
        'partners', 'deliveryPartnersPaginationLabel',
        'deliveryPartnersPrevious', 'deliveryPartnersNext'
      );
      return;
    }

    const params = queryString({
      franchisee_id: franchiseeId,
      search: getSearch('deliveryPartnerSearch'),
      status: getSearch('deliveryPartnerStatus'),
      verification_status: getSearch('deliveryPartnerVerification'),
      page: pages.partners,
      page_size: PAGE_SIZE
    });

    body.innerHTML = '<tr><td colspan="8">Loading delivery partners…</td></tr>';
    message('deliveryPartnersMessage', '');

    try {
      const data = await request(`/api/admin/delivery-partners?${params}`);
      const items = data.items || [];
      totals.partners = Number(data.total || 0);
      totalPages.partners = Math.max(1, Number(data.total_pages || 1));

      body.innerHTML = items.length ? items.map((item) => `
        <tr>
          <td>${showValue(item.partner_id)}</td>
          <td>${showValue(item.full_name)}</td>
          <td>${showValue(item.mobile_number)}</td>
          <td>${showValue(item.vehicle_type)}</td>
          <td>${showValue(item.city)}</td>
          <td>${showValue(item.status)}</td>
          <td>${showValue(item.verification_status)}</td>
          <td>—</td>
        </tr>
      `).join('') : '<tr><td colspan="8">No delivery partners found.</td></tr>';

      updatePagination(
        'partners', 'deliveryPartnersPaginationLabel',
        'deliveryPartnersPrevious', 'deliveryPartnersNext'
      );
    } catch (error) {
      body.innerHTML = '<tr><td colspan="8">Could not load delivery partners.</td></tr>';
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
          <td>—</td>
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

  async function loadOrders() {
    const body = $('moduleOrdersTableBody');
    if (!body) return;

    const params = queryString({
      search: getSearch('moduleOrderSearch'),
      status: getSearch('moduleOrderStatus'),
      page: pages.orders,
      page_size: PAGE_SIZE
    });

    body.innerHTML = '<tr><td colspan="8">Loading orders…</td></tr>';
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
          <td>${showValue(item.rider_id)}</td>
          <td>${money(item.total_amount ?? item.grand_total ?? item.amount)}</td>
          <td>${showValue(item.order_status ?? item.status)}</td>
          <td>${dateValue(item.created_at)}</td>
          <td>—</td>
        </tr>
      `).join('') : '<tr><td colspan="8">No orders found.</td></tr>';

      updatePagination(
        'orders', 'moduleOrdersPaginationLabel',
        'moduleOrdersPrevious', 'moduleOrdersNext'
      );
    } catch (error) {
      body.innerHTML = '<tr><td colspan="8">Could not load orders.</td></tr>';
      message('moduleOrdersMessage', error.message || 'Request failed.', true);
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

  function loadAll() {
    if (!$('deliveryManagementSection')) return;
    if (typeof state !== 'undefined' && !state.token) {
      message('deliveryPartnersMessage', 'Please sign in to load data.');
      message('restaurantsMessage', 'Please sign in to load data.');
      message('moduleOrdersMessage', 'Please sign in to load data.');
      message('module44ReportsMessage', 'Please sign in to load data.');
      return;
    }

    loadPartners();
    loadRestaurants();
    loadOrders();
    loadReports();
  }

  function bind() {
    const bindClick = (id, callback) => {
      $(id)?.addEventListener('click', callback);
    };

    bindClick('refreshDeliveryPartnersButton', loadPartners);
    bindClick('refreshRestaurantsButton', loadRestaurants);
    bindClick('refreshModuleOrdersButton', loadOrders);
    bindClick('module44ReportsRefreshButton', loadReports);

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
    bindSearch('module44FranchiseeId', 'partners', loadPartners);
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
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})();
