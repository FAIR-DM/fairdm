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

  // From: https://github.com/dallaslu/bootstrap-5-multi-level-dropdown
  // License: MIT 
  // Credit: Dallas Lu (https://github.com/dallaslu)
  (function ($bs) {
    const CLASS_NAME = 'has-child-dropdown-show'
    $bs.Dropdown.prototype.toggle = function (_orginal) {
      return function () {
        document.querySelectorAll('.' + CLASS_NAME).forEach(function (e) {
          e.classList.remove(CLASS_NAME)
        })
        let dd = this._element.closest('.dropdown').parentNode.closest('.dropdown')
        for (; dd && dd !== document; dd = dd.parentNode.closest('.dropdown')) {
          dd.classList.add(CLASS_NAME)
        }
        return _orginal.call(this)
      }
    }($bs.Dropdown.prototype.toggle)

    document.querySelectorAll('.dropdown').forEach(function (dd) {
      dd.addEventListener('hide.bs.dropdown', function (e) {
        if (this.classList.contains(CLASS_NAME)) {
          this.classList.remove(CLASS_NAME)
          e.preventDefault()
        }
        e.stopPropagation() // do not need pop in multi level mode
      })
    })

    // for hover
    document.querySelectorAll('.dropdown-hover, .dropdown-hover-all .dropdown').forEach(function (dd) {
      dd.addEventListener('mouseenter', function (e) {
        let toggle = e.target.querySelector(':scope>[data-bs-toggle="dropdown"]')
        if (!toggle.classList.contains('show')) {
          $bs.Dropdown.getOrCreateInstance(toggle).toggle()
          dd.classList.add(CLASS_NAME)
          $bs.Dropdown.clearMenus(e)
        }
      })
      dd.addEventListener('mouseleave', function (e) {
        let toggle = e.target.querySelector(':scope>[data-bs-toggle="dropdown"]')
        if (toggle.classList.contains('show')) {
          $bs.Dropdown.getOrCreateInstance(toggle).toggle()
        }
      })
    })
  })(bootstrap)