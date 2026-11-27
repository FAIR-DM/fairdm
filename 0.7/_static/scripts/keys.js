/* Keyboard shortcuts: one place to ask whether the reader is typing, and one to bind a key, with or without Ctrl or ⌘. */
(function () {
  "use strict";

  window.sphinxDaisyui = window.sphinxDaisyui || {};

  /* True while the reader is in a field, so a shortcut leaves their typing alone. */
  function isTyping() {
    const el = document.activeElement;
    if (!el) return false;
    return el.matches("input, textarea, select") || el.isContentEditable;
  }

  /* Run a handler when a key is pressed. A plain shortcut ignores the key while Alt, Ctrl or Meta is held; with options.modifier it runs only while Ctrl or Meta is held, and not Alt. */
  function on(key, handler, options) {
    const modifier = Boolean(options && options.modifier);
    const wanted = key.toLowerCase();
    document.addEventListener("keydown", (event) => {
      if (event.altKey) return;
      if (modifier) {
        if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== wanted) return;
      } else if (event.key !== key || event.ctrlKey || event.metaKey) {
        return;
      }
      handler(event);
    });
  }

  window.sphinxDaisyui.keys = { isTyping: isTyping, on: on };
})();
