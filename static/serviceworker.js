/**
 * Service Worker — Backoffice San Felipe PWA.
 *
 * Strategies:
 * - /static/ assets: stale-while-revalidate (instant load, background refresh)
 * - Navigations / HTML: network-first with cache fallback (fresh data, offline support)
 * - Non-GET and cross-origin requests: never intercepted
 *
 * CSP-safe: no eval, no inline handlers, no external connections.
 */
"use strict";

const VERSION = "v1";
const STATIC_CACHE = `sf-static-${VERSION}`;
const PAGES_CACHE = `sf-pages-${VERSION}`;
const KNOWN_CACHES = [STATIC_CACHE, PAGES_CACHE];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(PAGES_CACHE)
      .then((cache) => cache.add("/admin/login/"))
      .catch(() => undefined)
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => !KNOWN_CACHES.includes(key))
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;

  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith("/static/")) {
    event.respondWith(staleWhileRevalidate(request, STATIC_CACHE));
    return;
  }

  const acceptsHtml = (request.headers.get("accept") || "").includes("text/html");
  if (request.mode === "navigate" || acceptsHtml) {
    event.respondWith(networkFirst(request, PAGES_CACHE));
  }
});

/**
 * Serve from cache immediately, refresh the copy in the background.
 * Falls back to the network when nothing is cached yet.
 */
async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  const refresh = fetch(request)
    .then((response) => {
      if (response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => cached || Response.error());

  return cached || refresh;
}

/**
 * Try the network first so users always get fresh pages; fall back to
 * the cached copy when offline or the server is unreachable.
 */
async function networkFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await cache.match(request);
    if (cached) return cached;
    throw error;
  }
}
