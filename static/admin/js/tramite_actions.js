/**
 * Tramite detail action buttons.
 *
 * Uses event delegation on the #accion-form to handle clicks on
 * buttons with data-action attributes. Sets the hidden #action-input
 * value before submitting the form.
 *
 * CSP-safe: no inline handlers, served as static file (allowed by script-src 'self').
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("accion-form");
    if (!form) return;

    form.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-action]");
      if (!btn) return;

      var actionInput = document.getElementById("action-input");
      if (actionInput) {
        actionInput.value = btn.dataset.action;
      }
    });
  });
})();
