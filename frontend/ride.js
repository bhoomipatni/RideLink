
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

        // render ride cards
        resultsDiv.innerHTML = "";
        for (let item of data) {
            let r = item.ride;
            let eta = item.detour_eta != null ? Math.round(item.detour_eta / 60) + " min" : "N/A";
            let fullMins = item.full_eta != null ? Math.round(item.full_eta / 60) : null;
            let trueEta = fullMins != null ? (fullMins >= 60 ? Math.floor(fullMins / 60) + "h " + (fullMins % 60) + "m" : fullMins + " min") : "N/A";
            let dateStr = new Date(r.date).toLocaleString();
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
    } catch (e) {
        console.error("fetch error:", e);
        resultsDiv.innerHTML = "<p class='no-results'>Error: " + e.message + "</p>";
    }
});
