/* Back to top: offered when the reader scrolls up, far down a page. */
(function () {
  "use strict";

  const button = document.querySelector(".daisy-back-to-top");
  if (!button) return;

  let last = window.scrollY;
  window.addEventListener(
    "scroll",
    () => {
      const y = window.scrollY;
      button.hidden = !(y < last && y > 600);
      last = y;
    },
    { passive: true },
  );

  button.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
    const main = document.getElementById("main-content");
    if (main) main.focus({ preventScroll: true });
    button.hidden = true;
  });
})();
