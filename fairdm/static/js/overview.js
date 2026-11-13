// The overview pages' behaviour: description tabs, folding long text, copy buttons, the header's
// Cite button, the full-size view of the record's image, filter chips and maps. Linked from
// `overview/page.html`.
(function () {
  "use strict";

  function onReady(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  // Folds: a long description shows its first lines and a "Read more" button. It folds only when
  // that hides a few lines' worth, so a line or two more is simply shown.
  function checkFolds(root) {
    root.querySelectorAll(".ov-fold").forEach(function (fold) {
      var body = fold.querySelector(".ov-fold__body");
      if (!body || fold.dataset.opened === "true" || !body.offsetParent) return;
      fold.dataset.folded = "true";
      var hidden = body.scrollHeight - body.clientHeight;
      fold.dataset.folded = hidden > 64 ? "true" : "false";
      fold.dataset.overflowing = hidden > 64 ? "true" : "false";
    });
  }

  function initFolds(root) {
    checkFolds(root);
    root.querySelectorAll(".ov-fold__toggle").forEach(function (button) {
      button.addEventListener("click", function () {
        var fold = button.closest(".ov-fold");
        var open = fold.dataset.folded === "true";
        fold.dataset.folded = open ? "false" : "true";
        fold.dataset.opened = open ? "true" : "false";
        button.setAttribute("aria-expanded", open ? "true" : "false");
        button.querySelector("[data-label]").textContent = open
          ? button.dataset.less
          : button.dataset.more;
        if (!open) fold.scrollIntoView({ block: "nearest" });
      });
    });
    window.addEventListener("resize", function () { checkFolds(document); });
    window.addEventListener("load", function () { checkFolds(document); });
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(function () { checkFolds(document); });
    }
  }

  // Tabs: a role="tablist" of buttons, each controlling a panel. Arrow keys, Home and End move
  // between them.
  function initTabs(root) {
    root.querySelectorAll(".ov [role=tablist]").forEach(function (list) {
      var tabs = Array.prototype.slice.call(list.querySelectorAll("[role=tab]"));
      function select(tab, focus) {
        tabs.forEach(function (other) {
          var on = other === tab;
          other.setAttribute("aria-selected", on ? "true" : "false");
          other.tabIndex = on ? 0 : -1;
          var panel = document.getElementById(other.getAttribute("aria-controls"));
          if (panel) panel.hidden = !on;
        });
        if (focus) tab.focus();
        checkFolds(document);
      }
      tabs.forEach(function (tab, i) {
        tab.addEventListener("click", function () { select(tab); });
        tab.addEventListener("keydown", function (event) {
          var next = null;
          if (event.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
          if (event.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
          if (event.key === "Home") next = tabs[0];
          if (event.key === "End") next = tabs[tabs.length - 1];
          if (next) {
            event.preventDefault();
            select(next, true);
          }
        });
      });
    });
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    try {
      document.execCommand("copy");
    } finally {
      document.body.removeChild(area);
    }
    return Promise.resolve();
  }

  // Copy buttons: data-copy holds the text, or data-copy-from names the element to read it from.
  function initCopy(root) {
    root.querySelectorAll("[data-copy], [data-copy-from]").forEach(function (button) {
      button.addEventListener("click", function () {
        var text = button.dataset.copy;
        if (button.dataset.copyFrom) {
          var source = document.getElementById(button.dataset.copyFrom);
          text = source ? source.textContent : "";
        }
        copyText(text).then(function () {
          button.setAttribute("data-copied", "true");
          setTimeout(function () { button.removeAttribute("data-copied"); }, 1600);
          var status = button.parentElement.querySelector(".ov-copied");
          if (status) {
            status.hidden = false;
            setTimeout(function () { status.hidden = true; }, 1600);
          }
        });
      });
    });
  }

  // The header's Cite button: scroll to the citation and point at it.
  function initJumpToCite(root) {
    root.querySelectorAll("[data-jump-cite]").forEach(function (button) {
      button.addEventListener("click", function (event) {
        var target = document.getElementById("cite");
        if (!target) return;
        event.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        target.classList.add("ov-pulse");
        setTimeout(function () { target.classList.remove("ov-pulse"); }, 1400);
      });
    });
  }

  // A button with data-opens shows the dialog it names, such as the record's image at full size.
  function initDialogs(root) {
    root.querySelectorAll("[data-opens]").forEach(function (button) {
      button.addEventListener("click", function () {
        var dialog = document.getElementById(button.dataset.opens);
        if (dialog) dialog.showModal();
      });
    });
  }

  // Filter chips: a group with data-filter-chips names a list, and each chip shows only the rows
  // whose data-type is its data-value (an empty value shows them all). The list's "and n more"
  // link, marked data-filter-more with the same name, counts every type, so it hides while a
  // type is chosen.
  function initChips(root) {
    root.querySelectorAll("[data-filter-chips]").forEach(function (group) {
      var name = group.dataset.filterChips;
      var list = document.getElementById(name);
      var chips = group.querySelectorAll(".ov-chip");
      var more = document.querySelector("[data-filter-more='" + name + "']");
      if (!list) return;
      chips.forEach(function (chip) {
        chip.addEventListener("click", function () {
          var value = chip.dataset.value;
          chips.forEach(function (other) {
            other.setAttribute("aria-pressed", other === chip ? "true" : "false");
          });
          list.querySelectorAll("li[data-type]").forEach(function (row) {
            row.hidden = Boolean(value) && row.dataset.type !== value;
          });
          if (more) more.hidden = Boolean(value);
        });
      });
    });
  }

  // Maps, drawn with MapLibre, which the page loads when it has one. Tiles from OpenFreeMap, which
  // needs no key.
  function cssVar(el, name) {
    return getComputedStyle(el).getPropertyValue(name).trim();
  }

  // The tiles' credits, closed behind their (i) button until someone opens them. MapLibre opens
  // the compact control on a wide map, so it is closed again once the map has drawn.
  function addAttribution(map) {
    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");
    function close() {
      map.getContainer().querySelectorAll(".maplibregl-ctrl-attrib").forEach(function (el) {
        el.classList.remove("maplibregl-compact-show");
        el.removeAttribute("open");
      });
    }
    close();
    map.once("load", close);
    map.once("idle", close);
  }

  // A map in el with the controls every map on these pages carries: zoom buttons, the credits
  // behind (i), and a page that scrolls past it until someone means to move the map. The options
  // are MapLibre's own, such as a center and zoom or bounds to fit.
  function startMap(el, options) {
    var map = new maplibregl.Map(Object.assign({
      container: el,
      style: "https://tiles.openfreemap.org/styles/liberty",
      attributionControl: false,
      cooperativeGestures: true,
    }, options));
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    addAttribution(map);
    return map;
  }

  // The colour a map draws its points in: the record type's, else the theme's primary.
  function mapColour(el) {
    return cssVar(el, "--record") || cssVar(el, "--color-primary") || undefined;
  }

  // Every element marked data-map: one point at its data-lon and data-lat, with a marker.
  function initMaps(root) {
    if (!window.maplibregl) return;
    root.querySelectorAll("[data-map]").forEach(function (el) {
      if (!el.dataset.lon || !el.dataset.lat) return;
      var point = [parseFloat(el.dataset.lon), parseFloat(el.dataset.lat)];
      var map = startMap(el, { center: point, zoom: 9 });
      new maplibregl.Marker({ color: mapColour(el) }).setLngLat(point).addTo(map);
    });
  }

  onReady(function () {
    initTabs(document);
    initFolds(document);
    initCopy(document);
    initJumpToCite(document);
    initDialogs(document);
    initChips(document);
    initMaps(document);
  });
})();
