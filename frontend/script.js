//used for trips_details.html -> load in info for an individual trip
async function loadIndTrip() {
    //get the id from the URL
    const id = new URLSearchParams(location.search).get('id');

    //DON'T DELETE
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
}
loadIndTrip.apply();

//used for trips.html -> loads in the list
async function loadTrips() {
  const response = await fetch('test.json'); //this is just to see how the list looks with fake user input
  const trips = await response.json();

  trips.forEach(trip => {
    document.getElementById('trip-list').innerHTML += `
      <a href="trips_details.html?id=${trip.id}" class="trip-card">
        <h3>${trip.destination}</h3>
        <p>${trip.date}</p>
        <p>$${trip.cost}</p>
      </a>
    `;
  });
}
loadTrips();