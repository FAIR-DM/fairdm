/* Colour mode: sets the theme on <html> before the body is added, from the reader's choice or the site's starting mode. */
(function () {
  "use strict";

  window.sphinxDaisyui = window.sphinxDaisyui || {};

  const root = document.documentElement;
  const site = document.currentScript.dataset;
  const offered = (site.themes || "").split(" ").filter(Boolean);
  const themePrefix = "theme:";
  const start = site.defaultMode || "auto";

  root.dataset.lightTheme = site.lightTheme;
  root.dataset.darkTheme = site.darkTheme;
  root.dataset.defaultMode = start;

  /* One entry per site, so two sites on one host keep their own choices. */
  function storageKey() {
    const base = new URL(root.dataset.content_root || "./", location.href);
    return "sphinx-daisyui:" + base.pathname;
  }

  /* The reader's saved choice, or null when there is none or storage is blocked. */
  function stored() {
    try {
      return localStorage.getItem(storageKey());
    } catch (error) {
      return null;
    }
  }

  function setMode(choice) {
    const dark =
      choice === "dark" ||
      (choice === "auto" && matchMedia("(prefers-color-scheme: dark)").matches);
    root.dataset.theme = dark ? site.darkTheme : site.lightTheme;
    root.dataset.mode = dark ? "dark" : "light";
    root.dataset.modeChoice = choice;
  }

  function setTheme(name) {
    root.dataset.theme = name;
    root.dataset.modeChoice = "theme";
    // A named theme says whether it is light or dark through its color-scheme.
    const scheme = getComputedStyle(root).colorScheme || "";
    root.dataset.mode = scheme.includes("dark") ? "dark" : "light";
  }

  /* Tell the page's other scripts that the drawn choice changed. */
  function announce() {
    document.dispatchEvent(new CustomEvent("sphinx-daisyui:mode"));
  }

  /* Draw a choice: "auto", "light", "dark" or "theme:<name>". A choice the site no longer offers draws the starting mode. Returns the choice drawn. */
  function apply(choice) {
    if (choice === "auto" || choice === "light" || choice === "dark") {
      setMode(choice);
      announce();
      return choice;
    }
    if (typeof choice === "string" && choice.startsWith(themePrefix)) {
      const name = choice.slice(themePrefix.length);
      if (offered.includes(name)) {
        setTheme(name);
        announce();
        return choice;
      }
    }
    setMode(start);
    announce();
    return start;
  }

  /* Draw a choice and keep it for this site. A browser that blocks storage still changes the page. */
  function choose(choice) {
    const drawn = apply(choice);
    try {
      localStorage.setItem(storageKey(), drawn);
    } catch (error) {
      /* The choice lasts for this page only. */
    }
    return drawn;
  }

  /* The choice on the page now: a mode, or "theme:<name>" for a picked theme. */
  function choice() {
    const current = root.dataset.modeChoice;
    return current === "theme" ? themePrefix + root.dataset.theme : current;
  }

  window.sphinxDaisyui.mode = {
    apply: apply,
    choose: choose,
    stored: stored,
    choice: choice,
    offered: offered,
  };

  /* In auto the page follows the system, also when the theme menu is not placed. */
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if (root.dataset.modeChoice === "auto") apply("auto");
  });

  apply(stored());
})();
