(function () {

  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(';') : []
    for (let cookie of cookies) {
      cookie = cookie.trim()
      if (cookie.startsWith(name + '=')) {
        return decodeURIComponent(cookie.substring(name.length + 1))
      }
    }
    return null
  }

  function qs(selector, root = document) {
    return root.querySelector(selector)
  }

  function qsa(selector, root = document) {
    return Array.from(root.querySelectorAll(selector))
  }

  function initMartor(container) {
    container.dispatchEvent(new Event('martor.init'))

    const fieldName = container.dataset.fieldName
    const textarea = qs(`#id_${fieldName}`)
    const editorId = `martor-${fieldName}`
    const editor = ace.edit(editorId)

    const editorConfig = JSON.parse(
      textarea.dataset.enableConfigs.replace(/'/g, '"')
    )

    // --- ACE SETUP ---
    editor.setTheme('ace/theme/github')
    editor.session.setMode('ace/mode/markdown')
    editor.session.setUseWrapMode(true)
    editor.setOptions({
      enableBasicAutocompletion: true,
      enableSnippets: true,
      enableLiveAutocompletion: true,
      enableMultiselect: false
    })

    if (editorConfig.living === 'true') {
      container.classList.add('enable-living')
    }

    // --- COMPLETERS ---
    const emojiWordCompleter = {
      getCompletions(editor, session, pos, prefix, callback) {
        const wordList = typeof emojis !== "undefined" ? emojis : []
        const token = editor.session.getTokenAt(pos.row, pos.column)

        if (!token || !token.value) return

        const lastToken = token.value.split(/\s+/).pop()

        if (lastToken.startsWith(':')) {
          callback(null, wordList.map(word => ({
            caption: word,
            value: word.replace(':', '') + ' ',
            meta: 'emoji'
          })))
        }
      }
    }

    const mentionWordCompleter = {
      getCompletions(editor, session, pos, prefix, callback) {
        const token = editor.session.getTokenAt(pos.row, pos.column)
        if (!token || !token.value) return

        const lastToken = token.value.split(/\s+/).pop()

        if (lastToken.startsWith('@[')) {
          const username = lastToken.replace(/[@\[\]]/g, '')

          fetch(textarea.dataset.searchUsersUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ username })
          })
            .then(res => res.json())
            .then(data => {
              if (data.status === 200) {
                const list = data.data.map(u => u.username)
                callback(null, list.map(word => ({
                  caption: word,
                  value: word,
                  meta: 'username'
                })))
              }
            })
        }
      }
    }

    editor.completers = editorConfig.mention === 'true'
      ? [emojiWordCompleter, mentionWordCompleter]
      : [emojiWordCompleter]

    // --- HIDE TEXTAREA ---
    textarea.style.display = 'none'

    // --- SYNC EDITOR → TEXTAREA ---
    editor.on('change', () => {
      textarea.value = editor.getValue()
    })

    // --- PREVIEW ---
    const previewTab = qs(`#nav-preview-${fieldName}`)
    let timeoutID

    function refreshPreview() {
      const form = new FormData()
      form.append('content', textarea.value)
      form.append('csrfmiddlewaretoken', getCookie('csrftoken'))

      previewTab.classList.add('martor-preview-stale')

      fetch(textarea.dataset.markdownfyUrl, {
        method: 'POST',
        body: form
      })
        .then(res => res.text())
        .then(html => {
          previewTab.innerHTML = html || '<p>Nothing to preview</p>'
          previewTab.classList.remove('martor-preview-stale')

          document.dispatchEvent(new CustomEvent('martor:preview', {
            detail: previewTab
          }))

          if (editorConfig.hljs === 'true' && window.hljs) {
            qsa('pre').forEach(block => hljs.highlightElement(block))
          }
        })
        .catch(err => console.error(err))
    }

    function refreshPreviewTimeout() {
      clearTimeout(timeoutID)
      timeoutID = setTimeout(
        refreshPreview,
        parseInt(textarea.dataset.saveTimeout, 10)
      )
    }

    window.addEventListener('load', refreshPreview)

    if (editorConfig.living === 'true') {
      editor.on('change', refreshPreviewTimeout)
    }

    // --- TOOLBAR BUTTONS ---
    function bindClick(selector, fn) {
      qsa(`${selector}[data-field-name="${fieldName}"]`)
        .forEach(el => el.addEventListener('click', () => fn(editor)))
    }

    function wrapSelection(editor, before, after = before) {
      const range = editor.getSelectionRange()

      if (editor.selection.isEmpty()) {
        const pos = editor.getCursorPosition()
        editor.session.insert(pos, ` ${before}${after} `)
        editor.selection.moveTo(pos.row, pos.column + before.length + 1)
      } else {
        const text = editor.session.getTextRange(range)
        editor.session.replace(range, `${before}${text}${after}`)
      }
      editor.focus()
    }

    bindClick('.markdown-bold', ed => wrapSelection(ed, '**'))
    bindClick('.markdown-italic', ed => wrapSelection(ed, '_'))
    bindClick('.markdown-code', ed => wrapSelection(ed, '`'))

    // --- FULLSCREEN ---
    const btnMax = qs(`.markdown-toggle-maximize[data-field-name="${fieldName}"]`)

    if (btnMax) {
      btnMax.addEventListener('click', () => {
        container.classList.toggle('main-martor-fullscreen')
        document.body.classList.toggle('overflow')
        editor.resize()
      })
    }

    // --- ESC TO EXIT FULLSCREEN ---
    document.addEventListener('keyup', (e) => {
      if (e.key === 'Escape' &&
        container.classList.contains('main-martor-fullscreen')) {
        btnMax?.click()
      }
    })

    // --- INITIAL VALUE ---
    editor.setValue(textarea.value || '', -1)
  }

  // --- INIT ALL ---
  document.addEventListener('DOMContentLoaded', () => {
    qsa('.main-martor').forEach(initMartor)
  })

})()
