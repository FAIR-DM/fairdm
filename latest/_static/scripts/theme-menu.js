/* The theme menu: a choice is drawn and kept through the mode script, the menu closes with focus back on its button, and the current choice is marked for sight and for a screen reader. */
(function () {
  "use strict";

  const mode = window.sphinxDaisyui && window.sphinxDaisyui.mode;
  if (!mode) return;

  const menus = new Set();
  document
    .querySelectorAll("[data-daisy-set-mode], [data-daisy-set-theme]")
    .forEach((button) => {
      const menu = button.closest(".daisy-dropdown");
      if (menu) menus.add(menu);
    });

  menus.forEach((menu) => {
    const trigger = menu.querySelector(":scope > [role='button']");
    const modeButtons = menu.querySelectorAll("[data-daisy-set-mode]");
    const themeButtons = menu.querySelectorAll("[data-daisy-set-theme]");
    const names = (menu.dataset.daisyModeNames || "").split("|");
    const modeNames = { auto: names[0], light: names[1], dark: names[2] };
    const announcement = menu.querySelector("[data-daisy-mode-current]");

    function mark(button, on) {
      button.setAttribute("aria-pressed", String(on));
      button.classList.toggle("menu-active", on);
    }

    /* The buttons of the choice on the page are pressed, the others are not. */
    function show() {
      const current = mode.choice();
      let name = modeNames[current] || "";
      modeButtons.forEach((button) => {
        mark(button, button.dataset.daisySetMode === current);
      });
      themeButtons.forEach((button) => {
        const picked = "theme:" + button.dataset.daisySetTheme === current;
        mark(button, picked);
        if (picked) name = button.textContent.trim();
      });
      if (announcement) announcement.textContent = name;
    }

    /* Closed as navigation.js closes it on Escape: held shut until the button is used again. */
    function close() {
      if (menu.contains(document.activeElement)) document.activeElement.blur();
      menu.classList.add("dropdown-close");
      if (trigger) trigger.focus();
    }

    menu.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button || !menu.contains(button)) return;
      if (button.dataset.daisySetMode) {
        mode.choose(button.dataset.daisySetMode);
      } else if (button.dataset.daisySetTheme) {
        mode.choose("theme:" + button.dataset.daisySetTheme);
      } else {
        return;
      }
      close();
    });

    document.addEventListener("sphinx-daisyui:mode", show);
    show();
  });
})();
