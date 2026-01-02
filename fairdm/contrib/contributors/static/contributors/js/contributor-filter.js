// Contributor filtering and animation
document.addEventListener('DOMContentLoaded', function () {
  let currentContributorType = 'all'
  let currentRole = 'all'

  function filterContributors() {
    const items = document.querySelectorAll('.contributor-item')

    items.forEach(item => {
      const ctype = item.dataset.ctype
      const roles = item.dataset.roles ? item.dataset.roles.split(',').map(r => r.trim()) : []

      let showByType = currentContributorType === 'all' || ctype === currentContributorType
      let showByRole = currentRole === 'all' || roles.includes(currentRole)

      if (showByType && showByRole) {
        // Show item
        item.classList.remove('hiding', 'hidden')
      } else {
        // Hide item
        if (!item.classList.contains('hiding') && !item.classList.contains('hidden')) {
          item.classList.add('hiding')
          setTimeout(() => {
            item.classList.add('hidden')
          }, 600) // Match transition duration
        }
      }
    })
  }

  function updateRoleFilters() {
    const roleOptions = document.querySelectorAll('input[name="role-filter"]')

    roleOptions.forEach(option => {
      const forCtype = option.dataset.forCtype
      const optionContainer = option.closest('.form-check')

      if (!forCtype || currentContributorType === 'all' || forCtype === currentContributorType) {
        optionContainer.style.display = ''
      } else {
        optionContainer.style.display = 'none'
        if (option.checked) {
          // Reset to "all" if current selection is being hidden
          document.querySelector('input[name="role-filter"][value="all"]').checked = true
          currentRole = 'all'
        }
      }
    })
  }

  // Contributor type filter
  document.querySelectorAll('input[name="contributor-filter"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      currentContributorType = e.target.value
      updateRoleFilters()
      filterContributors()
    })
  })

  // Role filter
  document.querySelectorAll('input[name="role-filter"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      currentRole = e.target.value
      filterContributors()
    })
  })

  // Initial setup
  updateRoleFilters()
  filterContributors()

  // Handle HTMX events for contribution updates
  document.body.addEventListener('htmx:afterSwap', function (event) {
    // After successful form submission in modal, close modal and refresh list
    if (event.detail.target.id === 'contribution-modal-content') {
      // Check if the response indicates success (you may need to adjust based on your backend response)
      const successIndicator = event.detail.target.querySelector('.alert-success')
      if (successIndicator) {
        // Close modal after a short delay
        setTimeout(() => {
          const modal = bootstrap.Modal.getInstance(document.getElementById('contributionModal'))
          if (modal) {
            modal.hide()
          }
          // Reload the contributors list
          window.location.reload()
        }, 1000)
      }
    }
  })
})
