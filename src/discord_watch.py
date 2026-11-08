#!/usr/bin/env python3
"""Watch Discord's start and tell the person when it does not finish starting (docs/dev/discord-watch.md).

`discord_watch.py launch [--from shortcut|autostart] -- <Discord command> [args]` starts Discord FIRST, detached,
with its arguments unchanged (discord:// links included), then follows Discord's own renderer log
(<user data>/logs/renderer_js.log) from where it was at launch, for at most WINDOW seconds, and records the outcome
in Corsu's data folder (discord-watch/state.json). It never touches Discord's process: no debugging port, no kill.
Any watcher error after Discord started is only logged. `scan_last_start()` classifies the last start found in the
log after the fact. Only log lines matching the known Discord/Vencord patterns below are ever kept, redacted: never
message content.

Discord is started before anything heavy is imported, so the watcher never delays it.
"""
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

WINDOW = 180          # seconds a start may take before it counts as slow
GRACE = 30            # after an uncaught error, seconds Discord still gets to reach its UI
CORSU_WAIT = 15       # after the UI, seconds left for Vencord to start the Corsu plugin
TAIL = 2_000_000      # bytes of the log read by the post-hoc scan
EVIDENCE = 20
PROBLEMS = ('vencord-error', 'start-error', 'slow', 'network', 'offscreen')
GOOD = ('ok', 'ok-corsu')
PROCESS_NAMES = ('Discord', 'DiscordPTB', 'DiscordCanary')
SYSTEM_APPLICATIONS = Path('/usr/share/applications')
DESKTOP_IDS = ('discord.desktop', 'discord-ptb.desktop', 'discord-canary.desktop')

LINE = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d(?:\.\d+)?)\] \[(\w+)\]\s*(.*)$')
# Vencord logs through console styles: "Vencord %c %c PluginManager  background: …; color: black; …; Starting plugin X".
STYLE = re.compile(r'%c\s*|\s*background: [^;]*;(?: [\w-]+: [^;]*;)*')
# Which lines are kept, and what they mean. Checked against real Discord 1.0.168 logs (tests/fixtures/discord-watch).
KINDS = (
    # The UI is drawn: logged in (gateway open) or the login page (its QR-code login socket).
    ('ui', re.compile(r'^\[Flux\] Dispatching CONNECTION_OPEN|^\[useAuthWebsocket\] .*connecting to')),
    ('corsu', re.compile(r'^Vencord PluginManager Starting plugin Corsu$')),
    # Discord's page could not load (offline, proxy): its preload then runs on Chromium's error page, where storage is
    # denied, and Discord retries. Seen with Discord 1.0.168 behind an unreachable proxy.
    ('network', re.compile(r"^Uncaught SecurityError: Failed to read the 'localStorage' property from 'Window': "
                           r"Access is denied for this document")),
    # Thrown on purpose by Vencord's NoTrack; the RPC port is taken when another program holds it: both harmless.
    ('ignored', re.compile(r'^Uncaught Error: (?:Sentry successfully disabled|listen EADDRINUSE)')),
    ('uncaught', re.compile(r'^Uncaught ')),
    ('vencord', re.compile(r'^Vencord ')),
    ('updating', re.compile(r'^splashScreenPreload: onStateUpdate: \{"status":"(?:downloading|installing|update-available|restarting)')),
    ('network', re.compile(r'^splashScreenPreload: onStateUpdate: \{"status":"update-failure"|^\[GatewaySocket\] .*WS CLOSED'
                           r'|network detected offline|net::ERR_(?:INTERNET_DISCONNECTED|NAME_NOT_RESOLVED|NETWORK_CHANGED'
                           r'|CONNECTION_\w+|PROXY_\w+|TIMED_OUT)')),
    ('splash', re.compile(r'^splashScreenPreload: ')),
    # Discord's own bundle ran its start-up: the crash, if any, came later than module loading.
    ('app', re.compile(r'^\[default\] \[(?:BUILD|NATIVE) INFO\]')),
)
EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')


def config_folder():
    """Where Discord keeps its user data (corsu.CONFIG, computed without importing corsu)."""
    if sys.platform == 'win32':
        return Path(os.environ.get('APPDATA', Path.home() / 'AppData/Roaming'))
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support'
    return Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))


def folder():
    import corsu  # only after Discord started
    return corsu.DATA / 'discord-watch'


def user_data_dir(command=()):
    """Discord's user-data folder for a command: --user-data-dir, else by channel (stable, PTB, Canary)."""
    for argument in command:
        if argument.startswith('--user-data-dir='):
            return Path(argument.split('=', 1)[1])
    text = ' '.join(command).lower()
    name = 'discordcanary' if 'canary' in text else 'discordptb' if 'ptb' in text else 'discord'
    return config_folder() / name


def discord_running():
    """Whether a Discord process (stable, PTB or Canary) is open. Unknown counts as open: nothing is then changed."""
    try:
        if sys.platform == 'win32':
            import corsu  # Windows has no wrapper: Corsu's window calls this, corsu is already loaded there
            output = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'],
                                    **corsu.hidden(capture_output=True, text=True, check=False)).stdout.lower()
            return any(f'"{name.lower()}.exe"' in output for name in PROCESS_NAMES)
        if sys.platform == 'darwin':
            return any(subprocess.run(['pgrep', '-x', name], capture_output=True, check=False).returncode == 0
                       for name in PROCESS_NAMES)
        for comm in Path('/proc').glob('[0-9]*/comm'):
            try:
                if comm.read_text().strip() in PROCESS_NAMES:
                    return True
            except OSError:
                continue
        return False
    except OSError:
        return True


def default_command():
    if sys.platform == 'win32':
        update = Path(os.environ.get('LOCALAPPDATA', '')) / 'Discord/Update.exe'
        return [str(update), '--processStart', 'Discord.exe']
    if sys.platform == 'darwin':
        return ['open', '-a', 'Discord']
    # The `Discord` link Discord's Linux updater keeps next to its versions is the real binary; else the packaged one.
    link = config_folder() / 'discord/Discord'
    if link.exists():
        return [str(link)]
    import shutil
    if shutil.which('discord'):
        return [shutil.which('discord')]
    import installer
    location = installer.discord_location()
    return [str(Path(location) / 'Discord')] if location else ['discord']


def start(command):
    """Start Discord detached from this process, so it outlives the watcher and never waits on it."""
    options = {'stdin': subprocess.DEVNULL, 'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL, 'close_fds': True}
    if sys.platform == 'win32':
        options['creationflags'] = 0x08000000 | 0x00000200  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
    else:
        options['start_new_session'] = True
    return subprocess.Popen(command, **options)


def size(path):
    try:
        return Path(path).stat().st_size
    except OSError:
        return 0


# ---------------------------------------------------------------- log reading and classification

def clean(text):
    return re.sub(r'\s+', ' ', STYLE.sub(' ', text)).strip()


def redact(text):
    text = text.replace(str(Path.home()), '~')
    text = EMAIL.sub('<email>', text)
    text = re.sub(r'\b\d{15,21}\b', '<id>', text)
    # Tokens, fingerprints, session ids, hashes.
    text = re.sub(r'[A-Za-z0-9_-]{24,}(?:\.[A-Za-z0-9_-]{6,}){0,2}', '<token>', text)
    return text[:300]


def parse(text):
    """The known lines of a renderer_js.log excerpt, in order: [{t, level, kind, text}]. Any other line is dropped;
    lines without a timestamp (stack traces) only extend an uncaught error's text, for the Vencord check."""
    entries = []
    for raw in text.splitlines():
        match = LINE.match(raw)
        if not match:
            if entries and entries[-1]['kind'] == 'uncaught':
                entries[-1]['stack'] = entries[-1].get('stack', '') + raw[:300] + '\n'
            continue
        stamp, level, message = match.groups()
        message = clean(message)
        kind = next((name for name, pattern in KINDS if pattern.search(message)), None)
        if kind is None or (kind == 'uncaught' and level != 'error'):
            continue
        try:
            moment = datetime.datetime.strptime(stamp, '%Y-%m-%d %H:%M:%S.%f' if '.' in stamp else '%Y-%m-%d %H:%M:%S').timestamp()
        except ValueError:
            continue
        entries.append({'t': moment, 'level': level, 'kind': kind, 'text': message})
    return entries


def sessions(entries):
    """Split at the splash's signalReady (a new start); a second signalReady before anything else is the same start."""
    groups = []
    for entry in entries:
        if entry['kind'] == 'splash' and entry['text'].endswith('signalReady') \
                and (not groups or any(item['kind'] != 'splash' for item in groups[-1])):
            groups.append([])
        if groups:
            groups[-1].append(entry)
    return groups


def classify(entries, alive, now, started, window=WINDOW, grace=GRACE):
    """The state of one start from its log lines, or None while undecided."""
    kinds = {entry['kind'] for entry in entries}
    if 'ui' in kinds:
        return 'ok-corsu' if 'corsu' in kinds else 'ok'
    for index, crash in enumerate(entries):
        if crash['kind'] != 'uncaught':
            continue
        before = entries[:index]
        # The renderer log has no stack: a crash while Vencord patches Discord's modules, before Discord's own
        # start-up ran, is Vencord's probable doing (Discord 1.0.168 with Vencord 1.15.9: "i.A is not a constructor").
        named = 'vencord' in (crash['text'] + crash.get('stack', '')).lower() or 'webpackpatcher' in crash['text'].lower()
        during = any(entry['kind'] == 'vencord' for entry in before) and not any(entry['kind'] == 'app' for entry in before)
        if 'network' in kinds and not (named or during):
            continue  # Discord's page did not load: its errors follow from that
        if not alive or now - crash['t'] >= grace:
            return 'vencord-error' if named or during else 'start-error'
        break
    if not alive:
        # Discord's updater quits and starts the new version itself.
        return 'updating' if 'updating' in kinds else 'closed'
    if now - started >= window:
        return 'network' if 'network' in kinds else 'updating' if 'updating' in kinds else 'slow'
    return None


def evidence(entries):
    """At most EVIDENCE redacted lines: the routine "Starting plugin X" lines are left out, repeats collapsed."""
    kept = []
    for entry in entries:
        if entry['kind'] == 'vencord' and 'Starting plugin ' in entry['text']:
            continue
        line = redact(entry['text'])
        if kept and kept[-1]['line'] == line:
            continue
        kept.append({'t': entry['t'], 'kind': entry['kind'], 'line': line})
    return kept if len(kept) <= EVIDENCE else kept[:5] + kept[-(EVIDENCE - 5):]


def app_version(entries, client):
    for entry in entries:
        match = re.search(r'\[NATIVE INFO\] host ([\d.]+)', entry['text'])
        if match:
            return match.group(1)
    name = Path(client).name if client else ''
    return name[4:] if name.startswith('app-') else None


# ---------------------------------------------------------------- state

def read_state():
    try:
        return json.loads((folder() / 'state.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def write_json(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.corsu-tmp')
    temp.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, path)


def write_state(document):
    write_json(folder() / 'state.json', document)


def client_folder(user_data):
    """The Discord app folder a launch runs: Linux's `Discord` link names it; else the one the installer finds."""
    link = Path(user_data) / 'Discord'
    if sys.platform.startswith('linux') and link.exists():
        return link.resolve().parent
    import installer
    return installer.discord_location()


def vencord_info(location):
    """Whether Discord at `location` loads a Vencord build, and which one (its dist/corsu-build.json)."""
    import installer
    info = {'injected': False, 'revision': None, 'corsu_version': None, 'dist': None}
    try:
        data = installer.discord_archive(location).read_bytes() if location else b''
    except OSError:
        return info
    match = re.search(rb'require\(("(?:[^"\\]|\\.)*patcher\.js")\)', data) if installer.vencord_launcher(data) else None
    if match:
        dist = Path(json.loads(match.group(1))).parent
        build = installer.build_record(dist.parent)
        info.update(injected=True, dist=str(dist), revision=build.get('vencord_revision'), corsu_version=build.get('corsu_version'))
    return info


def make_state(state, started, launch, client, entries, decided=None, incident=None):
    return {'version': 1, 'incident': incident or (str(uuid.uuid4()) if state in PROBLEMS else None), 'state': state,
            'started_at': started, 'decided_at': decided, 'launch': launch, 'client': str(client) if client else None,
            'session': entries[0]['t'] if entries else None, 'app_version': app_version(entries, client),
            'vencord': vencord_info(client), 'evidence': evidence(entries), 'notified': False, 'dismissed': False}


MESSAGES = {
    'vencord-error': ("Discord did not finish starting, probably because of the translation (Vencord). Open Corsu to start "
                      "it without the translation or look for an update.",
                      "Discord n'a pas fini de démarrer, probablement à cause de la traduction (Vencord). Ouvrez Corsu pour "
                      "le démarrer sans la traduction ou chercher une mise à jour."),
    'start-error': ("Discord stopped with an error while starting. Open Corsu to see what happened.",
                    "Discord s'est arrêté sur une erreur au démarrage. Ouvrez Corsu pour voir ce qui s'est passé."),
    'slow': ("Discord has not finished starting after 3 minutes. The cause is unknown.",
             "Discord n'a pas fini de démarrer après 3 minutes. La cause est inconnue."),
    'network': ("Discord is still starting: it could not reach its servers. Check the connection.",
                "Discord démarre encore : il n'a pas pu joindre ses serveurs. Vérifiez la connexion."),
    'offscreen': ("Discord started, but its window is outside the screens.",
                  "Discord a démarré, mais sa fenêtre est hors des écrans."),
}


def alert(record):
    """One notification per incident, through Corsu's notifier (src/notify.py, which also keeps it to one per incident):
    notify_incident(record) when it has it, which owns the wording, else notify(title, body, …) with these texts."""
    if record['state'] not in PROBLEMS or record.get('notified'):
        return record
    try:
        import notify
    except ImportError:
        return record
    import corsu
    if hasattr(notify, 'notify_incident'):
        sent = notify.notify_incident(record)
    else:
        sent = notify.notify(corsu.t('Discord', 'Discord'), corsu.t(*MESSAGES[record['state']]),
                             action='discord-recovery', incident=record['incident'])
    record['notified'] = bool(sent)
    write_state(record)
    return record


def dismiss(incident):
    """"Later" in Corsu's window: the incident stays recorded but is no longer shown. Only when it is still the last one."""
    record = read_state()
    if not incident or record.get('incident') != incident:
        return {'ok': False, 'reason': 'other-incident'}
    record['dismissed'] = True
    write_state(record)
    return {'ok': True, 'reason': None}


# ---------------------------------------------------------------- watching

def pid_alive(pid):
    if sys.platform == 'win32':
        # os.kill on Windows terminates the process: ask tasklist instead.
        import corsu
        output = subprocess.run(['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                                **corsu.hidden(capture_output=True, text=True, check=False)).stdout
        return f'"{pid}"' in output
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def acquire_lock():
    """One supervisor at a time: False when another live watcher holds the lock."""
    lock = folder() / 'lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                pid = int(lock.read_text() or 0)
            except (OSError, ValueError):
                pid = 0
            if pid and pid != os.getpid() and pid_alive(pid):
                return False
            lock.unlink(missing_ok=True)
            continue
        with os.fdopen(descriptor, 'w') as handle:
            handle.write(str(os.getpid()))
        return True
    return False


def release_lock():
    lock = folder() / 'lock'
    try:
        if int(lock.read_text() or 0) == os.getpid():
            lock.unlink()
    except (OSError, ValueError):
        pass


def offscreen():
    """On Hyprland: a description of Discord's window when it lies outside every monitor, else None."""
    import shutil
    if not (os.environ.get('HYPRLAND_INSTANCE_SIGNATURE') and shutil.which('hyprctl')):
        return None
    try:
        clients = json.loads(subprocess.run(['hyprctl', 'clients', '-j'], capture_output=True, text=True, timeout=5).stdout)
        monitors = json.loads(subprocess.run(['hyprctl', 'monitors', '-j'], capture_output=True, text=True, timeout=5).stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
    return outside(clients, monitors)


def outside(clients, monitors):
    windows = [client for client in clients if str(client.get('class', '')).lower().startswith('discord')
               and client.get('mapped', True)]

    def visible(window):
        (x, y), (width, height) = window['at'], window['size']
        return any(x < monitor['x'] + monitor['width'] / monitor.get('scale', 1) and x + width > monitor['x']
                   and y < monitor['y'] + monitor['height'] / monitor.get('scale', 1) and y + height > monitor['y']
                   for monitor in monitors)
    if windows and not any(visible(window) for window in windows):
        window = windows[0]
        return f'Discord window at {window["at"][0]},{window["at"][1]} size {window["size"][0]}x{window["size"][1]} outside all monitors'
    return None


class LogFollower:
    """New complete lines of a log from an offset; a log that shrank (rotated) is read again from its start."""

    def __init__(self, path, offset):
        self.path, self.offset, self.pending = Path(path), offset, ''

    def read(self):
        current = size(self.path)
        if current < self.offset:
            self.offset = 0
        if current == self.offset:
            return ''
        with open(self.path, 'rb') as handle:
            handle.seek(self.offset)
            data = handle.read(current - self.offset)
        self.offset = current
        text = self.pending + data.decode('utf-8', errors='replace')
        complete, _, self.pending = text.rpartition('\n')
        return complete + '\n' if complete else ''


def watch(follower, alive, started, launch='unknown', client=None, window=WINDOW, clock=time.time, sleep=time.sleep,
          check_offscreen=offscreen):
    """Follow one start until a decisive signal or the end of the window; record and return the state."""
    text, extended, dead_since, ui_at = '', False, None, None
    while True:
        text += follower.read()
        entries = parse(text)
        now = clock()
        living = alive()
        # A process can be briefly gone while Discord hands over to its updated copy.
        dead_since = None if living else (dead_since or now)
        state = classify(entries, living or now - dead_since < 3, now, started, window)
        if state == 'updating' and living and not extended:
            extended, window = True, window + WINDOW
            state = None
        if state == 'ok' and any(entry['kind'] == 'vencord' for entry in entries):
            ui_at = ui_at or now
            if now - ui_at < CORSU_WAIT and living:
                state = None
        if state:
            break
        sleep(1)
    record = make_state(state, started, launch, client, entries, decided=now)
    if state in GOOD:
        sleep(3)
        where = check_offscreen()
        if where:
            record.update(state='offscreen', incident=str(uuid.uuid4()))
            record['evidence'] = (record['evidence'] + [{'t': clock(), 'kind': 'offscreen', 'line': where}])[-EVIDENCE:]
    write_state(record)
    return record


def launch_kind(command, given):
    if any(argument.startswith('discord://') for argument in command):
        return 'url'
    return given or 'unknown'


def launch(command=None, kind=None, window=WINDOW):
    """Start Discord, then watch its start. Returns the recorded state (None when not watched)."""
    command = list(command or default_command())
    # Read before starting (the open instance and the log's end), but never at the cost of starting Discord.
    try:
        user_data = user_data_dir(command)
        log = user_data / 'logs/renderer_js.log'
        running, offset = discord_running(), size(log)
    except Exception:
        user_data = log = running = offset = None
    started = time.time()
    process = start(command)
    if log is None:
        return None
    try:
        import logbook
        if running or not acquire_lock():
            # Discord takes the arguments over in its open instance ("Quitting secondary instance"): nothing to watch.
            logbook.write(f'discord-watch: {"Discord already running" if running else "another watcher is active"}; not watching')
            if running and read_state().get('state') not in PROBLEMS:
                write_state({'version': 1, 'incident': None, 'state': 'already-running', 'started_at': started,
                             'decided_at': started, 'launch': 'already-running', 'client': None, 'session': None,
                             'app_version': None, 'vencord': None, 'evidence': [], 'notified': False, 'dismissed': False})
            return None
        try:
            client = client_folder(user_data)
            record = watch(LogFollower(log, offset), lambda: process.poll() is None or discord_running(), started,
                           launch_kind(command, kind), client, window)
            logbook.write(f'discord-watch: {record["state"]}')
            return alert(record)
        finally:
            release_lock()
    except Exception as error:  # Discord is started: the watcher's own failure must never matter to it.
        try:
            import logbook
            logbook.write(f'discord-watch: watcher error after Discord started: {error!r}')
        except Exception:
            pass
        return None


def scan_last_start(user_data=None, now=None, alive=None, write=True):
    """Classify the last start in Discord's log after the fact (Corsu's window, Windows and macOS, updater restarts).
    Returns its state record (the one already recorded for that start when there is one), or None when undecided."""
    user_data = Path(user_data) if user_data else user_data_dir()
    log = user_data / 'logs/renderer_js.log'
    try:
        with open(log, 'rb') as handle:
            handle.seek(max(0, size(log) - TAIL))
            text = handle.read().decode('utf-8', errors='replace')
    except OSError:
        return None
    groups = sessions(parse(text))
    if not groups:
        return None
    last = groups[-1]
    alive = discord_running() if alive is None else alive
    now = time.time() if now is None else now
    state = classify(last, alive, now, last[0]['t'])
    if state is None:
        return None
    current = read_state()
    if current.get('session') == last[0]['t'] or current.get('state') == 'rescue':
        return current
    record = make_state(state, last[0]['t'], 'unknown', client_folder(user_data), last, decided=now)
    if write:
        write_state(record)
    return record


# ---------------------------------------------------------------- rescue

def in_rescue():
    return (folder() / 'rescue.json').exists()


def rescue_check():
    """Whether Discord can be put back to its original archive (no translation), and why not."""
    import corsu
    import installer
    if discord_running():
        return {'ok': False, 'reason': 'running', 'location': None}
    launched = read_state().get('client')
    records = {name: record for name, record in corsu.load_state()['files'].items() if record.get('discord_location')}
    location = launched or (str(installer.discord_location()) if installer.discord_location() else None)
    found = next(((name, record) for name, record in records.items()
                  if Path(record['discord_location']).resolve() == Path(location).resolve()), None) if location else None
    if not records:
        return {'ok': False, 'reason': 'no-record', 'location': location}
    if not found:
        return {'ok': False, 'reason': 'unknown-app', 'location': location}
    name, record = found
    backup = Path(record['backup']) if record.get('backup') else None
    if not backup or not backup.is_file():
        return {'ok': False, 'reason': 'backup-missing', 'location': location}
    original = backup.read_bytes()
    if installer.vencord_launcher(original):
        return {'ok': False, 'reason': 'launcher-backup', 'location': location}
    app = Path(name)
    moved = app.with_name('_app.asar')
    current = app.read_bytes() if app.is_file() else b''
    # Discord must be as Corsu left it: app.asar the recorded launcher, _app.asar (when kept) the same original.
    if corsu.digest(current) != record.get('installed_sha256') or not installer.vencord_launcher(current) \
            or (moved.is_file() and corsu.digest(moved.read_bytes()) != corsu.digest(original)):
        return {'ok': False, 'reason': 'backup-mismatch', 'location': location}
    if not os.access(app.parent, os.W_OK):
        return {'ok': False, 'reason': 'read-only', 'location': location}
    return {'ok': True, 'reason': None, 'location': location, 'app': name}


def rescue(incident=None):
    """Start Discord without the translation from now on: restore its original archive (Vencord's _app.asar copy is
    kept), until reactivate(). Never closes Discord. Profiles and settings are not touched."""
    import corsu
    check = rescue_check()
    if not check['ok']:
        return check
    app = Path(check['app'])
    state = corsu.load_state()
    record = state['files'][check['app']]
    original = Path(record['backup']).read_bytes()
    temp = app.with_name(app.name + '.corsu-tmp')
    temp.write_bytes(original)
    if record.get('mode') is not None:
        temp.chmod(record['mode'])
    os.replace(temp, app)
    # Uninstalling or reinstalling sees the original as what Corsu left there, not as a change made by someone else.
    record['installed_sha256'] = corsu.digest(original)
    record['rescue'] = True
    corsu.save_state(state)
    watched = read_state()
    write_json(folder() / 'rescue.json', {'location': check['location'], 'since': time.time(),
                                          'from_revision': (watched.get('vencord') or {}).get('revision'),
                                          'incident': incident or watched.get('incident')})
    write_state({**watched, 'version': 1, 'state': 'rescue', 'decided_at': time.time()})
    return {**check, 'ok': True}


def reactivate(window=WINDOW):
    """Put the translation back (the installer's install_discord), then watch a launch; back to rescue if it fails."""
    import corsu
    import installer
    if discord_running():
        return {'ok': False, 'reason': 'running'}
    try:
        info = json.loads((folder() / 'rescue.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {'ok': False, 'reason': 'not-in-rescue'}
    (folder() / 'rescue.json').unlink()
    try:
        state = corsu.load_state()
        for record in state['files'].values():
            record.pop('rescue', None)
        corsu.save_state(state)
        installer.install_discord(Path(info['location']))
    except Exception as error:
        return {'ok': False, 'reason': 'install-failed', 'error': str(error), 'rescue': rescue(info.get('incident'))}
    record = launch(window=window)
    if record is None or record['state'] not in PROBLEMS:
        return {'ok': True, 'reason': None, 'state': record and record['state']}
    return {'ok': False, 'reason': record['state'], 'rescue': rescue(record['incident'])}


# ---------------------------------------------------------------- Linux desktop entries

def wrapper_text(original, python, kind):
    """A copy of Discord's desktop entry whose Exec lines start Discord through the watcher, same arguments."""
    import shlex
    import corsu
    prefix = f'{shlex.quote(str(python))} {shlex.quote(str(corsu.SRC / "discord_watch.py"))} launch --from {kind} -- '
    return re.sub(r'^(Exec=)(.*)$', lambda match: match.group(1) + prefix + match.group(2), original, flags=re.M)


def wrapper_places():
    """(path written, entry it wraps, launch kind) for Discord's menu entries, and its autostart entry when there is one."""
    import corsu
    places = []
    for desktop_id in DESKTOP_IDS:
        path = corsu.HOME / '.local/share/applications' / desktop_id
        places.append((path, SYSTEM_APPLICATIONS / desktop_id, 'shortcut'))
        places.append((corsu.CONFIG / 'autostart' / desktop_id, None, 'autostart'))
    return places


def install_wrappers(installer, python):
    """Linux: point Discord's menu (and autostart) entries at the watcher; recorded, so uninstall puts them back."""
    import corsu
    for path, system, kind in wrapper_places():
        key = str(path)
        record = installer.state['files'].get(key)
        if record and (not path.exists() or corsu.digest(path.read_bytes()) != record['installed_sha256']):
            # Discord or the person rewrote or removed it since: theirs now, wrapped again below if it is there.
            installer.state['files'].pop(key)
            record = None
        if record:
            source = Path(record['backup']) if record.get('backup') else system
        else:
            source = path if path.exists() else system
        if source is None or not source.is_file():
            continue
        text = source.read_text(encoding='utf-8')
        if 'discord_watch.py' in text or not re.search(r'^Exec=', text, flags=re.M):
            continue
        installer.write(path, wrapper_text(text, python, kind))
        installer.state['files'][key]['component'] = 'discord'
        installer.state['files'][key]['discord_watch'] = True
    corsu.save_state(installer.state)


def remove_wrappers(installer):
    import corsu
    for name, record in list(installer.state['files'].items()):
        if record.get('discord_watch'):
            if corsu.restore(Path(name), record):
                installer.state['files'].pop(name)
    corsu.save_state(installer.state)


def update_wrappers(installer, python):
    """Wrappers on Linux while the watch is wanted (preference "discord_watch", on by default), else none."""
    import corsu
    import update
    if corsu.PLATFORM == 'linux' and update.preferences()['discord_watch']:
        install_wrappers(installer, python)
    else:
        remove_wrappers(installer)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ['launch']:
        options, command = (argv[1:argv.index('--')], argv[argv.index('--') + 1:]) if '--' in argv else (argv[1:], [])
        kind = options[options.index('--from') + 1] if '--from' in options else None
        launch(command or None, kind)
        return 0
    if argv[:1] == ['scan']:
        print(json.dumps(scan_last_start(), ensure_ascii=False, indent=2))
        return 0
    print('Usage: discord_watch.py launch [--from shortcut|autostart] -- <Discord command> [arguments] | scan',
          file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())
