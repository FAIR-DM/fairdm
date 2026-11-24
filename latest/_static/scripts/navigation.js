/* The navigation: each sidebar toggle opens and closes its branch, the current page's entry is brought into view, and the header links line up and open their menu from the keyboard. */
(function () {
  "use strict";

  /* The stylesheet hides a closed branch's list from its toggle's state. */
  document.querySelectorAll(".daisy-nav-toggle").forEach((toggle) => {
    toggle.addEventListener("click", () => {
      const open = toggle.getAttribute("aria-expanded") !== "true";
      toggle.setAttribute("aria-expanded", String(open));
    });
  });

  /* A menu in the header opens when its control has focus, as daisyUI draws it.
     Escape closes it and leaves focus on the control, which would open it again
     but for the class that holds it shut until the control is used or left. */
  document.querySelectorAll(".daisy-dropdown").forEach((menu) => {
    const control = menu.querySelector(":scope > [role='button']");
    if (!control) return;
    menu.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      menu.classList.add("dropdown-close");
      control.focus();
    });
    control.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      menu.classList.remove("dropdown-close");
    });
    control.addEventListener("click", () => menu.classList.remove("dropdown-close"));
    menu.addEventListener("focusout", (event) => {
      if (!menu.contains(event.relatedTarget)) menu.classList.remove("dropdown-close");
    });
  });

  /* The header links start where the article does. The margin is measured, as it
     depends on the layout code, the sidebar's width and the window's. */
  const slot = document.querySelector('[data-navbar-align="content"]');
  const article = document.querySelector(".daisy-area-main > div");
  const wide = window.matchMedia("(min-width: 64rem)");
  const alignHeaderLinks = () => {
    if (!slot || !article) return;
    slot.style.marginInlineStart = "";
    const first = slot.querySelector("a, [role='button']");
    if (!wide.matches || !first) return;
    const gap = article.getBoundingClientRect().left - first.getBoundingClientRect().left;
    if (gap > 0) slot.style.marginInlineStart = `${gap}px`;
  };
  alignHeaderLinks();
  window.addEventListener("resize", alignHeaderLinks);
  if (document.fonts) document.fonts.ready.then(alignHeaderLinks);

  /* Scrolling the sidebar alone keeps the page where the reader left it. */
  const scroller = document.querySelector(".daisy-sidebar-scroll");
  const current = document.querySelector('.daisy-nav [aria-current="page"]');
  if (!scroller || !current) return;
  const box = scroller.getBoundingClientRect();
  const entry = current.getBoundingClientRect();
  /* An entry within a few lines of the edge counts as out of view, as in the prototype. */
  if (entry.top < box.top || entry.bottom > box.bottom - 40) {
    scroller.scrollTop += entry.top - box.top - box.height / 3;
  }
})();
