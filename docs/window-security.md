# Window security

The Corsu window is a local web page served by `src/app.py` on `127.0.0.1`, port 7744 (or the next free one up to
7753). The page and anything else that can open a TCP connection to that address could read what Corsu knows (the
state of each program and its paths, the appearance settings, the personal background picture) and drive Corsu
(install, uninstall, update, restart, change preferences), so every API call, read or action, is checked first. This
page says what each check guards against, what was reviewed and what is left.

## The checks

| Check | Where | Guards against |
|---|---|---|
| Binding to `127.0.0.1` only | `bind()`, `listen()` | Other computers on the network. The socket is IPv4 loopback only, so neither the LAN nor `::1` reach it. |
| `Host` must be `127.0.0.1:<port>` or `localhost:<port>` | `do_GET` for the page, `allowed()` for the API | DNS rebinding: a site whose name is made to resolve to 127.0.0.1 sends its own name as `Host` and gets 403 (page) or nothing (API). |
| `X-Corsu: 1` header required on every API call, reads included | `allowed()` | Cross-site request forgery. A page from another origin can send "simple" requests (form posts, image loads) without asking, but not a custom header: the browser first sends a CORS preflight, which the server never answers with `Access-Control-Allow-*`, so the real request is never sent. |
| `Origin`, when present, must be the window's own | `allowed()` | Defence in depth for the same, in case a browser sends a cross-origin request with the header anyway. |
| The window's key in `X-Corsu-Key` on every API call (all systems) | `Access`, `allowed()` | Another account on the same computer, on Windows and macOS where nothing else stops it. Such a user is not a browser: they can set any `Host`, `X-Corsu` and `Origin` they like, so the headers alone do not stop them; they do not know the key. See "The window's key". |
| The connection's owner must be the user running Corsu (Linux) | `peer_uid()` in `allowed()` | The same, on Linux, independently of the key. |
| `Content-Security-Policy` with `frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store` | `send()` | Framing the window inside another site (clickjacking), content sniffing, cached answers. |

Every API route answers 403 when a check fails: `/api/state`, `/api/review/*`, `/appearance/settings`,
`/appearance/background` and every `POST`. What is served without checks is only the page and its own files
(`index.html`, its scripts, styles and icon): the same for everyone, with nothing of the person in them.

### The window's key

The key is a random secret (`secrets.token_urlsafe(32)`) made each time Corsu starts. It must never be on a command
line or in an address that reaches the server, because other accounts can read some of those (on macOS `ps` shows
every user's command lines; on Linux `/proc/<pid>/cmdline` is readable by everyone unless `hidepid` is set; on
Windows a standard user cannot read another user's command lines). So:

1. The server makes a **ticket** (a second random secret, single use, valid 120 s) and opens its window at
   `http://127.0.0.1:<port>/#t=<ticket>`. The part after `#` is never sent to a server.
2. The page (`src/app/key.js`, loaded first) takes the ticket out of the address with `history.replaceState`, so that
   no reload shows it again, and posts it to `POST /api/key`, which takes every other check (Host, `X-Corsu`,
   Origin, owner on Linux) and answers the key once.
3. The page keeps the key in `sessionStorage` (the tab's own storage, gone with the window) and sends it with every
   call. A reload, and the reload after Corsu restarts from an updated copy at the same address, keep it. Where
   `sessionStorage` cannot be used, the key is put after `#` instead (`#k=…`), which again only this window sees.
4. A ticket shown a **second time** means someone else read it: the key is replaced at once and the new one noted
   in the session file, so whoever got the key with that ticket is shut out, whichever came first. The window then
   says "This page does not have Corsu's key. Open Corsu again from the applications menu", and opening Corsu again
   gives a new window with a new ticket. An expired or unknown ticket is simply refused.
5. The key is written to `DATA/setup-session.json` with the address, created `0600` (Linux, macOS; on Windows the
   file is in the user's own `%LOCALAPPDATA%`, which other standard users cannot read). It serves two cases:
   - a **second launch** while Corsu is open reads it, checks that the open window answers with it, asks that
     window for a fresh ticket (`POST /api/ticket`, keyed) and opens a new window with it;
   - the **copy that replaces the window after an update** (`--replace <port>`) takes the same key, so the page that
     reloads from it keeps working. A copy before 0.25 had no key to hand over: the new copy then makes its own and
     opens its own window, and the old page says to reopen Corsu.

How each way of opening the window gets the ticket:

| Way | Where the address goes | Who else can read it |
|---|---|---|
| pywebview (standalone Corsu on Windows and macOS: WebView2, WKWebView) | inside Corsu's process | nobody |
| WebKitGTK (Linux) | inside Corsu's process | nobody |
| Chromium-based app window (`--app=…`) | the browser's command line | Windows: nobody; macOS and Linux: every account (`ps`) |
| A browser tab (`webbrowser.open`) | Windows: the browser's command line; macOS: the command line of `open` for a moment; Linux: `xdg-open`'s | as above |
| `--no-browser` | printed in the terminal (and the log) | nobody |

In the last three rows a ticket read by someone else is either useless (already used, or expired after 120 s) or
used first, which the window shows at once; and it is replaced together with the key when the real window shows it.
On Linux the owner check refuses other accounts anyway.

### How the owner is found (Linux)

The server knows both ends of the connection: the caller's address and port (`client_address`) and its own
(`getsockname()`). The kernel lists every TCP socket of the network namespace in `/proc/net/tcp` and `/proc/net/tcp6`
with its local address, remote address, state and owner uid. The caller's socket is the row whose **local** end is the
caller's address and port, whose **remote** end is the window's address and port, and whose state is ESTABLISHED
(`01`). IPv4-mapped IPv6 addresses (`::ffff:127.0.0.1`, a dual-stack client socket) count as their IPv4 address.

- Exactly one owner found: the request passes only if it is the user running Corsu.
- No such row, or rows with different owners: the caller is unknown and the request is **refused** (403). A legitimate caller cannot hit this: the lookup happens while the server is still reading the
  request, before it answers, so the caller's socket is open and ESTABLISHED. Only a caller that has already closed or
  half-closed its end is refused, and nobody is waiting for that answer. If `/proc/net/tcp*` cannot be read at all the
  window refuses every action; that is not a known configuration (the files are world-readable and `hidepid` does not
  hide them), and failing open would silently drop the protection.
- Nothing is retried: an action is either refused before it starts or runs once.

## Review of 0.24.0 and of 64d0808 (October 2026)

0.24.0 looked for the **first row whose local port equalled the caller's port**, whatever the addresses, the remote
end or the state, and allowed the request when nothing was found. 64d0808 (on `next-0.25`) added "remote port is the
window's port" and "not TIME_WAIT". Findings:

**Established (reproduced):**

1. *Random refusals of the user's own actions (0.24.0, since 0.20.0).* A closed connection in TIME_WAIT keeps its local
   port and shows uid 0. Linux reuses ephemeral ports for other destinations (and, on loopback, even for the same one,
   `tcp_tw_reuse=2`), so a new connection to the window often shares its local port with a TIME_WAIT row listed
   first; the request then gets 403 (actions) or 404 (state, which the page shows as an error). Measured with
   3000 legitimate POSTs against a window on a fixed port in an isolated HOME: 7 refused (0.23 %) on a quiet machine;
   2254 refused (75 %) while other local programs open and close connections quickly (about 15 000 TIME_WAIT rows).
   CI saw it once on the v0.24.0 tag because test servers use ephemeral ports, which leave TIME_WAIT rows on them.
   Fixed by 64d0808 and by the 4-tuple match: 0 refused in both runs.
2. *Another local user can pass the owner check (0.24.0 and 64d0808).* A caller that binds another loopback address
   (`127.0.0.2`) with the window's own port as its source port and connects to the window makes the window's end of
   that connection look, by ports alone, exactly like the caller's: local port = remote port = the window's port. That
   row, and the window's listening socket, belong to the user running Corsu. Checked on a real kernel table: in 200 of
   200 connections both the 0.24.0 and the 64d0808 lookups picked a row owned by the window's side, not the caller's.
   With the 4-tuple match the window's end (local `127.0.0.1:7744`, remote `127.0.0.2:7744`) never matches the
   caller (local `127.0.0.2:7744`, remote `127.0.0.1:7744`); a test runs this on the real kernel tables.
   Impact: on a Linux computer shared by several accounts, while one user's Corsu window is open, another user can run
   its actions as that user (install, uninstall, update from the published releases, change preferences, restart).
   It needs a local account; web pages cannot choose their source address or port and are stopped by the header checks.

**Hypotheses (not reproduced, closed by the fix anyway):**

- Another user's socket using the caller's local port towards elsewhere, listed first (0.24.0): wrong owner either way.
- "Not found → allowed" (0.24.0, 64d0808): no way was found for another local user to make their own live connection
  disappear from the table of the window's network namespace (another namespace cannot reach the window's 127.0.0.1
  at all). It is now refused regardless.
- Several matching rows with different owners: not possible for one live 4-tuple in one namespace; refused if seen.

**Not a problem:** the window is not reachable from other computers (IPv4 loopback bind); web pages, including through
DNS rebinding, are stopped by the `Host`, `X-Corsu` and `Origin` checks, independently of the owner check.

## Review of the read routes (0.25 candidate, October 2026)

**Established (reproduced on Linux with the platform set to Windows and to macOS, the code path those systems
run):** before the key, `allowed()` on Windows and macOS was only the header checks, which another account copies.
With `Host`, `X-Corsu: 1` and `Origin` set, `GET /api/state` answered 200 with the whole state (installed programs,
the Firefox profile and other paths of the person), `GET /appearance/settings` 200 and `GET /appearance/background`
200 with the personal picture's bytes; every action passed as well (the limit listed in 0.24). On Linux the owner
check refused them (403; 404 for the state). Not observed on a real Windows or macOS computer.

**Fixed by the key**, on every system, without removing any earlier check: unit tests
(`tests/test_app.py`, `WindowKeyTests`) refuse every read and action without the key or with a wrong one, with the
platform set to Windows, macOS and Linux, and check that the key does not replace Host, Origin, `X-Corsu` or the owner
check; `tests/e2e/check_appearance.py` checks in Chrome that the page gets the key from its ticket, keeps it across
`location.reload()`, that a page without key is told so, and that a ticket used twice shuts both pages out. The
WebKitGTK window opened by `app.serve('window')` was checked the same way (key, reload, second launch) in a container.

## Residual limits

- **The ticket in a browser's command line (macOS, Linux).** When Corsu falls back to a Chromium app window or a
  browser tab, an account polling `ps` could read the ticket and exchange it before the page does. It then holds the
  key until the page tries the ticket (seconds), which replaces the key; the page asks the person to reopen Corsu.
  The standalone Corsu for macOS bundles pywebview, which never shows the address; on Linux the owner check stops
  other accounts regardless. Not reproduced.
- **A browser tab or bookmark opened by hand** at `http://localhost:7744/` has no key: it says to reopen Corsu.
- **No owner check on Windows and macOS.** The key is the barrier there. A second, independent one is still possible:
  `GetExtendedTcpTable` (owning PID, then its user) on Windows; `LOCAL_PEERCRED` on a Unix socket on macOS.
- **Same user, other programs.** Anything running as the user can drive the window (it can read the session file,
  the browser's storage, or run the installer directly). Not a boundary Corsu tries to hold.
- **Port taken first.** Another user can listen on 7744 before Corsu starts; Corsu then moves to the next port and its
  own window uses that one, but a browser tab or bookmark pointing at the fixed address would reach the other program.
  That program never gets the key: Corsu's window only exchanges tickets with the address Corsu itself opened.
- **Root** can read and do everything; not in scope.
