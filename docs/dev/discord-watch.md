# Discord start watch — contract (integrator, 0.29.0 work)

## Architecture
Short-lived supervisor `src/discord_watch.py`, run by Corsu's own Python, never inside Discord:
- Linux: Corsu-owned user desktop entries override `discord.desktop` (applications + autostart if Discord's autostart
  entry exists). Exec = `<corsu-python> <release>/src/discord_watch.py launch -- %U`. The wrapper starts the real
  Discord binary with the original args (discord:// URLs kept) FIRST, detached, then watches. Any watcher error →
  Discord already started; watcher exits silently (logged).
- Windows/macOS: no wrapper (Discord rewrites its own shortcuts at each update; replacing them is invasive). Coverage
  there = the post-hoc scan below. No permanent service anywhere.
- Post-hoc scan (all platforms): `discord_watch.scan_last_start()` reads the tail (bounded, e.g. last 2 MB) of
  renderer_js.log, splits sessions at `splashScreenPreload: signalReady`/Vencord `Starting up`, and classifies the
  LAST session with the same rules. Run when Corsu's window opens and by the watcher itself. Covers the Linux
  host-updater restart path and Windows/macOS, after the fact (no live notification there unless Corsu's window or
  its tray is running).
- Watch window: bounded (default 180 s; stops at first decisive signal). One supervisor per Discord user-data dir
  (lock file in corsu.DATA/discord-watch/lock with pid; second launch → just passes args to Discord, no watch).
- Signals = Discord's own logs, read from the offset at launch: `<user-data>/logs/renderer_js.log` (renderer console:
  splash states, `[Flux] Dispatching CONNECTION_OPEN`, Vencord lines, `Uncaught …`), plus process liveness of the
  started pid / Discord processes. No --remote-debugging-port on the personal Discord, ever.
- Not covered: Discord restarted by its own host updater (no wrapper in that path) — next manual launch is watched;
  launches that bypass the wrapper (terminal `discord`, other launchers).

## States (`discord-watch/state.json`, written atomically; last incident only)
```
{"version":1, "incident": "<uuid>|null", "state": STATE, "started_at": float, "decided_at": float|null,
 "launch": "shortcut|autostart|url|already-running|unknown", "client": "<app folder>", "app_version": "1.0.168",
 "vencord": {"injected": bool, "revision": str|null, "corsu_version": str|null, "dist": path|null},   # from corsu-build.json
 "evidence": [ {"t": float, "kind": KIND, "line": "<≤300 chars, redacted>"} ]   # ≤ 20 entries
 , "notified": bool, "dismissed": bool}
```
STATE ∈
- `ok` — UI reached (CONNECTION_OPEN, or login page signal) — Discord started.
- `ok-corsu` — ok + Vencord PluginManager started Corsu (only claimable when a Vencord/Corsu line is seen).
- `vencord-error` — Uncaught error before UI reached AND stack/line mentions Vencord/VencordRenderer/WebpackPatcher
  → "probable incompatibility with the translation" (still worded as probable).
- `start-error` — explicit Uncaught before UI, no Vencord evidence.
- `slow` — no decisive signal after the window; process alive. Cause unknown.
- `closed` — Discord processes exited before UI and no error (user quit, or crash without log).
- `updating` — splash states downloading/installing updates seen (normal; watch extends once).
- `network` — splash/updater "update-failure"/offline/gateway connection failures, no error.
- `already-running` — second instance handed off ("Quitting secondary instance"): no watch.
- `offscreen` — separate check: window geometry outside all monitors (Linux Hyprland via hyprctl only; else n/a).
- `rescue` — Corsu put Discord in rescue mode (no translation) — set by rescue code, not by the watcher.

## Incident → UI (Agent B)
Watcher, on a problem state (`vencord-error`, `start-error`, `slow`, `network`, `offscreen`), once per incident:
`corsu.notify(title, body, action="discord-recovery", incident=id)` → native notification
(Linux: org.freedesktop.Notifications via gdbus/notify-send if present, action opens window; Windows: toast via
existing hidden PowerShell path or none — no console; macOS: osascript). No notification service → nothing
pops; state stays in state.json and shows in Corsu's window (Discord row) next time.
Recovery window = Corsu's window opened on page `discord-recovery` (existing app.py server, appearance, translations).
Actions per state:
- Rechercher une mise à jour → existing update check (app.py check_update); show its real status:
  available / up-to-date / check-impossible / installed-but-processes-old (running_releases) / dev build (hyprland
  manifest) — never promise it fixes the issue.
- Démarrer sans la traduction → rescue API (Agent A): `discord_watch.rescue(incident)`.
- Réessayer → `discord_watch.launch()` again (only if Discord not running).
- Voir le diagnostic → evidence + versions (collapsed).
- Plus tard → dismissed=true.

## Rescue API (Agent A, in discord_watch.py; uses installer record from 0.28.4)
- `rescue_check()` → {"ok": bool, "reason": "running|no-record|backup-mismatch|backup-missing|launcher-backup|unknown-app", "location": ...}
- `rescue()` → requires Discord not running (never kills; returns `running`), location = the app folder actually
  launched (state.client) == recorded discord_location, backup hash == record backup and not a launcher; restores
  original app.asar (keeps _app.asar), writes `discord-watch/rescue.json` {location, since, from_revision}; Corsu's
  repair/update/install_discord skip Discord while rescue.json exists (no silent reinjection).
- `rescue.json` has a `phase`: `rescue` (original archive back), `verifying` (translation reinstalled, no start has
  proved it yet), `restore-pending` (a reactivated start failed while Discord stayed open; `reason` says why the
  restore waited). In every phase `in_rescue()` is true: install_discord skips Discord (no silent reinjection).
- `reactivate()` → phase `verifying` first, then `installer.install_discord(location, reactivating=True)`, then a
  watched launch. Every watched launch calls `settle_reactivation(record)`: `ok-corsu` (the Corsu plugin seen
  starting) removes rescue.json, the only confirmed outcome; a problem state (not `offscreen`) runs `rescue()`, or
  sets `restore-pending` when Discord is still open; anything else (closed, ok without the plugin, updating,
  unwatched) stays `verifying` and is returned as `{"ok": false, "reason": "unconfirmed"}`. In `restore-pending`,
  "Finish the restore" in the window is `rescue()` again once Discord is closed. A reinstall that fails before
  replacing anything goes back to phase `rescue`.
- Uninstall removes desktop overrides, discord-watch/ dir, rescue.json.

## File ownership
- Agent A: src/discord_watch.py, tests/test_discord_watch.py, installer.py hooks (rescue skip, install/uninstall of
  wrappers), tests/e2e/check_discord_watch_real.py (reuses check_discord_real_start.py pieces).
- Agent B: corsu.notify (src/notify.py), src/app.py routes + src/app/ page/strings, window Discord status row,
  update-status mapping, docs/fr + docs/en, tests for UI/notify/update states, Windows console check extension.
- Integrator: contract, review, merge, CI, real runs.
