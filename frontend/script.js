// Load a single trip's detail view. Switches between rider and driver layouts.
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
  document.getElementById('timeNdriver').textContent = `${trip.day}, ${trip.date} @ ${trip.time} · with ${trip.driver}`;
  document.getElementById('distance').textContent = `${trip.distance} mi`;
  document.getElementById('cost').textContent = `$${Number(trip.cost).toFixed(2)}`;
  document.getElementById('payment').textContent = trip.payment_method;
  document.getElementById('riders').textContent = trip.num_riders === 1 ? '1 other rider' : `${trip.num_riders} other riders`;
  document.getElementById('driverName').textContent = trip.driver;
  document.getElementById('avatar').textContent = trip.driver.charAt(0).toUpperCase();

  const statusEl = document.getElementById('status');
  statusEl.textContent = trip.status;
  statusEl.className = `status-pill status-${trip.status.toLowerCase()}`;
}

function renderDriverDetail(trip) {
  //shared header fields
  document.getElementById('destination').textContent = trip.destination;
  document.getElementById('timeNdriver').textContent = `${trip.day}, ${trip.date} @ ${trip.time} · ${trip.origin} \u2192 ${trip.destination}`;

  //stats
  document.getElementById('distance').textContent = `${trip.distance} mi`;
  document.getElementById('cost').textContent = `$${Number(trip.cost).toFixed(2)}`;

  //swap "Other riders" stat label to show seats
  const ridersEl = document.getElementById('riders');
  ridersEl.textContent = `${trip.seats_filled} / ${trip.seats_total}`;
  ridersEl.closest('.stat-box').querySelector('.stat-lbl').textContent = 'Seats filled';

  //driver row — user is the driver
  document.getElementById('driverName').textContent = 'You (driver)';
  document.getElementById('avatar').textContent = 'Y';
  document.querySelector('.driver-sub').textContent = 'Your trip';

  //payment & status
  document.getElementById('payment').textContent = trip.payment_method;
  const statusEl = document.getElementById('status');
  statusEl.textContent = trip.status;
  statusEl.className = `status-pill status-${trip.status.toLowerCase()}`;

  //input passenger list
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
}

//only run on trips_details.html
if (document.getElementById('destination')) {
  loadIndTrip();
}


//trips.html stuff
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
  if (filter === 'upcoming')    toShow = upcomingList;
  else if (filter === 'past')   toShow = pastList;
  else                          toShow = driverList;

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
  container.innerHTML += `
    <a href="trips_details.html?id=${trip.id}" class="trip-card">
      <div class="trip-card-top">
        <span class="trip-destination">${trip.destination}</span>
        <span class="status-pill ${statusClass}">${trip.status}</span>
      </div>
      <div class="trip-card-meta">
        <span>${trip.day}, ${trip.date} @ ${trip.time}</span>
        <span>with ${trip.driver}</span>
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
      <div class="trip-card-meta">
        <span>${trip.day}, ${trip.date} @ ${trip.time}</span>
        <span class="driver-badge">You're driving</span>
      </div>
      <div class="trip-card-passengers">
        <span class="passengers-label">Passengers:</span>
        <span class="passengers-names">${passengerNames}</span>
      </div>
      <div class="trip-card-bottom">
        <span>${trip.distance} mi &middot; ${seatsFilled}/${seatsTotal} seats</span>
        <span class="trip-cost">$${parseFloat(trip.cost).toFixed(2)} / seat</span>
      </div>
    </a>
  `;
}

//only run on trips.html
if (document.getElementById('trip-list')) {
  loadTrips();
}

function showTab(tab, e) {
  loadTrips(tab);
  document.querySelectorAll('.tab').forEach(btn => btn.classList.remove('active'));
  (e ? e.target : event.target).classList.add('active');
}