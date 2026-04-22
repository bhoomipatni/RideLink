//trips_detail.html
async function loadIndTrip() {
  const id = new URLSearchParams(location.search).get('id');

  const response = await fetch('test.json');
  const trips = await response.json();
  const trip = trips.find(t => t.id === parseInt(id));

  if (!trip) return;

  if (trip.role === 'driver') {
    renderDriverDetail(trip);
  } else {
    renderRiderDetail(trip);
  }
}

function renderRiderDetail(trip) {
  document.getElementById('destination').textContent = trip.destination;
  document.getElementById('timeNdriver').textContent = `${trip.day}, ${trip.date} @ ${trip.time}`;
  document.getElementById('distance').textContent = `${trip.distance} mi`;
  document.getElementById('cost').textContent = `$${Number(trip.cost).toFixed(2)}`;
  document.getElementById('payment').textContent = trip.payment_method;
  document.getElementById('riders').textContent = trip.num_riders === 1 ? '1 other rider' : `${trip.num_riders} other riders`;
  document.getElementById('driverName').textContent = trip.driver;
  document.getElementById('avatar').textContent = trip.driver.charAt(0).toUpperCase();

  const meta = document.getElementById('timeNdriver');
  meta.insertAdjacentHTML('afterend', `<div class="header-route">${trip.origin} &rarr; ${trip.destination}</div>`);

  const statusEl = document.getElementById('status');
  statusEl.textContent = trip.status;
  statusEl.className = `status-pill status-${trip.status.toLowerCase()}`;
}

function renderDriverDetail(trip) {
  document.getElementById('destination').textContent = trip.destination;
  document.getElementById('timeNdriver').textContent = `${trip.day}, ${trip.date} @ ${trip.time}`;

  const meta = document.getElementById('timeNdriver');
  meta.insertAdjacentHTML('afterend', `<div class="header-route">${trip.origin} &rarr; ${trip.destination}</div>`);

  document.getElementById('distance').textContent = `${trip.distance} mi`;
  document.getElementById('cost').textContent = `$${Number(trip.cost).toFixed(2)}`;

  const ridersEl = document.getElementById('riders');
  ridersEl.textContent = `${trip.seats_filled} / ${trip.seats_total}`;
  ridersEl.closest('.stat-box').querySelector('.stat-lbl').textContent = 'Seats filled';

  document.getElementById('driverName').textContent = 'You (driver)';
  document.getElementById('avatar').textContent = 'Y';
  document.querySelector('.driver-sub').textContent = 'Your trip';

  document.getElementById('payment').textContent = trip.payment_method;
  const statusEl = document.getElementById('status');
  statusEl.textContent = trip.status;
  statusEl.className = `status-pill status-${trip.status.toLowerCase()}`;

  const body = document.querySelector('.detail-body');
  const passengerHTML = `
    <hr class="detail-divider">
    <div class="detail-section-label">Passengers</div>
    <div class="passenger-list">
      ${trip.passengers.map(p => `
        <div class="passenger-row">
          <div class="driver-avatar passenger-avatar">${p.name.charAt(0).toUpperCase()}</div>
          <div class="passenger-info">
            <div class="passenger-name">${p.name}</div>
            <div class="passenger-id">ID: ${p.id}</div>
          </div>
          <div class="passenger-badges">
            <span class="badge badge-join-${p.status}">${p.status}</span>
            <span class="badge badge-pay-${p.payment_status}">${p.payment_status}</span>
          </div>
        </div>
      `).join('')}
    </div>
  `;
  body.insertAdjacentHTML('beforeend', passengerHTML);

  if (trip.status === 'completed' || trip.status === 'cancelled') return;

  const editHTML = `
    <hr class="detail-divider">
    <div class="detail-section-label">Manage trip</div>
    <div class="edit-panel" id="edit-panel">

      <div class="edit-field">
        <label class="edit-label" for="edit-destination">Destination</label>
        <input class="edit-input" id="edit-destination" type="text" value="${trip.destination}" />
      </div>

      <div class="edit-field">
        <label class="edit-label" for="edit-origin">Pickup location</label>
        <input class="edit-input" id="edit-origin" type="text" value="${trip.origin}" />
      </div>

      <div class="edit-row-2">
        <div class="edit-field">
          <label class="edit-label" for="edit-date">Date</label>
          <input class="edit-input" id="edit-date" type="text" value="${trip.date}" />
        </div>
        <div class="edit-field">
          <label class="edit-label" for="edit-time">Time</label>
          <input class="edit-input" id="edit-time" type="time"
            value="${to24hr(trip.time)}" />
        </div>
      </div>

      <div class="edit-row-2">
        <div class="edit-field">
          <label class="edit-label" for="edit-seats">Total seats</label>
          <input class="edit-input" id="edit-seats" type="number"
            min="${trip.seats_filled}" max="8" value="${trip.seats_total}" />
        </div>
        <div class="edit-field">
          <label class="edit-label" for="edit-payment">Payment method</label>
          <select class="edit-input" id="edit-payment">
            ${['Venmo','PayPal','Cash','Other'].map(m =>
              `<option${m === trip.payment_method ? ' selected' : ''}>${m}</option>`
            ).join('')}
          </select>
        </div>
      </div>

      <div class="edit-actions-row">
        <button class="edit-save-btn" onclick="saveTrip(${trip.id})">Save changes</button>
        <button class="edit-cancel-btn" onclick="confirmCancel(${trip.id})">Cancel trip</button>
      </div>

      <div id="edit-status-msg" class="edit-status-msg"></div>
    </div>
  `;
  body.insertAdjacentHTML('beforeend', editHTML);
}

function to24hr(timeStr) {
  const [time, meridiem] = timeStr.split(' ');
  let [h, m] = time.split(':').map(Number);
  if (meridiem === 'PM' && h !== 12) h += 12;
  if (meridiem === 'AM' && h === 12) h = 0;
  return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`;
}

function to12hr(val) {
  let [h, m] = val.split(':').map(Number);
  const mer = h >= 12 ? 'PM' : 'AM';
  if (h > 12) h -= 12;
  if (h === 0) h = 12;
  return `${h}:${String(m).padStart(2,'0')} ${mer}`;
}

function saveTrip(id) {
  const destination = document.getElementById('edit-destination').value.trim();
  const origin      = document.getElementById('edit-origin').value.trim();
  const date        = document.getElementById('edit-date').value.trim();
  const timeRaw     = document.getElementById('edit-time').value;
  const payment     = document.getElementById('edit-payment').value;

  if (!destination || !origin || !date || !timeRaw) {
    showEditMsg('Please fill in all fields.', 'error');
    return;
  }

  const time12 = to12hr(timeRaw);

  document.getElementById('destination').textContent = destination;
  document.getElementById('timeNdriver').textContent = `${date} @ ${time12}`;
  const routeEl = document.querySelector('.header-route');
  if (routeEl) routeEl.textContent = `${origin} → ${destination}`;
  document.getElementById('payment').textContent = payment;

  showEditMsg('Changes saved.', 'success');
}

function confirmCancel(id) {
  const confirmed = window.confirm(
    'Are you sure you want to cancel this trip? Your passengers will be notified.'
  );
  if (!confirmed) return;

  const statusEl = document.getElementById('status');
  statusEl.textContent = 'cancelled';
  statusEl.className = 'status-pill status-cancelled';

  document.getElementById('edit-panel').remove();

  const body = document.querySelector('.detail-body');
  body.insertAdjacentHTML('beforeend',
    `<p class="edit-cancelled-note">This trip has been cancelled.</p>`);
}

function showEditMsg(msg, type) {
  const el = document.getElementById('edit-status-msg');
  el.textContent = msg;
  el.className = `edit-status-msg edit-status-${type}`;
  setTimeout(() => { el.textContent = ''; el.className = 'edit-status-msg'; }, 3000);
}

if (document.getElementById('destination')) {
  loadIndTrip();
}


//trips.html

async function loadTrips(filter = 'upcoming') {
  const response = await fetch('test.json');
  const trips = await response.json();

  const today = new Date();
  const upcomingList = [];
  const pastList = [];
  const driverList = [];

  trips.forEach(trip => {
    if (trip.role === 'driver') {
      driverList.push(trip);
      return;
    }
    const tripDate = new Date(trip.date);
    if (tripDate >= today) {
      upcomingList.push(trip);
    } else {
      pastList.push(trip);
    }
  });

  let toShow;
  if (filter === 'upcoming')  toShow = upcomingList;
  else if (filter === 'past') toShow = pastList;
  else                        toShow = driverList;

  const listEl = document.getElementById('trip-list');
  listEl.innerHTML = '';

  if (toShow.length === 0) {
    listEl.innerHTML = `<p class="trips-empty">No trips to show.</p>`;
    return;
  }

  if (filter === 'driver') {
    toShow.forEach(trip => renderDriverCard(trip, listEl));
  } else {
    toShow.forEach(trip => renderRiderCard(trip, listEl));
  }
}

function renderRiderCard(trip, container) {
  const statusClass = `status-${trip.status.toLowerCase()}`;
  const origin = trip.origin || 'Campus';
  container.innerHTML += `
    <a href="trips_details.html?id=${trip.id}" class="trip-card">
      <div class="trip-card-top">
        <span class="trip-destination">${trip.destination}</span>
        <span class="status-pill ${statusClass}">${trip.status}</span>
      </div>
      <div class="trip-card-route">
        <span class="route-origin">${origin}</span>
        <span class="route-arrow">→</span>
        <span class="route-dest">${trip.destination}</span>
      </div>
      <div class="trip-card-meta">
        <span class="meta-icon">🗓</span>
        <span>${trip.day}, ${trip.date} @ ${trip.time}</span>
        <span class="meta-sep">·</span>
        <span class="meta-icon">🚗</span>
        <span>${trip.driver}</span>
      </div>
      <div class="trip-card-bottom">
        <span>${trip.distance} mi</span>
        <span class="trip-cost">$${parseFloat(trip.cost).toFixed(2)}</span>
      </div>
    </a>
  `;
}

function renderDriverCard(trip, container) {
  const statusClass = `status-${trip.status.toLowerCase()}`;
  const seatsFilled = trip.seats_filled ?? (trip.passengers ? trip.passengers.length : 0);
  const seatsTotal  = trip.seats_total ?? '?';
  const passengerNames = trip.passengers && trip.passengers.length > 0
    ? trip.passengers.map(p => p.name).join(', ')
    : 'No passengers yet';

  container.innerHTML += `
    <a href="trips_details.html?id=${trip.id}" class="trip-card trip-card-driver">
      <div class="trip-card-top">
        <span class="trip-destination">${trip.destination}</span>
        <span class="status-pill ${statusClass}">${trip.status}</span>
      </div>
      <div class="trip-card-route">
        <span class="route-origin">${trip.origin}</span>
        <span class="route-arrow">→</span>
        <span class="route-dest">${trip.destination}</span>
      </div>
      <div class="trip-card-meta">
        <span class="meta-icon">🗓</span>
        <span>${trip.day}, ${trip.date} @ ${trip.time}</span>
        <span class="meta-sep">·</span>
        <span class="driver-badge">You're driving</span>
      </div>
      <div class="trip-card-passengers">
        <span class="passengers-label">Passengers:</span>
        <span class="passengers-names">${passengerNames}</span>
        <span class="seats-chip">${seatsFilled}/${seatsTotal} seats</span>
      </div>
      <div class="trip-card-bottom">
        <span>${trip.distance} mi</span>
        <span class="trip-cost">$${parseFloat(trip.cost).toFixed(2)} / seat</span>
      </div>
    </a>
  `;
}

if (document.getElementById('trip-list')) {
  loadTrips();
}

function showTab(tab, e) {
  loadTrips(tab);
  document.querySelectorAll('.tab').forEach(btn => btn.classList.remove('active'));
  (e ? e.target : event.target).classList.add('active');
}