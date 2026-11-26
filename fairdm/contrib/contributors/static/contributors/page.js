// Prototype: the Contributors page. Never merged; see PROTOTYPE.md.
(() => {
  // A change saved: close the sheet it was made in.
  document.addEventListener("contrib:done", () => {
    document.querySelectorAll("dialog[open][data-mvp-sheet]").forEach((sheet) => sheet.close());
  });

  // The toast goes after a few seconds, unless the pointer or focus is on it.
  let timer = null;
  function arm() {
    clearTimeout(timer);
    const toast = document.querySelector("[data-contrib-toast]");
    if (!toast) return;
    const hold = () => toast.matches(":hover, :focus-within");
    const later = () => {
      timer = setTimeout(() => (hold() ? later() : toast.setAttribute("data-gone", "")), 6000);
    };
    later();
  }
  document.addEventListener("DOMContentLoaded", arm);
  document.addEventListener("htmx:afterSettle", (event) => {
    if (event.detail.target?.id === "contrib-region" || event.target?.id === "contrib-region") arm();
    // Put the caret in a sheet's first field once a step has arrived.
    const field = document.querySelector("dialog[open] [data-contrib-autofocus]");
    if (field && !field.dataset.focused) {
      field.dataset.focused = "1";
      if (matchMedia("(pointer: fine)").matches) field.focus();
    }
    registries();
  });

  // Live search of ORCID or ROR with Tom Select, its results always open beneath the field, as in
  // Tom Select's own inline remote example. Picking a match fills the name fields of the form.
  function registries() {
    if (!window.TomSelect) return;
    if (!TomSelect.prototype.contribNoClose) {
      TomSelect.define("no_close", function () {
        this.close = function () {};
      });
      TomSelect.prototype.contribNoClose = true;
    }
    document.querySelectorAll("dialog[open] [data-contrib-registry]").forEach((field) => {
      const select = field.querySelector("select");
      if (!select || select.tomselect) return;
      const form = select.form;
      const results = field.querySelector("[data-contrib-registry-results]");
      const ts = new TomSelect(select, {
        valueField: "id",
        labelField: "name",
        searchField: [],
        maxOptions: 10,
        create: false,
        dropdownParent: results,
        plugins: ["no_close"],
        shouldLoad: (query) => query.trim().length > 1,
        score: () => () => 1,
        load: (query, callback) => {
          fetch(`${field.dataset.contribRegistry}?q=${encodeURIComponent(query)}`, { headers: { Accept: "application/json" } })
            .then((answer) => answer.json())
            .then((json) => {
              ts.clearOptions((option) => option.id === ts.getValue());
              callback(json.results);
            })
            .catch(() => callback());
        },
        render: {
          option: (item) => `<div>${item.html || ""}</div>`,
          item: (item, escape) => `<div>${escape(item.name)} · ${escape(item.shown_id || item.id)}</div>`,
          no_results: () => "",
          loading: () => '<div class="p-2"><span class="loading loading-spinner loading-sm"></span></div>',
        },
        onChange: (value) => {
          const item = ts.options[value];
          if (!item || !form) return;
          ts.setTextboxValue("");
          if (field.dataset.contribRegistryKind === "orcid") {
            form.elements.first_name.value = item.given || "";
            form.elements.last_name.value = item.family || "";
          } else if (form.elements.new_name) {
            form.elements.new_name.value = item.name || "";
          }
        },
      });
      const query = field.dataset.contribRegistryQuery;
      if (query) {
        ts.setTextboxValue(query);
        ts.load(query);
      }
      if (matchMedia("(pointer: fine)").matches) ts.focus();
    });
  }
})();
