"use strict";
// The window's key (docs/window-security.md): every call to Corsu carries it in X-Corsu-Key, so only the page Corsu
// opened itself can read or drive it. Corsu opens the page with a ticket after "#" (never sent to the server); the
// ticket is taken out of the address at once, exchanged once for the key, and the key is kept in sessionStorage so
// a reload (or the restart after an update, at the same address) keeps it. Without sessionStorage it is kept after
// "#" instead, which only this window sees.
const corsuAccess = (() => {
  const STORE = "corsu-key";
  let key = null;
  try { key = sessionStorage.getItem(STORE); } catch (error) {}
  const fragment = new URLSearchParams(location.hash.slice(1));
  const ticket = fragment.get("t");
  if (!key && fragment.get("k")) key = fragment.get("k");
  // A ticket works only once: it must not stay in the address, where a reload would show it again.
  if (ticket && history.replaceState) history.replaceState(null, "", location.pathname + location.search);

  function keep(value) {
    key = value;
    try { sessionStorage.setItem(STORE, value); return; } catch (error) {}
    if (history.replaceState) history.replaceState(null, "", location.pathname + location.search + "#k=" + encodeURIComponent(value));
  }

  // A new ticket wins over a kept key: Corsu was opened again, possibly with a new key.
  const ready = !ticket ? Promise.resolve(key) : fetch("/api/key", {
    method: "POST", headers: { "X-Corsu": "1", "Content-Type": "application/json" }, body: JSON.stringify({ ticket }),
  }).then(response => response.ok ? response.json() : null).then(answer => {
    if (answer && answer.key) keep(answer.key);
    return key;
  }).catch(() => key);

  return {
    ready,
    // The headers of a call to Corsu, with `extra` (Content-Type…).
    headers: (extra = {}) => ({ "X-Corsu": "1", "X-Corsu-Key": key || "", ...extra }),
    has: () => Boolean(key),
  };
})();
