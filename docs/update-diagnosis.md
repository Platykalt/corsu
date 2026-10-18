# Why Corsu 0.24.0 said "up to date" while 0.25.1 was out (18 October 2026)

What the maintainer saw: the Corsu window, version 0.24.0, said « Corsu est à jour » although 0.25.1 had been
published. Diagnosed on 18 October 2026 from the code of the `v0.24.0` tag, GitHub's release list and the
maintainer's log, read only (nothing of the personal installation was run or changed). Fixed on `c026b-update`.

## Timeline (Linux, the maintainer's computer)

| Time (CEST) | Source | What happened |
| --- | --- | --- |
| 18 Oct 10:49:19 | `logs/corsu.log` l. 480–482 | `=== app`, `Corsu 0.23.0`, a new window: its check finds 0.24.0 and saves `update.json` = "latest 0.24.0" (inferred: the previous session, 17 Oct 01:59, predates the 0.24.0 release of 17 Oct 16:43, and the window asked for `--version 0.24.0`, which it does only for a release it found available) |
| 10:49:44–10:49:59 | log l. 483–562 | `update --install --version 0.24.0` → `@result {"corsu": "updated", "from": "0.23.0", "to": "0.24.0", "restart_app": true}` |
| 10:50:04 | log l. 563–565 | `=== app --replace 7744`, `Corsu 0.24.0`: the 0.24.0 server takes over the window and checks once (`start_check(job)`); the saved answer is under a minute old, so it is used → *up to date, latest 0.24.0, checked 10:49* |
| 13:15:51 | GitHub API `published_at` 2026-10-18T11:15:51Z | v0.25.1 published (v0.25.0 is a tag without a release: absent from the release list) |
| 16:13:13 | log l. 566–567 | `=== app`, `Corsu 0.24.0`, **no** "Corsu est ouvert" line: the launcher found the 10:50 server still running (`running_session()`) and only showed it |
| 17:48:53 | `update.json` `checked: 1792338533.75` | the "Rechercher les mises à jour" button (`force=True`) → latest 0.25.1 |
| 17:48:57–17:49:34 | log l. 568–653 | `update --install --version 0.25.1` (the version the window showed as available) → `updated 0.24.0 → 0.25.1` |
| 17:49:51 | log l. 654–656 | `app --replace 7744`, `Corsu 0.25.1` takes over the window |

Between 10:50 and 17:49 no other server started: one 0.24.0 process served the window for seven hours.

## Cause (confirmed)

1. **The window checked only when it opened.** In 0.24.0, `serve()` calls `start_check(job)` once
   (`v0.24.0:src/app.py` l. 844); `UPDATE['info']` is then only replaced by the button (`/api/update/check`, l. 383).
   The page polls `/api/state` every 1.5 s (`v0.24.0:src/app/index.html` l. 1174) and receives the same `info` each
   time. A window open before 13:15 kept "up to date, latest 0.24.0" until the button was pressed; a second launch
   showed that same window (`serve()` l. 818–825). The only hint was the "Dernière vérification" date (10:49).
2. **The saved answer was reused for 6 hours without saying so.** `CHECK_EVERY = 6 * 3600` (`v0.24.0:src/update.py`
   l. 43, `check()` l. 162–191): any window opened before 16:49 would have shown "up to date" from the 10:49 answer
   without asking GitHub, presented exactly like a fresh check. At 16:13 the saved answer was 5 h 24 old.

Both are reproduced with the real 0.24.0 code (`git archive v0.24.0 src`), a fake clock and a fake GitHub holding
0.25.1 from 13:15:51: the window says `up_to_date latest=0.24.0 checked=10:49` at 13:20, 16:13 and 17:48, a new
window at 16:13 says the same without asking GitHub, and the button at 17:48:53 finds 0.25.1. The unchanged code of
0.25.1 behaves the same. The same timeline is a unit test (`tests/test_update_check.py`,
`WindowTests.test_the_18_october_timeline`, `CacheTests.test_a_window_opened_hours_after_a_release_asks_github_again`).

## Ruled out, with the evidence

- **GitHub's answer, tags, drafts, prereleases**: the release list holds v0.25.1 (not draft, not prerelease) since
  11:15:51 UTC; v0.25.0 has no release and is not in the list; versions are compared as numbers. The button at
  17:48:53 got 0.25.1 at once.
- **Network error, rate limit (403/429), cut answer**: in 0.24.0 a failure gives `status: unknown` ("Vérification
  impossible"), never `up_to_date`; nothing in the log shows a failure, and the button worked. Now covered by tests
  for each kind.
- **Version of the window vs the installed copy**: between 10:50 and 17:49 both were 0.24.0 (log); the launcher
  pointed at the 0.24.0 copy (`app` at 16:13 ran 0.24.0).
- **A container migration**: unrelated; the window and the update ran on the host.

Not established: whether the window was looked at between 10:50 and 13:15 (it does not change the cause).

## A related trap found on the way

- A newer copy started while a window of an older one is open (the one-line installer opens the window in a
  graphical session, or a launcher of the new copy) showed the old window — old code, old answer — from 0.25 on
  (the session file holds a key since 0.25; a 0.24 server is not reached that way). Now the newer copy opens its own.
- After a catch-up by the one-line installer, the saved answer ("latest 0.24.0") made the new 0.25.1 window call
  itself a *development version* until it expired (seen with the public 0.25.1 in a Debian container,
  `check_catch_up.py` step 5: `"current": "0.25.1", "latest": "0.24.0", "status": "ahead"`). A saved answer older
  than the running or installed copy is now asked again.
- `restart_info` offered "Restart Corsu" for an installed copy *older* than the window (a development copy over an
  installed release). Now only for a newer one, or after an update that asks for it.

## What changed

- `src/update.py`: an answer is reused for an hour at most (`CHECK_EVERY = 3600`), never when it is older than the
  running or installed copy, and never when its time is in the future; `check()` says `fresh` (GitHub answered during
  this call) and keeps `checked` (when GitHub gave the answer shown); failures give `status: unknown` with
  `error_kind` (`network`, `rate_limit`, `http`, `bad_response`: an answer that is not a list, unreadable or cut
  short, or without a stable release); GitHub's `Retry-After` / rate-limit reset is respected; the comparison is
  made with the newest of the running and the installed copy (installed newer → restart, not install).
- `src/app.py`: the window checks when it opens (answer older than 10 minutes asked again), when a second launch
  shows it, and every hour while open (wall clock, so sleep counts; automatic updates still start only when Corsu is
  opened, as their switch says); a newer copy does not show an older window.
- Window: "Corsu est à jour (0.25.1 est la dernière version publiée). Dernière vérification : <date>." The facts
  show this window's version, the installed copy's, the latest release and the date of GitHub's answer; a failure
  stays "Vérification impossible : <raison>" with the last good answer and its date beside it.

## Catching up from an old version

A window of 0.24.0 or 0.25.1 keeps its old code: it cannot get these fixes. Ways out, none relying on a fresh
automatic check:
- the "Rechercher les mises à jour" button always asks GitHub (`force=True`) — it worked on 18 October;
- closing every Corsu window and opening Corsu again: 0.24.0 / 0.25.1 then use the saved answer if under 6 hours old;
- the one-line install (`install/get.sh`, `get.ps1`) over the existing installation: checked by
  `tests/e2e/check_catch_up.py` (public 0.24.0 → public latest, preferences, switched-off part, personal files, one
  copy in use, repair, refusal of the older copy).
