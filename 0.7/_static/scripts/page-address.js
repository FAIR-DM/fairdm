/* Page addresses: where a page of the site is, from any page, for the search dialog and the version switcher. The rule is Sphinx's own, from its search script. */
(function () {
  "use strict";

  window.sphinxDaisyui = window.sphinxDaisyui || {};

  const body = document.body;
  /* Sphinx writes "#" for the root on the top page of a dirhtml site. */
  const root = body.dataset.daisyRoot === "#" ? "./" : body.dataset.daisyRoot || "";
  const linkSuffix = body.dataset.daisyLinkSuffix || "";
  const dirhtml = body.dataset.daisyBuilder === "dirhtml";

  /* The address of a page without the root: a directory for a dirhtml build. */
  function relative(docname) {
    if (!dirhtml) return docname + linkSuffix;
    if (docname === "index") return "";
    if (docname.endsWith("/index")) return docname.slice(0, -"index".length);
    return docname + "/";
  }

  /* The address of a page, with its anchor when it has one, from the page being read. */
  function url(docname, anchor) {
    const name = anchor ? String(anchor).replace(/^#/, "") : "";
    return root + relative(docname) + (name ? "#" + name : "");
  }

  /* The address of the page being read from the site's root, so another version's root can take it. */
  function path() {
    return relative(body.dataset.daisyPage);
  }

  window.sphinxDaisyui.pageAddress = { url: url, path: path };
})();
