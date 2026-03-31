let map;
let autocomplete;
let rideMarkers = [];

function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: 39.8283, lng: -98.5795 },
        zoom: 4,
    });

    let mapSearch = document.createElement("input");
    mapSearch.type = "text";
    mapSearch.placeholder = "Search for a location";
    mapSearch.style.cssText = "margin:10px;padding:8px 12px;width:300px;font-size:14px;border:none;border-radius:4px;box-shadow:0 2px 6px rgba(0,0,0,0.3);";

    map.controls[google.maps.ControlPosition.TOP_CENTER].push(mapSearch);

    let marker;
    autocomplete = new google.maps.places.Autocomplete(mapSearch, {
        fields: ["formatted_address", "geometry"],
    });

    autocomplete.addListener("place_changed", () => {
        let place = autocomplete.getPlace();
        if (place.geometry) {
            map.setCenter(place.geometry.location);
            map.setZoom(14);
            if (marker) marker.setMap(null);
            marker = new google.maps.Marker({
                map: map,
                position: place.geometry.location,
            });
            document.getElementById("address").value = place.formatted_address;
        }
    });
}

window.initMap = initMap;

let script = document.createElement("script");
script.src = "/get_map";
script.async = true;
document.head.appendChild(script);

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
                title: `${r.orgin} → ${r.address}`,
            });
            let infoWindow = new google.maps.InfoWindow({
                content: `<strong>${r.orgin} → ${r.address}</strong><br>$${r.cost.toFixed(2)} · ${dateStr}`,
            });
            marker.addListener("click", () => infoWindow.open(map, marker));
            rideMarkers.push(marker);
            bounds.extend(pos);

            // AI GEN REPLACE IN PROD ⚠️
            resultsDiv.innerHTML += `
            <div class="ride-card">
                <div class="ride-card-header">
                    <span class="ride-origin">${r.orgin}</span>
                    <span class="ride-arrow">→</span>
                    <span class="ride-dest">${r.address}</span>
                </div>
                <div class="ride-card-body">
                    <div class="ride-detail"><strong>Date:</strong> ${dateStr}</div>
                    <div class="ride-detail"><strong>Cost:</strong> $${r.cost.toFixed(2)}</div>
                    <div class="ride-detail"><strong>Trip Duration:</strong> ${trueEta}</div>
                    <div class="ride-detail"><strong>Detour ETA:</strong> ${eta}</div>
                    ${r.description ? `<div class="ride-detail"><strong>Info:</strong> ${r.description}</div>` : ""}
                </div>
            </div>`;
        }
        if (rideMarkers.length > 0) {
            map.fitBounds(bounds);
            google.maps.event.addListenerOnce(map, "bounds_changed", () => {
                if (map.getZoom() > 10) map.setZoom(10);
            });
        }
    } catch (e) {
        console.error("fetch error:", e);
        resultsDiv.innerHTML = "<p class='no-results'>Error: " + e.message + "</p>";
    }
});