//testing "database"
const rides = [
  { driver: "Alex", destination: "Boston", time: "5pm" },
  { driver: "Sam", destination: "NYC", time: "3pm" }
];

// Dropdown menu toggle
const dropdownToggle = document.querySelector('.dropdown-toggle');
const dropdownMenu = document.querySelector('.dropdown-menu');

if (dropdownToggle) {
  dropdownToggle.addEventListener('click', function (e) {
    e.preventDefault();
    dropdownMenu.style.display = dropdownMenu.style.display === 'block' ? 'none' : 'block';
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.dropdown')) {
      dropdownMenu.style.display = 'none';
    }
  });
//used for trips_details.html -> load in info for an individual trip
async function loadIndTrip() {
    //get the id from the URL
    const id = new URLSearchParams(location.search).get('id');

    //DON'T DELETE yet
    //fetch specific trip from your backend
    //const response = await fetch(`/api/trips/${id}`);
    //const trip = await response.json();

    //this is just for testing css and formatting, the actual js script should fetch from backend databse thingy
    const response = await fetch('test.json');
    const trips = await response.json();
    const trip = trips.find(t => t.id === parseInt(id));


    //get relevant data - also need to check what kind of data is collected by the backend 
    document.getElementById('destination').textContent = trip.destination;
    document.getElementById('timeNdriver').textContent = `${trip.day} ${trip.date} @ ${trip.time} with ${trip.driver}`;
    document.getElementById('distance').textContent = `${trip.distance} miles`;
    document.getElementById('cost').textContent = `$${Number(trip.cost).toFixed(2)}`;
    document.getElementById('payment').textContent = trip.payment_method;
    document.getElementById('riders').textContent = `${trip.num_riders} other riders`;
    document.getElementById("driverName").textContent = trip.driver;
    document.getElementById("avatar").textContent = trip.driver.charAt(0).toUpperCase(); //shows a profile circle with their initial, 
    // ^ don't know if we want to let them import pictures later on
    
    //this is for the status of whether or not the trip is confirmed
    const statusEl = document.getElementById('status');
    statusEl.textContent = trip.status;
    statusEl.className = `status-pill status-${trip.status.toLowerCase()}`;
}
loadIndTrip.apply();


//used for trips.html -> loads in the list
async function loadTrips(filter = 'upcoming') {
  const response = await fetch('test.json'); //this is just to see how the list looks with fake user input
  const trips = await response.json();

  const today = new Date();
  const upcomingList = []; //temp array holders whenever new user loads the page
  const pastList = [];

  trips.forEach(trip => {
    const tripDate = new Date(trip.date);
    if (tripDate >= today) {
      upcomingList.push(trip);
    } else {
      pastList.push(trip);
    }
  });

  const toShow = filter === 'upcoming' ? upcomingList : pastList;

  document.getElementById('trip-list').innerHTML = '';
  toShow.forEach(trip => {
  const statusClass = `status-${trip.status.toLowerCase()}`;
  document.getElementById('trip-list').innerHTML += `
    <a href="trips_details.html?id=${trip.id}" class="trip-card">
      <div class="trip-card-top">
        <span class="trip-destination">${trip.destination}</span>
        <span class="status-pill ${statusClass}">${trip.status}</span>
      </div>
      <div class="trip-card-meta">
        <span>${trip.day} ${trip.date} @ ${trip.time}</span>
        <span>with ${trip.driver}</span>
      </div>
      <div class="trip-card-bottom">
        <span>${trip.distance} miles</span>
        <span class="trip-cost">$${parseFloat(trip.cost).toFixed(2)}</span>
      </div>
    </a>
  `;
});
}
loadTrips();

function showTab(tab) { //used for switching between Upcoming & Past trips in My Trips page
  loadTrips(tab);
  document.querySelectorAll('.tab').forEach(btn => btn.classList.remove('active'));
  event.target.classList.add('active');
}
}