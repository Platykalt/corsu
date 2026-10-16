# Installing and updating Corsu: one managed installation per user

Contract between the installer, the updater and the Corsu window (October 2026). Developer page.

## One installation, one place

- Every way in (extracted archive, `install/get.sh` / `get.ps1`, the window's update button) runs the same code:
  `src/installer.py`, which deploys the release into the per-user data folder `corsu.DATA` (`~/.local/share/corsu`,
  `%LOCALAPPDATA%\corsu`, `~/Library/Application Support/corsu`) as `releases/<fingerprint>/` and re-runs itself from
  there. Launchers and shortcuts only ever point into `corsu.DATA`. An extracted archive or a git clone is never
  registered as an installation.
- `corsu.DATA/installation.json` (`corsu.STATE`) is the only record of what Corsu changed. It is shared by every
  release copy and is never merged with another file.
- Version policy, decided before anything is written: newer than the installed release → update; same → repair
  (re-apply, no duplicate records); older → refused unless `--allow-downgrade` is given explicitly; none → install.
  The installed release is the one the launchers point to (`installed_release()` in `src/update.py`).
- An update keeps the components recorded in the state, their enabled/disabled state, preferences, backups and
  uninstall records. It never enables a disabled component nor adds components the person did not choose. The
  original value of a setting is recorded once, at the first change, and never replaced by a value Corsu wrote.

## Lock

`corsu.DATA/lock`: one process at a time installs, updates, uninstalls, enables or disables. Created with an exclusive
open, holding the pid, start time and action; a lock whose process is gone is stale and taken over. A second run
waits up to a few seconds then stops with a clear message ("Corsu is already busy: <action> since <time>"). The
window maps it to "busy".

## Update

`src/update.py`:
- `check(force=False) -> dict`: `{'current', 'latest', 'tag', 'url', 'status', 'checked', 'error'}`. `status` is
  `up_to_date`, `available`, `unknown` (could not check: offline, rate limit — with `error`) or `ahead` (the running
  copy is newer than the latest release, e.g. a development build). Cached in `corsu.DATA/update.json` for 6 hours;
  only stable releases (not drafts, not pre-releases) are considered.
- `python update.py --install [--version X.Y.Z]`: downloads the archive of that exact tag
  (`releases/download/vX.Y.Z/…`, never `latest`), checks its `.sha256` and that its `src/release.json` names the same
  version, extracts safely (no path leaving the folder, no links, on every supported Python), runs its installer with
  the recorded components, and prints `@progress` lines then one `@result {json}` line:
  `{'corsu': 'updated'|'repaired'|'unchanged'|'failed', 'from', 'to', 'restart_app': bool, 'error'}`. The
  per-component outcome is in `installation.json` → `results` (activation per program, Minecraft folders…), which
  the window already shows.
- Preferences: `corsu.DATA/preferences.json`, read and written by `update.preferences()` /
  `update.set_preference(name, value)`. `auto_update` (default false): install new stable releases when the window
  opens.

## Recovery

The new release is downloaded, checked, extracted and deployed into its own folder before anything else changes; the
running copy is untouched. The state is written atomically (`save_state`, previous copy kept). An interrupted update
leaves the previous release in place with its launchers; running the installer or the update again resumes. Old
release copies are removed only after success and only when they are Corsu release folders in `corsu.DATA/releases`
(fingerprint name, `src/release.json` inside) that nothing uses. Original-setting backups in `corsu.DATA/backups`
are never pruned.

## File ownership during this work

- Update engine: `src/update.py`, `src/installer.py`, `install/*`, the bookkeeping of `src/corsu.py` (`install`,
  `Installer`, lock), `tests/test_update.py`, `tests/test_installer.py`, `tests/e2e/check_update.py`.
- Window: `src/app.py`, `src/app/index.html`, `tests/test_app*.py`.
- Minecraft presentation: `tools/mcreport.py`, `minecraft/README.md`, `minecraft/java/README.md`,
  `minecraft/java/COMPATIBILITY.md`, `minecraft/java/STATUS.md`, `docs/*/minecraft*.md`, the Minecraft blocks of
  `README.md` and `.github/RELEASE_NOTES.md`, `tests/test_mcreport.py`.
- Lead: Discord plugin, CI, integration, this page.
