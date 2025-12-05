// Theme toggle functionality
function toggleTheme() {
  const html = document.documentElement
  const currentTheme = html.getAttribute('data-bs-theme')
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark'

  html.setAttribute('data-bs-theme', newTheme)

  // Update icons
  const desktopIcon = document.getElementById('themeIcon')
  const mobileIcon = document.getElementById('mobileThemeIcon')

  if (newTheme === 'dark') {
    desktopIcon.className = 'bi bi-moon-fill'
    mobileIcon.className = 'bi bi-moon-fill me-2'
  } else {
    desktopIcon.className = 'bi bi-sun-fill'
    mobileIcon.className = 'bi bi-sun-fill me-2'
  }

  // Store preference
  localStorage.setItem('theme', newTheme)
}

// Initialize theme from localStorage
document.addEventListener('DOMContentLoaded', function () {
  const savedTheme = localStorage.getItem('theme') || 'light'
  document.documentElement.setAttribute('data-bs-theme', savedTheme)

  const desktopIcon = document.getElementById('themeIcon')
  const mobileIcon = document.getElementById('mobileThemeIcon')

  if (savedTheme === 'dark') {
    desktopIcon.className = 'bi bi-moon-fill'
    mobileIcon.className = 'bi bi-moon-fill me-2'
  }
})

// Add event listeners
document.getElementById('themeToggle').addEventListener('click', toggleTheme)
document.getElementById('mobileThemeToggle').addEventListener('click', toggleTheme)

// Close mobile menu when clicking on actual navigation links (not collapse toggles)
document.querySelectorAll('#mobileNavbar .nav-link:not([data-bs-toggle="collapse"])').forEach(link => {
  link.addEventListener('click', (e) => {
    // Only close if it's an actual navigation link with href, not a collapse toggle
    if (link.getAttribute('href') && link.getAttribute('href') !== '#') {
      const offcanvas = bootstrap.Offcanvas.getInstance(document.getElementById('mobileNavbar'))
      if (offcanvas) {
        offcanvas.hide()
      }
    }
  })
})
