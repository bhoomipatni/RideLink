//testing "database"
const rides = [
  { driver: "Alex", destination: "Boston", time: "5pm" },
  { driver: "Sam", destination: "NYC", time: "3pm" }
];

// Dropdown menu toggle
const dropdownToggle = document.querySelector('.dropdown-toggle');
const dropdownMenu = document.querySelector('.dropdown-menu');

if (dropdownToggle) {
  dropdownToggle.addEventListener('click', function (e) {
    e.preventDefault();
    dropdownMenu.style.display = dropdownMenu.style.display === 'block' ? 'none' : 'block';
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.dropdown')) {
      dropdownMenu.style.display = 'none';
    }
  });
}