// The import page: the drop zone shows the chosen file, and a form is sent once.
(function () {
  function bindDrop(root) {
    root.querySelectorAll("[data-ie-drop]").forEach(function (drop) {
      if (drop.dataset.ieBound) return;
      drop.dataset.ieBound = "1";
      var input = drop.querySelector("[data-ie-file]");
      var chosen = drop.querySelector("[data-ie-chosen]");
      var text = drop.querySelector("[data-ie-drop-text]");
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
    root.querySelectorAll("form[data-ie-upload], form[data-ie-once]").forEach(function (form) {
      if (form.dataset.ieGuarded) return;
      form.dataset.ieGuarded = "1";
      form.addEventListener("submit", function (event) {
        if (form.dataset.ieSent) { event.preventDefault(); return; }
        form.dataset.ieSent = "1";
        var button = event.submitter;
        if (button) {
          setTimeout(function () { button.disabled = true; button.classList.add("btn-disabled"); }, 0);
        }
      });
    });
  }
  document.addEventListener("DOMContentLoaded", function () { bindDrop(document); });
  document.addEventListener("htmx:afterSettle", function (e) { bindDrop(e.target); });
})();
