"""src/hyprland/config and src/hyprland/noctalia: Lua syntax, binds and key help from one list, no machine values,
AZERTY-safe workspace keys, Noctalia profile layers and palette contrast."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    tomllib = None
import unittest

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / 'src' / 'hyprland' / 'config'
NOCTALIA = ROOT / 'src' / 'hyprland' / 'noctalia'
LUA_FILES = sorted(CONFIG.rglob('*.lua'))
STUBS = Path('/usr/share/hypr/stubs/hl.meta.lua')
# Hyprland 0.56 links Lua 5.5; 5.4 parses everything these files use.
LUA = shutil.which('lua5.5') or shutil.which('lua5.4') or shutil.which('lua')
LUAC = shutil.which('luac5.5') or shutil.which('luac5.4') or shutil.which('luac')

# A stand-in for Hyprland's `hl` table: it records binds, config values, rules and commands, then prints them as JSON
# lines. Lua's own require resolves "corsu.x" to corsu/x.lua under the config folder, as Hyprland's does.
HARNESS = r'''
local config_dir, entry = arg[1], arg[2]
package.path = config_dir .. "/?.lua;" .. package.path
local out = {}
local function emit(kind, data) out[#out + 1] = { kind = kind, data = data } end
local function flatten(prefix, t)
  for k, v in pairs(t) do
    local key = prefix == "" and k or (prefix .. "." .. k)
    if type(v) == "table" and not (v[1] ~= nil or v.colors ~= nil) then flatten(key, v) else emit("config", key) end
  end
end
local function dispatcher(path)
  return setmetatable({}, {
    __index = function(_, name) return dispatcher(path == "" and name or (path .. "." .. name)) end,
    __call = function(_, args) return { dsp = path, args = args } end,
  })
end
hl = {
  dsp = dispatcher(""),
  bind = function(keys, action, opts) emit("bind", { keys = keys, action = action, opts = opts or {} }); return {} end,
  config = function(t) flatten("", t) end,
  monitor = function(t) emit("monitor", t) end,
  gesture = function(t) emit("gesture", t) end,
  curve = function() end,
  animation = function() end,
  layer_rule = function(t) emit("layer_rule", t.name) ; return {} end,
  window_rule = function(t) emit("window_rule", t.name); return {} end,
  on = function(event, fn) emit("on", event); fn(); return {} end,
  exec_cmd = function(cmd) emit("exec", cmd) end,
  env = function(k) emit("env", k) end,
}
dofile(config_dir .. "/" .. entry)
local function json(v)
  if type(v) == "table" then
    local is_list = #v > 0
    local parts = {}
    if is_list then
      for _, x in ipairs(v) do parts[#parts + 1] = json(x) end
      return "[" .. table.concat(parts, ",") .. "]"
    end
    for k, x in pairs(v) do parts[#parts + 1] = json(tostring(k)) .. ":" .. json(x) end
    return "{" .. table.concat(parts, ",") .. "}"
  elseif type(v) == "string" then
    return '"' .. v:gsub('[%c"\\]', function(c) return string.format("\\u%04x", c:byte()) end) .. '"'
  elseif v == nil then return "null"
  else return tostring(v) end
end
for _, item in ipairs(out) do print(json(item)) end
'''


def run_config(entry='hyprland.lua', machine=None):
    """Runs a config entry point under the stand-in; returns (records, help lines, process)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        config = tmp / 'hypr'
        shutil.copytree(CONFIG, config)
        if machine is not None:
            (config / 'corsu' / 'machine.lua').write_text(machine, encoding='utf-8')
        harness = tmp / 'harness.lua'
        harness.write_text(HARNESS, encoding='utf-8')
        runtime = tmp / 'run'
        runtime.mkdir()
        env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': str(tmp), 'XDG_RUNTIME_DIR': str(runtime)}
        proc = subprocess.run([LUA, str(harness), str(config), entry], capture_output=True, text=True, env=env,
                              timeout=30)
        records = [json.loads(line) for line in proc.stdout.splitlines() if line.startswith('{')]
        help_file = runtime / 'corsu' / 'hypr-keys.tsv'
        lines = help_file.read_text(encoding='utf-8').splitlines() if help_file.exists() else []
        return records, lines, proc


def keys_table():
    """keys.lua's entries, read through Lua itself."""
    script = ('package.path = arg[1] .. "/?.lua;" .. package.path\n'
              'local k = require("corsu.keys")\n'
              'for _, e in ipairs(k.binds) do\n'
              '  print((e.keys or "") .. "\\t" .. (e.label or "") .. "\\t" .. (e.help or "") .. "\\t" ..'
              ' tostring(e.workspaces or ""))\nend\n'
              'print("ROW\\t" .. table.concat(k.number_row, " "))\n')
    with tempfile.NamedTemporaryFile('w', suffix='.lua', delete=False) as f:
        f.write(script)
    try:
        out = subprocess.run([LUA, f.name, str(CONFIG)], capture_output=True, text=True, check=True).stdout
    finally:
        os.unlink(f.name)
    rows = [line.split('\t') for line in out.splitlines()]
    return [r for r in rows if r[0] != 'ROW'], next(r[1].split() for r in rows if r[0] == 'ROW')


class LuaSyntax(unittest.TestCase):
    def test_files_exist(self):
        names = {p.relative_to(CONFIG).as_posix() for p in LUA_FILES}
        for name in ('hyprland.lua', 'corsu/init.lua', 'corsu/input.lua', 'corsu/binds.lua', 'corsu/keys.lua',
                     'corsu/rules.lua', 'corsu/look.lua', 'corsu/autostart.lua'):
            self.assertIn(name, names)

    @unittest.skipUnless(LUAC, 'luac is not installed')
    def test_every_file_parses(self):
        for path in LUA_FILES:
            proc = subprocess.run([LUAC, '-p', str(path)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, f'{path}: {proc.stderr}')

    def test_init_requires_every_module(self):
        init = (CONFIG / 'corsu' / 'init.lua').read_text(encoding='utf-8')
        required = set(re.findall(r'require\("corsu\.(\w+)"\)', init))
        modules = {p.stem for p in (CONFIG / 'corsu').glob('*.lua')} - {'init', 'keys', 'machine_values'}
        self.assertEqual(required, modules)

    def test_starter_loads_corsu_then_user(self):
        text = (CONFIG / 'hyprland.lua').read_text(encoding='utf-8')
        self.assertLess(text.index('require("corsu.init")'), text.index('"user"'))


@unittest.skipUnless(LUA, 'lua is not installed')
class BindsAndHelp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records, cls.help, cls.proc = run_config()
        cls.binds = [r['data'] for r in cls.records if r['kind'] == 'bind']

    def test_config_runs_without_machine_file(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr)
        self.assertTrue(self.binds)

    def test_help_has_one_line_per_entry_and_every_bind_is_described(self):
        entries, _ = keys_table()
        self.assertEqual(len(self.help), len(entries))
        for (keys, label, text, _), line in zip(entries, self.help):
            self.assertEqual(line, f'{label or keys}\t{text}')
            self.assertTrue(text.strip(), keys)
        helps = {line.split('\t')[1] for line in self.help}
        for bind in self.binds:
            self.assertIn(bind['opts'].get('description'), helps, bind['keys'])

    def test_every_entry_is_bound(self):
        entries, row = keys_table()
        chords = [b['keys'] for b in self.binds]
        for keys, _, _, workspaces in entries:
            if workspaces:
                for code in row:
                    self.assertIn(f'{keys} + {code}', chords)
            else:
                self.assertIn(keys, chords)
        self.assertEqual(len(chords), len(set(chords)), 'a chord is bound twice')

    def test_workspace_keys_use_number_row_keycodes(self):
        # code:10..19 is the number row whatever the layout: & é " ' ( - è _ ç à on AZERTY, 1..0 on QWERTY.
        _, row = keys_table()
        self.assertEqual(row, [f'code:{n}' for n in range(10, 20)])
        targets = {}
        for bind in self.binds:
            m = re.fullmatch(r'SUPER \+ code:(\d+)', bind['keys'])
            if m:
                targets[int(m.group(1))] = bind['action']['args']['workspace']
        self.assertEqual(targets, {code: code - 9 for code in range(10, 20)})
        for bind in self.binds:
            self.assertIsNone(re.search(r'\+ [0-9]$', bind['keys']), f'{bind["keys"]} needs Shift on AZERTY')

    def test_mouse_binds_move_and_resize(self):
        by_keys = {b['keys']: b for b in self.binds}
        self.assertEqual(by_keys['SUPER + mouse:272']['action']['dsp'], 'window.drag')
        self.assertEqual(by_keys['SUPER + mouse:273']['action']['dsp'], 'window.resize')
        self.assertTrue(by_keys['SUPER + mouse:272']['opts']['mouse'])

    def test_media_keys_work_on_the_lock_screen(self):
        for bind in self.binds:
            if bind['keys'].startswith('XF86'):
                self.assertTrue(bind['opts'].get('locked'), bind['keys'])

    def test_only_binds_lua_binds(self):
        for path in LUA_FILES:
            if path.name != 'binds.lua':
                self.assertNotIn('hl.bind(', path.read_text(encoding='utf-8'), path)

    @unittest.skipUnless(tomllib, 'tomllib needs Python 3.11')
    def test_key_help_command_opens_the_noctalia_provider(self):
        profile = tomllib.loads((NOCTALIA / '00-corsu-profile.toml').read_text(encoding='utf-8'))
        entry = profile['shell']['launcher']['dmenu']['entry']['corsu-keys']
        commands = [b['action']['args'] for b in self.binds if b['keys'] == 'SUPER + F1']
        self.assertEqual(commands, [f'noctalia msg panel-toggle launcher /{entry["prefix"]}'])
        self.assertIn('corsu/hypr-keys.tsv', entry['command'])

    def test_noctalia_started_once_and_no_environment_set(self):
        execs = [r['data'] for r in self.records if r['kind'] == 'exec']
        self.assertEqual(sum('noctalia' in e for e in execs), 1)
        self.assertIn('pgrep', next(e for e in execs if 'noctalia' in e))
        # The session environment belongs to uwsm's env-hyprland (hyprland_system.py), not to hl.env().
        self.assertFalse([r for r in self.records if r['kind'] == 'env'])

    @unittest.skipUnless(STUBS.exists(), 'Hyprland stubs are not installed')
    def test_config_options_exist_in_hyprland(self):
        known = set(re.findall(r"\['([a-z0-9_.]+)'\]", STUBS.read_text(encoding='utf-8')))
        for key in {r['data'] for r in self.records if r['kind'] == 'config'}:
            self.assertIn(key, known)


@unittest.skipUnless(LUA, 'lua is not installed')
class MachineValues(unittest.TestCase):
    def test_detected_values_are_used(self):
        machine = ('return { keyboard = { layout = "fr", variant = "" },'
                   ' monitors = { { output = "X-1", mode = "preferred", position = "auto", scale = 1 } },'
                   ' apps = { terminal = "org.example.Term" } }')
        records, _, proc = run_config(machine=machine)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('input.kb_layout', [r['data'] for r in records if r['kind'] == 'config'])
        self.assertNotIn('input.kb_variant', [r['data'] for r in records if r['kind'] == 'config'])
        self.assertEqual([r['data']['output'] for r in records if r['kind'] == 'monitor'], ['X-1'])
        term = [r['data'] for r in records if r['kind'] == 'bind' and r['data']['keys'] == 'SUPER + Return'][0]
        self.assertIn("'org.example.Term.desktop'", term['action']['args'])

    def test_broken_machine_file_falls_back(self):
        records, _, proc = run_config(machine='return 42')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual([r['data']['output'] for r in records if r['kind'] == 'monitor'], [''])


class NoMachineValues(unittest.TestCase):
    PATTERNS = [
        r'\b(e?DP|HDMI-A|DVI|VGA)-\d', r'/dev/dri', r'\bcard\d', r'pci-0000', r'\b2560\b', r'\b1600\b', r'@240',
        r'miku', r'/home/', r'\bkalt\b', r'kb_layout\s*=\s*"', r'AQ_DRM_DEVICES', r'XCURSOR', r'scale\s*=\s*1\.6',
    ]

    def test_templates_carry_no_machine_values(self):
        files = LUA_FILES + sorted(NOCTALIA.rglob('*.toml')) + [NOCTALIA / 'qt6ct.conf']
        for path in files:
            text = path.read_text(encoding='utf-8')
            for pattern in self.PATTERNS:
                self.assertIsNone(re.search(pattern, text), f'{path.name}: {pattern}')


@unittest.skipUnless(tomllib, 'tomllib needs Python 3.11')
class NoctaliaProfile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = tomllib.loads((NOCTALIA / '00-corsu-profile.toml').read_text(encoding='utf-8'))
        cls.language = tomllib.loads((NOCTALIA / '00-corsu-language.toml').read_text(encoding='utf-8'))

    def test_files_sort_before_the_persons_config(self):
        for name in ('00-corsu-profile.toml', '00-corsu-language.toml'):
            self.assertLess(name, 'config.toml')

    def test_language_file_only_sets_the_language(self):
        self.assertEqual(self.language, {'shell': {'lang': 'co'}})
        self.assertNotIn('lang', self.profile.get('shell', {}))

    def test_no_template_writes_files_shared_with_plasma(self):
        theme = self.profile['theme']
        self.assertFalse(theme['sync_color_scheme'])
        self.assertEqual(theme['templates']['builtin_ids'], ['qt'])

    def test_bar_has_the_first_login_widgets(self):
        bar = self.profile['bar']['default']
        widgets = bar['start'] + bar['center'] + bar['end']
        for name in ('launcher', 'workspaces', 'taskbar', 'tray', 'clock', 'battery', 'network', 'bluetooth', 'volume',
                     'brightness', 'notifications', 'control-center', 'session'):
            self.assertIn(name, widgets)
        mic = [w for w in widgets if self.profile.get('widget', {}).get(w, {}).get('device') == 'input']
        self.assertEqual(len(mic), 1)

    def test_polkit_agent_and_uwsm_logout(self):
        self.assertTrue(self.profile['shell']['polkit_agent'])
        actions = self.profile['shell']['session']['actions']
        self.assertEqual([a['action'] for a in actions], ['lock', 'logout', 'lock_and_suspend', 'reboot', 'shutdown'])
        self.assertTrue(actions[1]['command'].startswith('uwsm stop'))

    def test_profile_selects_a_shipped_palette(self):
        name = self.profile['theme']['custom_palette']
        self.assertTrue((NOCTALIA / 'palettes' / f'{name}.json').exists())


def luminance(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


class Palettes(unittest.TestCase):
    PAIRS = [('mOnPrimary', 'mPrimary'), ('mOnSecondary', 'mSecondary'), ('mOnTertiary', 'mTertiary'),
             ('mOnError', 'mError'), ('mOnSurface', 'mSurface'), ('mOnSurfaceVariant', 'mSurfaceVariant'),
             ('mOnSurfaceVariant', 'mSurface'), ('mOnHover', 'mHover'), ('mPrimary', 'mSurface')]

    def test_text_is_readable_on_every_surface(self):
        paths = sorted((NOCTALIA / 'palettes').glob('*.json'))
        self.assertEqual([p.stem for p in paths], ['Corsu-Maquis', 'Corsu-Mare'])
        for path in paths:
            palette = json.loads(path.read_text(encoding='utf-8'))
            for mode in ('dark', 'light'):
                colors = palette[mode]
                for fg, bg in self.PAIRS:
                    ratio = contrast(colors[fg], colors[bg])
                    self.assertGreaterEqual(ratio, 4.5, f'{path.stem} {mode}: {fg} on {bg} = {ratio:.2f}')


if __name__ == '__main__':
    unittest.main()
