/* The search dialog: opened by a button or a key, it lists the pages, sections and API objects Sphinx's own search finds as the reader types. */
(function () {
  "use strict";

  const dialog = document.getElementById("daisy-search");
  const keys = window.sphinxDaisyui && window.sphinxDaisyui.keys;
  const address = window.sphinxDaisyui && window.sphinxDaisyui.pageAddress;
  if (!dialog || !keys || !address) return;

  const input = dialog.querySelector(".daisy-search-input");
  const results = dialog.querySelector("#daisy-search-results");
  const status = dialog.querySelector(".daisy-search-status");
  const text = dialog.dataset;
  const asYouType = text.daisyAsYouType !== "false";
  const MIN_LENGTH = 2;
  const TYPING_DELAY = 60;
  const POLL_DELAY = 50;
  const POLL_LIMIT = 10000;

  let opener = null;
  let loading = null;
  let unavailable = false;
  let timer = null;
  let chosen = -1;
  let typed = input.value;

  if (/Mac|iPhone|iPad/.test(navigator.platform)) {
    document.querySelectorAll("[data-daisy-mod]").forEach((key) => {
      key.textContent = "⌘";
    });
  }

  /* Wait until a condition holds, polling, and fail after the limit. */
  function until(condition) {
    return new Promise((resolve, reject) => {
      const started = Date.now();
      (function poll() {
        if (condition()) resolve();
        else if (Date.now() - started > POLL_LIMIT) reject(new Error("timeout"));
        else setTimeout(poll, POLL_DELAY);
      })();
    });
  }

  /* Append a script and resolve when it has loaded. */
  function addScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.addEventListener("load", resolve);
      script.addEventListener("error", reject);
      script.src = src;
      document.body.append(script);
    });
  }

  /* Load Sphinx's search once: the search page already holds it, any other page loads its three files in order. */
  function load() {
    if (loading) return loading;
    if (typeof Search !== "undefined") {
      loading = until(() => Search.hasIndex());
    } else {
      loading = addScript(text.daisyLanguageData)
        .then(() => addScript(text.daisySearchtools))
        .then(() => {
          /* Sphinx's own start-up empties every field named q. */
          input.value = typed;
          return addScript(text.daisySearchindex);
        })
        .then(() => until(() => Search.hasIndex()));
    }
    loading = loading.catch(() => {
      unavailable = true;
    });
    return loading;
  }

  function say(message) {
    status.hidden = false;
    status.textContent = message;
  }

  function clear() {
    results.replaceChildren();
    chosen = -1;
    input.removeAttribute("aria-activedescendant");
    input.setAttribute("aria-expanded", "false");
  }

  /* The text with each word marked, built from text nodes. */
  function marked(title, words) {
    const parts = [...new Set(words)]
      .filter((word) => word.length >= MIN_LENGTH)
      .sort((a, b) => b.length - a.length)
      .map((word) => word.replace(/[.*+?^${}()|[\]\\-]/g, "\\$&"));
    const nodes = [];
    if (!parts.length) return [document.createTextNode(title)];
    let last = 0;
    for (const match of title.matchAll(new RegExp(parts.join("|"), "gi"))) {
      if (match.index > last) nodes.push(title.slice(last, match.index));
      const mark = document.createElement("mark");
      mark.textContent = match[0];
      nodes.push(mark);
      last = match.index + match[0].length;
    }
    nodes.push(title.slice(last));
    return nodes;
  }

  function pageTitleOf(docname) {
    const index = Search._index;
    return index.titles[index.docnames.indexOf(docname)] || "";
  }

  /* Turn one of Sphinx's results into what the dialog draws: a badge, a title and the page it is on. */
  function describe(result) {
    const [docname, title, anchor, descr] = result;
    const page = pageTitleOf(docname);
    if (descr) {
      const gettext = typeof Documentation !== "undefined" ? Documentation.gettext : (s) => s;
      const tail = gettext(", in ") + page;
      const kind = descr.endsWith(tail) ? descr.slice(0, -tail.length) : descr;
      return { badge: kind, title: title, under: page };
    }
    if (anchor) {
      const head = page + " > ";
      return {
        badge: text.daisySection,
        title: title.startsWith(head) ? title.slice(head.length) : title,
        under: page,
      };
    }
    return { badge: text.daisyPage, title: title, under: "" };
  }

  function draw(result, highlight, position) {
    const [docname, , anchor] = result;
    const shown = describe(result);
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.id = "daisy-search-option-" + position;
    link.setAttribute("role", "option");
    link.setAttribute("aria-selected", "false");
    link.className = "flex items-start gap-3 py-2";
    link.href = address.url(docname, anchor);
    link.addEventListener("click", () => dialog.close());

    const badge = document.createElement("span");
    badge.className = "badge badge-sm badge-ghost mt-0.5 min-w-16 shrink-0 justify-center whitespace-nowrap capitalize";
    badge.textContent = shown.badge;
    const body = document.createElement("span");
    body.className = "min-w-0";
    const title = document.createElement("span");
    title.className = "block truncate font-medium";
    title.append(...marked(shown.title, [...highlight]));
    body.append(title);
    if (shown.under) {
      const under = document.createElement("span");
      under.className = "daisy-muted block truncate text-xs";
      under.textContent = shown.under;
      body.append(under);
    }
    link.append(badge, body);
    item.append(link);
    return item;
  }

  function run() {
    const query = input.value.trim();
    clear();
    if (unavailable) return say(text.daisyUnavailable);
    if (query.length < MIN_LENGTH) return say(text.daisyPrompt);
    let found;
    let highlight;
    try {
      const [q, terms, excluded, highlights, objects] = Search._parseQuery(query);
      highlight = highlights;
      found = Search._performSearch(q, terms, excluded, highlights, objects);
    } catch (error) {
      return say(text.daisyUnavailable);
    }
    /* Sphinx lists its results from the last to the best. */
    const best = found.slice().reverse();
    if (!best.length) return say(text.daisyNothing.replace("%(query)s", () => query));
    status.hidden = true;
    results.append(...best.map((result, position) => draw(result, highlight, position)));
    input.setAttribute("aria-expanded", "true");
  }

  /* Move the choice to a result, wrapping at both ends. */
  function choose(position) {
    const options = [...results.querySelectorAll("[role=option]")];
    if (!options.length) return;
    chosen = (position + options.length) % options.length;
    options.forEach((option, n) => {
      option.classList.toggle("menu-active", n === chosen);
      option.setAttribute("aria-selected", String(n === chosen));
    });
    options[chosen].scrollIntoView({ block: "nearest" });
    input.setAttribute("aria-activedescendant", options[chosen].id);
  }

  function open() {
    if (dialog.open) return;
    opener = document.activeElement;
    dialog.showModal();
    input.select();
    if (!asYouType) return;
    load().then(() => {
      if (input.value.trim()) run();
    });
  }

  dialog.addEventListener("close", () => {
    if (opener && opener.isConnected && document.activeElement !== opener) opener.focus();
  });

  input.addEventListener("input", () => {
    typed = input.value;
    if (!asYouType) return;
    clearTimeout(timer);
    timer = setTimeout(() => load().then(run), TYPING_DELAY);
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      choose(chosen + (event.key === "ArrowDown" ? 1 : -1));
    } else if (event.key === "Enter" && chosen >= 0) {
      event.preventDefault();
      const target = results.querySelectorAll("[role=option]")[chosen].href;
      dialog.close();
      location.href = target;
    }
  });

  document.querySelectorAll(".daisy-search-open").forEach((button) => {
    button.addEventListener("click", open);
  });
  dialog.querySelectorAll("[data-daisy-search-close]").forEach((button) => {
    button.addEventListener("click", () => dialog.close());
  });

  keys.on("k", (event) => {
    event.preventDefault();
    open();
  }, { modifier: true });
  keys.on("/", (event) => {
    if (keys.isTyping() || dialog.open) return;
    event.preventDefault();
    open();
  });
})();
