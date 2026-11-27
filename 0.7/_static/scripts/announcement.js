/* Announcement fetched from a URL: the page carries an empty banner to fill. */
(function () {
  "use strict";

  const body = document.querySelector("[data-daisy-announcement-body]");
  if (!body) return;

  const banner = body.closest("[data-daisy-announcement]");
  const remove = () => banner.remove();

  fetch(banner.dataset.daisyAnnouncement)
    .then((response) => (response.ok ? response.text() : ""))
    .then((html) => {
      if (html.trim()) body.innerHTML = html;
      else remove();
    })
    .catch(remove);
})();
