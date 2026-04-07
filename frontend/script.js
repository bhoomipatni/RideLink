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
    document.getElementById('cost').textContent = `$${trip.cost}`;
    document.getElementById('payment').textContent = trip.payment_method;
    document.getElementById('riders').textContent = `${trip.num_riders} other riders`;
    document.getElementById("driverName").textContent = trip.driver;
    document.getElementById("avatar").textContent = trip.driver.charAt(0).toUpperCase();
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
    document.getElementById('trip-list').innerHTML += `
      <a href="trips_details.html?id=${trip.id}" class="trip-card">
        <h4>${trip.destination}</h4>
        <p>${trip.date}</p>
        <p>$${trip.cost}</p>
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