/**
 * Table View JavaScript - Mobile search drawer and responsive functionality
 */

// Mobile Search Drawer Functions
function toggleSearchDrawer() {
  const drawer = document.getElementById('searchDrawer')
  drawer.classList.toggle('show')

  // Focus on the search input when drawer opens
  if (drawer.classList.contains('show')) {
    const searchInput = drawer.querySelector('input[type="text"]')
    setTimeout(() => searchInput.focus(), 100)
  }
}

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {

  // Close drawer when clicking outside
  document.addEventListener('click', function (event) {
    const drawer = document.getElementById('searchDrawer')
    const searchButton = document.querySelector('.mobile-controls button[onclick="toggleSearchDrawer()"]')

    if (drawer && drawer.classList.contains('show') &&
      !drawer.contains(event.target) &&
      searchButton && !searchButton.contains(event.target)) {
      drawer.classList.remove('show')
    }
  })

  // Close drawer on escape key
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      const drawer = document.getElementById('searchDrawer')
      if (drawer) {
        drawer.classList.remove('show')
      }
    }
  })

  // Optional: Initialize select all checkbox functionality
  const selectAllCheckbox = document.getElementById('selectAll')
  if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', function () {
      const rowCheckboxes = document.querySelectorAll('.table-container tbody input[type="checkbox"]')
      rowCheckboxes.forEach(checkbox => {
        checkbox.checked = this.checked
      })
    })
  }

  // Optional: Update select all when individual checkboxes change
  const rowCheckboxes = document.querySelectorAll('.table-container tbody input[type="checkbox"]')
  rowCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', function () {
      const allCheckboxes = document.querySelectorAll('.table-container tbody input[type="checkbox"]')
      const checkedCheckboxes = document.querySelectorAll('.table-container tbody input[type="checkbox"]:checked')
      const selectAllCheckbox = document.getElementById('selectAll')

      if (selectAllCheckbox) {
        if (checkedCheckboxes.length === 0) {
          selectAllCheckbox.indeterminate = false
          selectAllCheckbox.checked = false
        } else if (checkedCheckboxes.length === allCheckboxes.length) {
          selectAllCheckbox.indeterminate = false
          selectAllCheckbox.checked = true
        } else {
          selectAllCheckbox.indeterminate = true
        }
      }
    })
  })
})