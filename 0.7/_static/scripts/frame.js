/* The page frame: the scrolled mark, the measured header, the drawer and the moving navbar_end. */
(function () {
  "use strict";

  const shell = document.querySelector(".daisy-layout");
  if (!shell) return;

  /* The header draws its line and shadow once the page has scrolled. */
  function markScrolled() {
    shell.classList.toggle("daisy-scrolled", window.scrollY > 0);
  }
  window.addEventListener("scroll", markScrolled, { passive: true });
  markScrolled();

  /* The header's height, so the sticky sidebars sit below it whatever it holds. */
  const header = shell.querySelector(".daisy-area-header");
  if (header && "ResizeObserver" in window) {
    new ResizeObserver(() => {
      const height = header.getBoundingClientRect().height;
      shell.style.setProperty("--daisy-header-height", height + "px");
    }).observe(header, { box: "border-box" });
  }

  /* Following a link in the navigation closes the drawer, and so does Escape. */
  const drawer = document.getElementById("daisy-drawer");
  document.querySelectorAll(".daisy-area-primary a").forEach((link) => {
    link.addEventListener("click", () => {
      if (drawer) drawer.checked = false;
    });
  });
  const opener = document.querySelector("[data-daisy-drawer-open]");
  const closer = document.querySelector("[data-daisy-drawer-close]");
  if (window.sphinxDaisyui && window.sphinxDaisyui.keys) {
    /* A menu in the drawer takes its own Escape, so the drawer stays open. */
    window.sphinxDaisyui.keys.on("Escape", (event) => {
      if (!drawer || !drawer.checked) return;
      if (event.target.closest && event.target.closest(".daisy-dropdown")) return;
      drawer.checked = false;
      if (opener) opener.focus();
    });
  }

  /* The menu and close buttons are labels, so they work without the script; Enter
     and Space press them from the keyboard, and focus follows the drawer. */
  [opener, closer].forEach((control) => {
    if (!control || !drawer) return;
    control.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      drawer.checked = !drawer.checked;
      const next = drawer.checked ? closer : opener;
      /* The drawer becomes visible as the next frame is drawn. */
      if (next) setTimeout(() => next.focus(), 50);
    });
  });

  /* Below 40rem the navbar's end items move into the drawer, and back above it. */
  const end = document.querySelector("[data-daisy-navbar-end]");
  const slot = document.querySelector("[data-daisy-navbar-end-slot]");
  if (end && slot) {
    const narrow = window.matchMedia("(width < 40rem)");
    const place = () => {
      const from = narrow.matches ? end : slot;
      const to = narrow.matches ? slot : end;
      while (from.firstElementChild) to.appendChild(from.firstElementChild);
    };
    narrow.addEventListener("change", place);
    place();
  }
})();
