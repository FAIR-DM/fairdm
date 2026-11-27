// The Contributors tab: closing the sheet when a change is saved, the notice's timer and the caret.
(() => {
  // A change saved: close the sheet it was made in.
  document.addEventListener("contrib:done", () => {
    document.querySelectorAll("dialog[open][data-mvp-sheet]").forEach((sheet) => sheet.close());
  });

  // The toast goes after a few seconds, unless the pointer or focus is on it.
  let timer = null;
  function arm() {
    clearTimeout(timer);
    const toast = document.querySelector("[data-contrib-toast]");
    if (!toast) return;
    const hold = () => toast.matches(":hover, :focus-within");
    const later = () => {
      timer = setTimeout(() => (hold() ? later() : toast.setAttribute("data-gone", "")), 6000);
    };
    later();
  }
  document.addEventListener("DOMContentLoaded", arm);
  document.addEventListener("htmx:afterSettle", (event) => {
    if (event.detail.target?.id === "contrib-region" || event.target?.id === "contrib-region") arm();
    // Put the caret in a sheet's first field once a step has arrived.
    const field = document.querySelector("dialog[open] [data-contrib-autofocus]");
    if (field && !field.dataset.focused) {
      field.dataset.focused = "1";
      if (matchMedia("(pointer: fine)").matches) field.focus();
    }
  });
})();
