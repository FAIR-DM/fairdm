/* On this page: the heading being read is marked as the reader scrolls. */
(function () {
  "use strict";

  const links = Array.from(document.querySelectorAll(".daisy-secondary .daisy-toc-link"));
  const copies = Array.from(document.querySelectorAll(".daisy-toc-mobile .daisy-toc-link"));

  /* Following a heading in the disclosure closes it. */
  copies.forEach((link) => {
    link.addEventListener("click", () => {
      link.closest("details").open = false;
    });
  });

  if (!links.length) return;

  const headings = [];
  links.forEach((link) => {
    const id = decodeURIComponent((link.getAttribute("href") || "").replace(/^#/, ""));
    const heading = id && document.getElementById(id);
    if (heading) headings.push({ heading, href: link.getAttribute("href") });
  });
  if (!headings.length) return;

  const marked = links.concat(copies);
  const READING_LINE = 120;

  const mark = () => {
    let current = null;
    headings.forEach((entry) => {
      if (entry.heading.getBoundingClientRect().top < READING_LINE) current = entry;
    });
    /* At the foot of the page the last heading is the one being read, even if it never reached the top. */
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) {
      current = headings[headings.length - 1];
    }
    marked.forEach((link) => link.removeAttribute("aria-current"));
    document.querySelectorAll(".daisy-toc-on-path").forEach((item) => item.classList.remove("daisy-toc-on-path"));
    if (!current) return;
    marked
      .filter((link) => link.getAttribute("href") === current.href)
      .forEach((link) => {
        link.setAttribute("aria-current", "location");
        for (let item = link.closest("li"); item; item = item.parentElement && item.parentElement.closest("li")) {
          item.classList.add("daisy-toc-on-path");
        }
      });
  };

  window.addEventListener("scroll", () => window.requestAnimationFrame(mark), { passive: true });
  /* The page settles its height once styles and fonts load, which can bring its foot into view. */
  window.addEventListener("load", mark);
  window.addEventListener("resize", mark);
  mark();
})();
