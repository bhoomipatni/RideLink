let resultsDiv = document.getElementById("results");

async function resolveDriverRcsid(driverid) {
    try {
        let resp = await fetch("/users/" + encodeURIComponent(driverid));
        if (!resp.ok) return driverid;
        let user = await resp.json();
        return user.rcsid || driverid;
    } catch {
        return driverid;
    }
}

async function loadUpcomingRides() {
    resultsDiv.innerHTML = "<p>Loading...</p>";
    try {
        let response = await fetch("/five_upcoming_rides");
        let data = await response.json();

        if (!response.ok) {
            resultsDiv.innerHTML = "<p class='no-results'>" + (data.detail || "Could not load upcoming rides.") + "</p>";
            return;
        }

        let rides = data.rides || [];
        if (rides.length === 0) {
            resultsDiv.innerHTML = "<p class='no-results'>No upcoming rides yet.</p>";
            return;
        }

        let driverRcsids = await Promise.all(rides.map(r => resolveDriverRcsid(r.driverid)));

        resultsDiv.innerHTML = "";
        rides.forEach((r, i) => {
            let dateStr = new Date(r.date).toLocaleString();
            resultsDiv.innerHTML += `
            <div class="ride-card">
                <div class="ride-card-header">
                    <span class="ride-origin">${r.origin}</span>
                    <span class="ride-arrow">→</span>
                    <span class="ride-dest">${r.address}</span>
                </div>
                <div class="ride-card-body">
                    <div class="ride-detail"><strong>Date:</strong> ${dateStr}</div>
                    <div class="ride-detail"><strong>Cost:</strong> $${r.cost.toFixed(2)}</div>
                    <div class="ride-detail"><strong>Driver:</strong> ${driverRcsids[i]}</div>
                    ${r.description ? `<div class="ride-detail"><strong>Info:</strong> ${r.description}</div>` : ""}
                </div>
            </div>`;
        });
    } catch (e) {
        console.error("fetch error:", e);
        resultsDiv.innerHTML = "<p class='no-results'>Error: " + e.message + "</p>";
    }
}

loadUpcomingRides();
