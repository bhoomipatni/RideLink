let map;
let autocomplete;
let rideMarkers = [];
let destinationPlace;

function initRideMap() {
    map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: 39.8283, lng: -98.5795 },
        zoom: 4,
        mapTypeControl: false,
        streetViewControl: false,
    });

    autocomplete = new google.maps.places.Autocomplete(document.getElementById("address"), {
        fields: ["formatted_address", "geometry", "name"],
        componentRestrictions: { country: "us" },
    });

    autocomplete.addListener("place_changed", () => {
        destinationPlace = autocomplete.getPlace();
        if (destinationPlace.geometry) {
            map.setCenter(destinationPlace.geometry.location);
            map.setZoom(14);
            new google.maps.Marker({
                map: map,
                position: destinationPlace.geometry.location,
                title: destinationPlace.formatted_address || destinationPlace.name,
            });
            document.getElementById("address").value = destinationPlace.formatted_address;
        }
    });

    document.getElementById("address").addEventListener("input", () => {
        destinationPlace = null;
    });
}

async function loadGoogleMaps() {
    try {
        const response = await fetch("/google-maps-config");
        if (!response.ok) throw new Error("Google Maps is not configured");
        const { api_key: apiKey } = await response.json();
        window.initRideMap = initRideMap;
        const script = document.createElement("script");
        script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(apiKey)}&loading=async&libraries=places&callback=initRideMap`;
        script.async = true;
        script.defer = true;
        script.onerror = () => console.error("Google Maps could not be loaded");
        document.head.appendChild(script);
    } catch (error) {
        console.error("Google Maps could not be loaded:", error.message);
    }
}

loadGoogleMaps();

let searchBtn = document.getElementById("searchButton");
searchBtn.addEventListener("click", async () => {
    let address = document.getElementById("address").value.trim();
    let date = document.getElementById("date").value;
    let resultsDiv = document.getElementById("results");

    if (!address || !date) {
        resultsDiv.innerHTML = "<p class='no-results'>Please enter both an address and a date.</p>";
        return;
    }

    resultsDiv.innerHTML = "<p>Searching...</p>";

    try {
        let response = await fetch("/search_rides/" + encodeURIComponent(address) + "/" + new Date(date).toISOString());
        console.log("status:", response.status);
        let data = await response.json();
        console.log(data);

        if (!response.ok) {
            resultsDiv.innerHTML = "<p class='no-results'>" + (data.detail || "No rides found.") + "</p>";
            return;
        }

        // clear old ride markers
        rideMarkers.forEach(m => m.setMap(null));
        rideMarkers = [];

        // render ride cards and drop map pins
        resultsDiv.innerHTML = "";
        let bounds = new google.maps.LatLngBounds();
        for (let item of data) {
            let r = item.ride;
            let eta = item.detour_eta != null ? Math.round(item.detour_eta / 60) + " min" : "N/A";
            let fullMins = item.true_eta != null ? Math.round(item.true_eta / 60) : null;
            let trueEta = fullMins != null ? (fullMins >= 60 ? Math.floor(fullMins / 60) + "h " + (fullMins % 60) + "m" : fullMins + " min") : "N/A";
            let dateStr = new Date(r.date).toLocaleString();

            let pos = { lat: r.lat, lng: r.lon };
            let marker = new google.maps.Marker({
                map: map,
                position: pos,
                title: `${r.origin} → ${r.address}`,
            });
            let infoWindow = new google.maps.InfoWindow({
                content: `<strong>${r.origin} → ${r.address}</strong><br>$${r.cost.toFixed(2)} · ${dateStr}`,
            });
            marker.addListener("click", () => infoWindow.open(map, marker));
            rideMarkers.push(marker);
            bounds.extend(pos);

            // AI GEN REPLACE IN PROD ⚠️
            let rideCardHtml = `
            <div class="ride-card">
                <div class="ride-card-header">
                    <span class="ride-origin">${r.origin}</span>
                    <span class="ride-arrow">→</span>
                    <span class="ride-dest">${r.address}</span>
                </div>
                <div class="ride-card-body">
                    <div class="ride-detail"><strong>Date:</strong> ${dateStr}</div>
                    <div class="ride-detail"><strong>Cost:</strong> $${r.cost.toFixed(2)}</div>
                    <div class="ride-detail"><strong>Available Seats:</strong> ${r.seat_count}</div>
                    <div class="ride-detail"><strong>Trip Duration:</strong> ${trueEta}</div>
                    <div class="ride-detail"><strong>Detour ETA:</strong> ${eta}</div>
                    ${r.description ? `<div class="ride-detail"><strong>Info:</strong> ${r.description}</div>` : ""}
                </div>
                <div class="ride-card-actions">
                    <button class="request-ride-btn" data-ride-id="${r.id}">Request Ride</button>
                </div>
            </div>`;
            resultsDiv.innerHTML += rideCardHtml;
        }
        if (rideMarkers.length > 0) {
            map.fitBounds(bounds);
            google.maps.event.addListenerOnce(map, "bounds_changed", () => {
                if (map.getZoom() > 10) map.setZoom(10);
            });
        }

        // Attach event listeners to request buttons
        document.querySelectorAll(".request-ride-btn").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                e.preventDefault();
                const rideId = parseInt(btn.getAttribute("data-ride-id"));
                await requestRide(rideId);
            });
        });
    } catch (e) {
        console.error("fetch error:", e);
        resultsDiv.innerHTML = "<p class='no-results'>Error: " + e.message + "</p>";
    }
});

async function requestRide(rideId) {
    try {
        // Check authentication
        const meResponse = await fetch("/me");
        const meData = await meResponse.json();

        if (!meData.authenticated) {
            alert("Please log in first");
            window.location.href = "/login";
            return;
        }

        // Request the ride
        const response = await fetch("/add_rider", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                ride_id: rideId
            })
        });

        const result = await response.json();

        if (response.ok) {
            alert("Ride request submitted! The driver will review your request.");
        } else {
            alert("Error requesting ride: " + (result.detail || "Unknown error"));
        }
    } catch (e) {
        console.error("Error requesting ride:", e);
        alert("Error: " + e.message);
    }
}