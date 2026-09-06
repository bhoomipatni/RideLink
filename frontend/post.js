
let directionsService;
let directionsRenderer;
let startPlace;
let endPlace;
let selectedStartValue = "";
let selectedEndValue = "";

function setMapStatus(message) {
    const status = document.getElementById("mapStatus");
    if (status) status.textContent = message;
}

function updateRoute() {
    if (!startPlace || !endPlace) {
        setMapStatus("Choose a start and destination to preview your route.");
        return;
    }

    directionsService.route({
        origin: startPlace.geometry.location,
        destination: endPlace.geometry.location,
        travelMode: google.maps.TravelMode.DRIVING,
    }, (result, status) => {
        if (status !== "OK") {
            setMapStatus("We could not find a driving route for those locations.");
            return;
        }
        directionsRenderer.setDirections(result);
        const leg = result.routes[0].legs[0];
        setMapStatus(`${leg.distance.text} - about ${leg.duration.text}`);
    });
}

function initPostTripMap() {
    const map = new google.maps.Map(document.getElementById("postTripMap"), {
        center: { lat: 42.7284, lng: -73.6918 },
        zoom: 11,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
    });
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer({ map });

    const autocompleteOptions = {
        fields: ["formatted_address", "geometry", "name"],
        componentRestrictions: { country: "us" },
    };
    const startAutocomplete = new google.maps.places.Autocomplete(
        document.getElementById("start"), autocompleteOptions,
    );
    const endAutocomplete = new google.maps.places.Autocomplete(
        document.getElementById("end"), autocompleteOptions,
    );

    startAutocomplete.addListener("place_changed", () => {
        startPlace = startAutocomplete.getPlace();
        selectedStartValue = document.getElementById("start").value;
        updateRoute();
    });
    endAutocomplete.addListener("place_changed", () => {
        endPlace = endAutocomplete.getPlace();
        selectedEndValue = document.getElementById("end").value;
        updateRoute();
    });

    document.getElementById("start").addEventListener("input", (event) => {
        if (event.target.value !== selectedStartValue) startPlace = null;
    });
    document.getElementById("end").addEventListener("input", (event) => {
        if (event.target.value !== selectedEndValue) endPlace = null;
    });
}

async function loadGoogleMaps() {
    try {
        const response = await fetch("/google-maps-config");
        if (!response.ok) throw new Error("Google Maps is not configured");
        const { api_key: apiKey } = await response.json();
        window.initPostTripMap = initPostTripMap;
        window.gm_authFailure = () => setMapStatus("Google Maps needs billing enabled for this API key.");
        const script = document.createElement("script");
        script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(apiKey)}&loading=async&libraries=places&callback=initPostTripMap`;
        script.async = true;
        script.defer = true;
        script.onerror = () => setMapStatus("Map preview is unavailable right now.");
        document.head.appendChild(script);
    } catch (error) {
        console.warn("Google Maps could not be loaded:", error.message);
        setMapStatus("Map preview is unavailable right now.");
    }
}

loadGoogleMaps();

const submit = document.getElementById("postButton");
submit.addEventListener("click", async () => {
    try {
        // Get current user
        const meResponse = await fetch("/me");
        const meData = await meResponse.json();

        if (!meData.authenticated) {
            alert("Please log in first");
            window.location.href = "/login";
            return;
        }

        const startLoc = document.getElementById("start").value;
        const endLoc = document.getElementById("end").value;
        const date = document.getElementById("date").value;
        const time = document.getElementById("time").value || "00:00";
        const seats = parseInt(document.getElementById("seats").value) || 4;

        if (!startLoc || !endLoc || !date) {
            alert("Please fill in all required fields");
            return;
        }

        // Construct datetime
        const dateTime = new Date(date + "T" + time + ":00").toISOString();

        // Calculate basic cost (can be improved later with distance/time calculation)
        const baseCost = 10.50;
        const costPerSeat = seats > 0 ? (baseCost / seats).toFixed(2) : baseCost;

        let response = await fetch("/request_ride", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                origin: startLoc,
                address: endLoc,
                date: dateTime,
                seats: seats,
                cost: parseFloat(costPerSeat),
                description: ""
            })
        });

        const result = await response.json();
        console.log("status:", response.status);
        console.log(result);

        if (response.ok) {
            alert("Trip posted successfully!");
            window.location.href = "trips.html";
        } else {
            alert("Error posting trip: " + (result.detail || "Unknown error"));
        }
    } catch (e) {
        console.error("fetch error:", e);
        alert("Error: " + e.message);
    }
});

document.getElementById("seats").addEventListener("input", function() {
  if (this.value > 25) this.value = 25;
  if (this.value < 1 && this.value !== "") this.value = 1;
});
