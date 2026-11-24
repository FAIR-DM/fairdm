// The Export menu of a records table: closes on a click outside it or on a download, and on Escape.
(function () {
  document.addEventListener("click", function (event) {
    document.querySelectorAll("details[data-ie-menu][open]").forEach(function (menu) {
      // A click outside closes the menu, and so does choosing a file to download.
      if (!menu.contains(event.target) || event.target.closest("a[download]")) {
        setTimeout(function () { menu.removeAttribute("open"); }, 0);
      }
    });
  });
  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    document.querySelectorAll("details[data-ie-menu][open]").forEach(function (menu) {
      menu.removeAttribute("open");
      menu.querySelector("summary").focus();
    });
  });
})();
