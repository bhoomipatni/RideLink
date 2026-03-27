// ========== VARIABLES ==========

// --- VENMO ---
const venmoInput = document.getElementById("venmoUsername");
const venmoPreview = document.getElementById("venmoPreview");
const venmoConfirm = document.getElementById("venmoConfirm");
const venmoSave = document.getElementById("venmoSave");
const venmoStatus = document.getElementById("venmoStatus");
const venmoTest = document.getElementById("venmoTest");

// --- PAYPAL ---
const paypalInput = document.getElementById("paypalEmail");
const paypalConfirm = document.getElementById("paypalConfirm");
const paypalSave = document.getElementById("paypalSave");
const paypalStatus = document.getElementById("paypalStatus");
const paypalTest = document.getElementById("paypalTest");

// --- CASH ---
const cashToggle = document.getElementById("cashToggle");

// ========== VENMO LOGIC ==========
venmoInput.addEventListener("input", function () {
  let username = this.value.trim().replace("@", "");
  venmoPreview.innerText = username ? "Profile: @" + username : "";
});

venmoConfirm.addEventListener("change", function () {
  venmoSave.disabled = !this.checked;
});

venmoTest.addEventListener("click", function () {
  let username = venmoInput.value.trim().replace("@", "").toLowerCase();
  if (!username) { alert("Enter a username"); return; }

  const appLink = `venmo://users/${username}`;
  const webLink = `https://venmo.com/u/${username}`;

  window.location.href = appLink;
  setTimeout(() => { window.open(webLink, "_blank"); }, 1500);
});

venmoSave.addEventListener("click", async function () {
  let username = venmoInput.value.trim().replace("@", "").toLowerCase();
  if (!username) { alert("Enter a username"); return; }

  try {
    const res = await fetch("http://127.0.0.1:8000/payment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ venmo_username: username })
    });
    const data = await res.json();
    venmoStatus.innerText = "Saved: @" + data.payment.venmo;
  } catch (err) {
    console.error(err);
    alert("Failed to save Venmo username.");
  }
});

// ========== PAYPAL LOGIC ==========
paypalConfirm.addEventListener("change", function () {
  paypalSave.disabled = !this.checked;
});

paypalTest.addEventListener("click", function () {
  let email = paypalInput.value.trim();
  if (!email) { alert("Enter a PayPal email"); return; }
  window.open("https://www.paypal.com/signin", "_blank");
});

paypalSave.addEventListener("click", async function () {
  let email = paypalInput.value.trim();
  if (!email) { alert("Enter a PayPal email"); return; }

  try {
    const res = await fetch("http://127.0.0.1:8000/payment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ paypal_email: email })
    });
    const data = await res.json();
    paypalStatus.innerText = "Saved: " + data.payment.paypal;
  } catch (err) {
    console.error(err);
    alert("Failed to save PayPal email.");
  }
});

// ========== CASH LOGIC ==========
cashToggle.addEventListener("change", async function () {
  try {
    const res = await fetch("http://127.0.0.1:8000/payment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ accepts_cash: this.checked })
    });
    const data = await res.json();
    console.log("Cash updated:", data.payment.accepts_cash);
  } catch (err) {
    console.error(err);
  }
});