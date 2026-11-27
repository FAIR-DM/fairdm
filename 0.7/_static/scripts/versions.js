/* The version switcher and the version warning banner: both read the one file of versions, listed at the address the switcher carries. */
(function () {
  "use strict";

  const body = document.body;
  const switchers = document.querySelectorAll("[data-daisy-json-url]:not([data-daisy-version-banner])");
  const banner = document.querySelector("[data-daisy-version-banner]");
  const first = switchers[0] || banner;
  if (!first) return;

  const jsonUrl = first.dataset.daisyJsonUrl;
  const match = first.dataset.daisyVersionMatch;
  const siteRoot = new URL(body.dataset.daisyRoot === "#" ? "./" : body.dataset.daisyRoot || "", location.href);

  /* A full address as given, a path from the server's root against the origin, anything else from the site's root. */
  function resolve(address) {
    const text = String(address || "").trim();
    if (/^([a-z][a-z0-9+.-]*:|\/\/)/i.test(text)) return new URL(text, location.href);
    if (text.startsWith("/")) return new URL(text, location.origin);
    return new URL(text, siteRoot);
  }

  /* A link is made only from a web address; an entry with any other is listed as text. */
  function webAddress(address) {
    try {
      const found = resolve(address);
      return found.protocol === "http:" || found.protocol === "https:" ? found : null;
    } catch (error) {
      return null;
    }
  }

  function nameOf(entry) {
    return entry.name || entry.version;
  }

  /* The same page of a version when it holds one, its home page otherwise. */
  function go(root, event) {
    event.preventDefault();
    const base = root.href.replace(/\/?$/, "/");
    const target = base + window.sphinxDaisyui.pageAddress.path() + location.hash;
    fetch(target, { method: "HEAD" })
      .then((response) => { location.href = response.ok ? target : root.href; })
      .catch(() => { location.href = root.href; });
  }

  function fillSwitcher(box, versions) {
    const list = box.querySelector("[data-daisy-version-list]");
    const label = box.querySelector("[data-daisy-version-label]");
    versions.forEach((entry) => {
      const item = document.createElement("li");
      const root = webAddress(entry.url);
      const current = entry.version === match;
      const row = document.createElement(root ? "a" : "span");
      row.textContent = nameOf(entry);
      if (root) {
        row.href = root.href;
        row.addEventListener("click", (event) => go(root, event));
      }
      if (current) {
        row.classList.add("menu-active");
        row.setAttribute("aria-current", "true");
        const hidden = document.createElement("span");
        hidden.className = "sr-only";
        hidden.textContent = " " + box.dataset.textCurrent;
        row.append(hidden);
        if (label) label.textContent = nameOf(entry);
      }
      if (entry.preferred) {
        const badge = document.createElement("span");
        badge.className = "badge badge-sm badge-soft badge-success";
        badge.textContent = box.dataset.textPreferred;
        row.append(badge);
      }
      item.append(row);
      list.append(item);
    });
  }

  function fillBanner(versions) {
    const preferred = versions.find((entry) => entry.preferred);
    if (!preferred || preferred.version === match) return;
    const current = versions.find((entry) => entry.version === match);
    const text = banner.dataset.textMessage
      .replace("%(version)s", current ? nameOf(current) : match)
      .replace("%(preferred)s", nameOf(preferred));
    banner.textContent = text + " ";
    const root = webAddress(preferred.url);
    if (root) {
      const link = document.createElement("a");
      link.className = "link font-medium";
      link.href = root.href;
      link.textContent = banner.dataset.textLink;
      link.addEventListener("click", (event) => go(root, event));
      banner.append(link);
    }
    banner.hidden = false;
  }

  fetch(resolve(jsonUrl).href)
    .then((response) => response.json())
    .then((versions) => {
      if (!Array.isArray(versions)) throw new Error("not a list");
      switchers.forEach((box) => fillSwitcher(box, versions));
      if (banner) fillBanner(versions);
    })
    .catch(() => switchers.forEach((box) => box.remove()));
})();
