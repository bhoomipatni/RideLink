
let submit = document.getElementById("postButton");
submit.addEventListener("click", async () => {
    // TODO WHEN LOGIN DONE ADD TO GET THE RCSID
    //post to backend
    try {
        let response = await fetch("/request_ride", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                driverid: 1, // TODO: replace with real user id after login is done
                address: document.getElementById("endInput").value,
                orgin: document.getElementById("startInput").value,
                date: new Date(document.getElementById("leave-date").value + "T" + (document.getElementById("leave-time").value || "00:00") + ":00").toISOString(),
                cost: 10.50,
                description: "I have snacks"
            })
        });
        console.log("status:", response.status);
        console.log(await response.json());
    } catch (e) {
        console.error("fetch error:", e);
    }
});
