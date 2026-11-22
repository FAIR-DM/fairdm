// Spreadsheet import (prototype): the drop zone, one submit per form, and closing the export menu.
(function () {
  function bindDrop(root) {
    root.querySelectorAll("[data-tx-drop]").forEach(function (drop) {
      if (drop.dataset.txBound) return;
      drop.dataset.txBound = "1";
      var input = drop.querySelector("[data-tx-file]");
      var chosen = drop.querySelector("[data-tx-chosen]");
      var text = drop.querySelector("[data-tx-drop-text]");
      function show() {
        var file = input.files && input.files[0];
        if (!file) return;
        var kb = file.size / 1024;
        var size = kb > 1024 ? (kb / 1024).toFixed(1) + " MB" : Math.max(1, Math.round(kb)) + " KB";
        chosen.textContent = file.name + " · " + size;
        chosen.hidden = false;
        text.hidden = true;
        drop.classList.add("has-file");
      }
      input.addEventListener("change", show);
      ["dragenter", "dragover"].forEach(function (e) {
        drop.addEventListener(e, function () { drop.classList.add("is-over"); });
      });
      ["dragleave", "drop"].forEach(function (e) {
        drop.addEventListener(e, function () { drop.classList.remove("is-over"); });
      });
      show();
    });
    root.querySelectorAll("form[data-tx-upload], form[data-tx-once]").forEach(function (form) {
      if (form.dataset.txOnce) return;
      form.dataset.txOnce = "1";
      form.addEventListener("submit", function (event) {
        if (form.dataset.txSent) { event.preventDefault(); return; }
        form.dataset.txSent = "1";
        var button = event.submitter;
        if (button) {
          setTimeout(function () { button.disabled = true; button.classList.add("btn-disabled"); }, 0);
        }
      });
    });
  }
  document.addEventListener("click", function (event) {
    document.querySelectorAll("details[data-tx-menu][open]").forEach(function (menu) {
      // A click outside closes the menu, and so does choosing a file to download.
      if (!menu.contains(event.target) || event.target.closest("a[download]")) {
        setTimeout(function () { menu.removeAttribute("open"); }, 0);
      }
    });
  });
  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    document.querySelectorAll("details[data-tx-menu][open]").forEach(function (menu) {
      menu.removeAttribute("open");
      menu.querySelector("summary").focus();
    });
  });
  document.addEventListener("DOMContentLoaded", function () { bindDrop(document); });
  document.addEventListener("htmx:afterSettle", function (e) { bindDrop(e.target); });
})();
