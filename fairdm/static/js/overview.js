// The redesigned overview pages: description tabs and folding, the citation formats, copy
// buttons, the measurement filter and the maps. Prototype script, no build step.
(function () {
  "use strict";

  function onReady(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  // Tabs: a role="tablist" of buttons, each controlling a panel. Arrow keys move between them.
  function initTabs(root) {
    root.querySelectorAll("[role=tablist]").forEach(function (list) {
      var tabs = Array.prototype.slice.call(list.querySelectorAll("[role=tab]"));
      function select(tab, focus) {
        tabs.forEach(function (t) {
          var on = t === tab;
          t.setAttribute("aria-selected", on ? "true" : "false");
          t.tabIndex = on ? 0 : -1;
          var panel = document.getElementById(t.getAttribute("aria-controls"));
          if (panel) panel.hidden = !on;
        });
        if (focus) tab.focus();
        list.dispatchEvent(new CustomEvent("ov:tab", { detail: tab, bubbles: true }));
        checkFolds(document);
      }
      tabs.forEach(function (tab, i) {
        tab.addEventListener("click", function () { select(tab); });
        tab.addEventListener("keydown", function (e) {
          var next = null;
          if (e.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
          if (e.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
          if (e.key === "Home") next = tabs[0];
          if (e.key === "End") next = tabs[tabs.length - 1];
          if (next) { e.preventDefault(); select(next, true); }
        });
      });
    });
  }

  // Folds: a long description shows its first lines and a "Read more" button.
  function checkFolds(root) {
    root.querySelectorAll(".ov-fold").forEach(function (fold) {
      var body = fold.querySelector(".ov-fold__body");
      if (!body || fold.dataset.opened === "true" || !body.offsetParent) return;
      fold.dataset.folded = "true";
      // Fold only when it hides a few lines' worth; a line or two more is simply shown.
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
        button.querySelector("[data-label]").textContent = open ? button.dataset.less : button.dataset.more;
        if (!open) fold.scrollIntoView({ block: "nearest" });
      });
    });
    window.addEventListener("resize", function () { checkFolds(document); });
    window.addEventListener("load", function () { checkFolds(document); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { checkFolds(document); });
  }

  function flash(el, attr) {
    el.setAttribute(attr || "data-copied", "true");
    setTimeout(function () { el.removeAttribute(attr || "data-copied"); }, 1600);
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    try { document.execCommand("copy"); } finally { document.body.removeChild(area); }
    return Promise.resolve();
  }

  // Copy buttons: data-copy holds the text, or data-copy-from names an element to read.
  function initCopy(root) {
    root.querySelectorAll("[data-copy], [data-copy-from]").forEach(function (button) {
      button.addEventListener("click", function () {
        var text = button.dataset.copy;
        if (button.dataset.copyFrom) {
          var source = document.getElementById(button.dataset.copyFrom);
          text = source ? source.textContent : "";
        }
        copyText(text).then(function () {
          flash(button);
          var status = button.parentElement.querySelector(".ov-copied");
          if (status) {
            status.hidden = false;
            setTimeout(function () { status.hidden = true; }, 1600);
          }
        });
      });
    });
  }

  // Cite: the segmented control swaps the format; Download saves BibTeX or RIS.
  function initCite(root) {
    root.querySelectorAll("[data-cite]").forEach(function (box) {
      var formats = JSON.parse(box.querySelector("script[type='application/json']").textContent);
      var out = box.querySelector(".ov-cite__text");
      var download = box.querySelector("[data-download]");
      var buttons = box.querySelectorAll(".ov-seg button");
      function show(key) {
        var format = formats.filter(function (f) { return f.key === key; })[0];
        out.textContent = format.value;
        out.dataset.format = key;
        buttons.forEach(function (b) { b.setAttribute("aria-selected", b.dataset.format === key ? "true" : "false"); });
        if (download) {
          download.hidden = !format.file;
          download.dataset.file = format.file;
        }
        try { localStorage.setItem("ov-cite-format", key); } catch (e) { /* private mode */ }
      }
      buttons.forEach(function (b) { b.addEventListener("click", function () { show(b.dataset.format); }); });
      if (download) {
        download.addEventListener("click", function () {
          var blob = new Blob([out.textContent], { type: "text/plain;charset=utf-8" });
          var link = document.createElement("a");
          link.href = URL.createObjectURL(blob);
          link.download = download.dataset.file;
          document.body.appendChild(link);
          link.click();
          setTimeout(function () { URL.revokeObjectURL(link.href); link.remove(); }, 100);
        });
      }
      var saved = null;
      try { saved = localStorage.getItem("ov-cite-format"); } catch (e) { /* private mode */ }
      show(formats.some(function (f) { return f.key === saved; }) ? saved : "text");
    });
    // The header's Cite button: scroll to the citation and point at it.
    root.querySelectorAll("[data-jump-cite]").forEach(function (button) {
      button.addEventListener("click", function (e) {
        var target = document.getElementById("cite");
        if (!target) return;
        e.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        target.classList.add("ov-pulse");
        setTimeout(function () { target.classList.remove("ov-pulse"); }, 1400);
        var first = target.querySelector(".ov-seg button[aria-selected=true]");
        if (first) first.focus({ preventScroll: true });
      });
    });
  }

  // Filter chips: show only the rows of one type.
  function initChips(root) {
    root.querySelectorAll("[data-filter-chips]").forEach(function (group) {
      var list = document.getElementById(group.dataset.filterChips);
      var chips = group.querySelectorAll(".ov-chip");
      var more = document.querySelector("[data-filter-more='" + group.dataset.filterChips + "']");
      chips.forEach(function (chip) {
        chip.addEventListener("click", function () {
          var value = chip.dataset.value;
          chips.forEach(function (c) { c.setAttribute("aria-pressed", c === chip ? "true" : "false"); });
          var shown = 0;
          list.querySelectorAll("li[data-type]").forEach(function (row) {
            var on = !value || row.dataset.type === value;
            row.hidden = !on;
            if (on) shown += 1;
          });
          if (more) more.hidden = !!value;
        });
      });
    });
  }

  function cssVar(el, name) {
    return getComputedStyle(el).getPropertyValue(name).trim();
  }

  // Maps: a single point (data-lon, data-lat) or a set of points (data-points names a JSON script).
  function initMaps(root) {
    if (!window.maplibregl) return;
    root.querySelectorAll(".ov-map").forEach(function (el) {
      var colour = cssVar(el, "--record") || cssVar(el, "--color-primary") || "#17517D";
      var map;
      if (el.dataset.points) {
        var data = JSON.parse(document.getElementById(el.dataset.points).textContent);
        var b = JSON.parse(el.dataset.bounds);
        map = new maplibregl.Map({
          container: el,
          style: "https://tiles.openfreemap.org/styles/positron",
          bounds: [[b[0], b[1]], [b[2], b[3]]],
          fitBoundsOptions: { padding: 48, maxZoom: 10 },
          attributionControl: { compact: true },
          cooperativeGestures: true,
        });
        map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
        map.on("load", function () {
          map.addSource("samples", { type: "geojson", data: data, cluster: true, clusterRadius: 38, clusterMaxZoom: 11 });
          map.addLayer({
            id: "clusters", type: "circle", source: "samples", filter: ["has", "point_count"],
            paint: {
              "circle-color": colour, "circle-opacity": 0.85,
              "circle-radius": ["step", ["get", "point_count"], 14, 10, 18, 50, 24],
              "circle-stroke-width": 3, "circle-stroke-color": "rgba(255,255,255,0.85)",
            },
          });
          map.addLayer({
            id: "cluster-count", type: "symbol", source: "samples", filter: ["has", "point_count"],
            layout: { "text-field": ["get", "point_count_abbreviated"], "text-size": 12, "text-font": ["Noto Sans Bold"] },
            paint: { "text-color": "#111820" },
          });
          map.addLayer({
            id: "points", type: "circle", source: "samples", filter: ["!", ["has", "point_count"]],
            paint: { "circle-color": colour, "circle-radius": 6, "circle-stroke-width": 2, "circle-stroke-color": "#ffffff" },
          });
          map.on("click", "clusters", function (e) {
            var feature = map.queryRenderedFeatures(e.point, { layers: ["clusters"] })[0];
            map.getSource("samples").getClusterExpansionZoom(feature.properties.cluster_id).then(function (zoom) {
              map.easeTo({ center: feature.geometry.coordinates, zoom: zoom });
            });
          });
          map.on("click", "points", function (e) {
            var p = e.features[0].properties;
            var box = document.createElement("div");
            var link = document.createElement("a");
            link.href = p.url;
            link.textContent = p.name;
            var meta = document.createElement("span");
            meta.textContent = p.type + " · " + p.dataset;
            box.appendChild(link);
            box.appendChild(meta);
            new maplibregl.Popup({ offset: 10 }).setLngLat(e.features[0].geometry.coordinates).setDOMContent(box).addTo(map);
          });
          ["clusters", "points"].forEach(function (layer) {
            map.on("mouseenter", layer, function () { map.getCanvas().style.cursor = "pointer"; });
            map.on("mouseleave", layer, function () { map.getCanvas().style.cursor = ""; });
          });
        });
      } else if (el.dataset.lon) {
        var point = [parseFloat(el.dataset.lon), parseFloat(el.dataset.lat)];
        map = new maplibregl.Map({
          container: el,
          style: "https://tiles.openfreemap.org/styles/liberty",
          center: point,
          zoom: 9,
          attributionControl: { compact: true },
          cooperativeGestures: true,
        });
        map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
        new maplibregl.Marker({ color: colour }).setLngLat(point).addTo(map);
      }
    });
  }

  onReady(function () {
    initTabs(document);
    initFolds(document);
    initCopy(document);
    initCite(document);
    initChips(document);
    initMaps(document);
  });
})();
