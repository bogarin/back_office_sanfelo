/**
 * Quick Actions for TramiteAdmin changelist.
 *
 * Uses event delegation on the changelist form to handle clicks
 * on elements with class="quick-action". Each button carries
 * data-action (batch action name) and data-pk (object ID).
 *
 * CSP-safe: no inline handlers, served as static file (allowed by script-src 'self').
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("changelist-form");
    if (!form) return;

    form.addEventListener("click", function (e) {
      var btn = e.target.closest(".quick-action");
      if (!btn) return;

      e.preventDefault();

      // Set the action dropdown value
      var sel = form.querySelector('select[name="action"]');
      if (sel) {
        sel.value = btn.dataset.action;
      }

      // Add hidden input for the selected object
      var inp = document.createElement("input");
      inp.type = "hidden";
      inp.name = "_selected_action";
      inp.value = btn.dataset.pk;
      form.appendChild(inp);

      form.submit();
    });
  });
})();
