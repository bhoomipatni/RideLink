//used for trips_details.html -> load in info for an individual trip
async function loadIndTrip() {
    //get the id from the URL
    const id = new URLSearchParams(location.search).get('id');

    //fetch specific trip from your backend
    const response = await fetch(`/api/trips/${id}`);
    const trip = await response.json();

    //get relevant data
    document.getElementById('destination').textContent = trip.destination;
    document.getElementById('dateNtime').textContent = `${trip.dayname} ${trip.date} @ ${trip.time}`;
    document.getElementById('driver').textContent = `with ${trip.driver}`;
    document.getElementById('distance').textContent = `${trip.distance} miles`;
    document.getElementById('cost').textContent = `$${trip.cost}`;
    document.getElementById('payment').textContent = trip.payment_method;
    document.getElementById('riders').textContent = `${trip.num_riders} other riders`;
}
loadIndTrip.apply();

//used for trips.html -> loads in the list
async function loadTrips() {
  const response = await fetch('test.json'); //this is just to see how the list looks with fake user input
  const trips = await response.json();

  trips.forEach(trip => {
    document.getElementById('trip-list').innerHTML += `
      <a href="trips_details.html?id=${trip.id}" class="trip-card">
        <span>${trip.destination}</span>
        <span>${trip.date}</span>
        <span>$${trip.cost}</span>
      </a>
    `;
  });
}
loadTrips();