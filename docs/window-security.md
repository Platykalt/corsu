# Window security

The Corsu window is a local web page served by `src/app.py` on `127.0.0.1`, port 7744 (or the next free one up to
7753). The page and anything else that can open a TCP connection to that address could drive Corsu (install,
uninstall, update, restart, change preferences), so every action is checked first. This page says what each check
guards against, what was reviewed and what is left.

## The checks

| Check | Where | Guards against |
|---|---|---|
| Binding to `127.0.0.1` only | `bind()`, `listen()` | Other computers on the network. The socket is IPv4 loopback only, so neither the LAN nor `::1` reach it. |
| `Host` must be `127.0.0.1:<port>` or `localhost:<port>` | `do_GET` for the page, `allowed()` for the API | DNS rebinding: a site whose name is made to resolve to 127.0.0.1 sends its own name as `Host` and gets 403 (page) or nothing (API). |
| `X-Corsu: 1` header required on every API call | `allowed()` | Cross-site request forgery. A page from another origin can send "simple" requests (form posts, image loads) without asking, but not a custom header: the browser first sends a CORS preflight, which the server never answers with `Access-Control-Allow-*`, so the real request is never sent. |
| `Origin`, when present, must be the window's own | `allowed()` | Defence in depth for the same, in case a browser sends a cross-origin request with the header anyway. |
| The connection's owner must be the user running Corsu (Linux) | `peer_uid()` in `allowed()` | Another account on the same computer. Such a user is not a browser: they can set any `Host`, `X-Corsu` and `Origin` they like, so the headers alone do not stop them. |
| `Content-Security-Policy` with `frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store` | `send()` | Framing the window inside another site (clickjacking), content sniffing, cached answers. |

### How the owner is found (Linux)

The server knows both ends of the connection: the caller's address and port (`client_address`) and its own
(`getsockname()`). The kernel lists every TCP socket of the network namespace in `/proc/net/tcp` and `/proc/net/tcp6`
with its local address, remote address, state and owner uid. The caller's socket is the row whose **local** end is the
caller's address and port, whose **remote** end is the window's address and port, and whose state is ESTABLISHED
(`01`). IPv4-mapped IPv6 addresses (`::ffff:127.0.0.1`, a dual-stack client socket) count as their IPv4 address.

- Exactly one owner found: the request passes only if it is the user running Corsu.
- No such row, or rows with different owners: the caller is unknown and the request is **refused** (403 for actions,
  404 for state). A legitimate caller cannot hit this: the lookup happens while the server is still reading the
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

## Residual limits

- **Windows and macOS have no owner check.** After the header checks `allowed()` returns true, so another account
  logged in at the same time (fast user switching, a remote session, a service) can drive the window. Possible
  follow-ups: `GetExtendedTcpTable` (owning PID, then its user) on Windows; `proc_pidfdinfo`/`lsof`-style socket owner
  lookup, or `LOCAL_PEERCRED` on a Unix socket, on macOS. A per-session secret given to the window (and kept out of the
  URL) would cover all platforms, but the page is also opened in plain browsers, so it needs care.
- **Same user, other programs.** Anything running as the user can drive the window, as it could run the installer
  directly. Not a boundary Corsu tries to hold.
- **Port taken first.** Another user can listen on 7744 before Corsu starts; Corsu then moves to the next port and its
  own window uses that one, but a browser tab or bookmark pointing at the fixed address would reach the other program.
- **Root** can read and do everything; not in scope.
