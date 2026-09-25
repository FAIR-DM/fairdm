/*
 * Paint every chart on the page in the active daisyUI theme.
 *
 * django-mvp-charts deliberately writes no colours, so a chart built in Python would otherwise
 * carry ECharts' own palette whatever theme the portal runs. This reads the theme's tokens when
 * each chart is drawn, and again whenever the theme is switched, so a chart never disagrees with
 * the page around it.
 *
 * Load it before mvp-charts.js: the drawn event fires once, and a listener added later misses it.
 */
(function () {
  "use strict";

  const probe = document.createElement("canvas").getContext("2d", { willReadFrequently: true });

  // daisyUI 5 declares its colours in oklch(), which ECharts' own colour parser does not read.
  // Painting one pixel and reading it back gives the same colour as plain sRGB.
  function token(name, alpha) {
    const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    if (!value) return undefined;
    probe.clearRect(0, 0, 1, 1);
    probe.fillStyle = "#000";
    probe.fillStyle = value;
    probe.fillRect(0, 0, 1, 1);
    const [r, g, b] = probe.getImageData(0, 0, 1, 1).data;
    return alpha === undefined ? `rgb(${r}, ${g}, ${b})` : `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  function themed(chart) {
    const ink = token("--color-base-content");
    const muted = token("--color-base-content", 0.65);
    const rule = token("--color-base-content", 0.12);
    const axis = {
      axisLabel: { color: muted },
      axisLine: { lineStyle: { color: rule } },
      axisTick: { lineStyle: { color: rule } },
      splitLine: { lineStyle: { color: rule } },
    };
    const series = (chart.getOption().series || []).map(() => ({ label: { color: ink } }));
    return {
      // Fixed order: the first series is always primary, the second always secondary.
      color: [token("--color-primary"), token("--color-secondary")],
      textStyle: { color: ink, fontFamily: getComputedStyle(document.body).fontFamily },
      legend: { textStyle: { color: ink } },
      tooltip: {
        backgroundColor: token("--color-base-100"),
        borderColor: token("--color-base-300"),
        textStyle: { color: ink },
      },
      xAxis: axis,
      yAxis: axis,
      series: series,
    };
  }

  document.addEventListener("mvp-chart:drawn", (event) => {
    const chart = event.detail.chart;
    chart.setOption(themed(chart));
  });

  new MutationObserver(() => {
    if (!window.echarts) return;
    document.querySelectorAll("[data-mvp-chart-surface]").forEach((surface) => {
      const chart = window.echarts.getInstanceByDom(surface);
      if (chart) chart.setOption(themed(chart));
    });
  }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
})();
