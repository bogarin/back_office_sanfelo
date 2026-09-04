/**
 * Service Worker registration for the PWA.
 *
 * Loads after window load so it never competes with the first render.
 * CSP-safe: served as a static file (allowed by script-src 'self').
 */
(function () {
  "use strict";

  if (!("serviceWorker" in navigator)) return;

  window.addEventListener("load", function () {
    navigator.serviceWorker
      .register("/sw.js", { scope: "/" })
      .catch(function (error) {
        console.error("Service Worker registration failed:", error);
      });
  });
})();
