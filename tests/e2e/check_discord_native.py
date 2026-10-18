#!/usr/bin/env python3
"""Discord's texts drawn outside the page: the menu of the notification-area icon and the taskbar preview buttons.

Usage: check_discord_native.py VENCORD_DIR [--discord-bundle FILE]
Discord's page sends these texts to the desktop app (NativeUtils.setSystemTrayStrings and setThumbarButtons), which
draws them with the system's own menus: the page translator never sees them. The Corsu plugin patches those two
functions (index.ts, nativePatch in translate.ts). This check, in Node.js:
- bundles src/discord-plugin/translate.ts with Vencord's esbuild and the REAL generated dictionary
  (VENCORD_DIR/src/userplugins/corsu/dictionary.json, written by corsu.generate());
- applies the plugin's patches, the way Vencord does (\\i is an identifier, $self the plugin), to an excerpt of
  Discord's NativeUtils module (Discord's public web client, October 2026), then calls the patched functions with the
  strings Discord sends in French and in English (and with another product name, Discord PTB): what reaches the
  desktop app must be Corsican, the product name unchanged, and texts in another language left as they are;
- checks that the built bundle (VENCORD_DIR/dist/renderer.js) carries the patches;
- with --discord-bundle (a web.*.js of Discord's client, downloaded from discord.com/assets), checks that the find text
  is in exactly one module of it and that both patterns match there once.
A simulated call of the patched functions, not an observation of the real Discord app's menu.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent.parent

# Discord's NativeUtils module, October 2026 (web client, web.4d4b2f75fdea5470.js), the methods around the patched ones.
NATIVE_UTILS = ('setSystemTrayIcon(e){I.isPlatformEmbedded&&this.sendIPC(c.SYSTEM_TRAY_SET_ICON,e)},'
                'setSystemTrayApplications(e){I.isPlatformEmbedded&&this.sendIPC(c.SYSTEM_TRAY_SET_APPLICATIONS,e)},'
                'setSystemTrayStates(e){Y(c.SYSTEM_TRAY_SET_STATES,e)},'
                'setSystemTrayStrings(e){Y(c.SYSTEM_TRAY_SET_STRINGS,e)},'
                'setThumbarButtons(e){I.isPlatformEmbedded&&g.thumbar?.setThumbarButtons?.(e,this.isSystemDarkMode())},')

# What Discord's page sends (its function building them, with appName = friendlyReleaseName), from its French and
# English messages of October 2026 (keys zjuWNH, w4m945, wjcRFX, FJSZVM, uLddbQ, btxSdB, JO5lXN, PhnOeM, 0nUKy3,
# VuK9sC, mpd5Bv). French puts a no-break space before "!".
FRENCH = {
    'appName': 'Discord', 'openApp': 'Ouvrir Discord', 'mute': 'Rendre muet', 'deafen': 'Mettre en sourdine',
    'suppressed': 'Interdit', 'serverMuted': 'Serveur muet', 'serverDeafened': 'Mis en sourdine sur le serveur',
    'voiceSettings': 'Ouvrir les paramètres vocaux et vidéo', 'checkForUpdates': 'Rechercher les mises à jour…',
    'acknowledgements': 'Remerciements', 'quitApp': 'Quitter Discord',
    'closeHint': "Salut ! Discord s'exécutera en arrière-plan pour te permettre de rester en contact avec tes "
                 "ami(e)s. Tu peux faire un clic droit ici pour quitter.",
}
ENGLISH = {
    'appName': 'Discord', 'openApp': 'Open Discord', 'mute': 'Mute', 'deafen': 'Deafen', 'suppressed': 'Suppressed',
    'serverMuted': 'Server Muted', 'serverDeafened': 'Server Deafened', 'voiceSettings': 'Open Voice && Video Settings',
    'checkForUpdates': 'Check For Updates...', 'acknowledgements': 'Acknowledgements', 'quitApp': 'Quit Discord',
    'closeHint': 'Hi! Discord will run in the background to keep you in touch with your friends. You can right-click '
                 'here to quit.',
}
CLOSE_HINT = ('Salute! Discord ferma attivu in sfondulu per ch\'è tù fermi in cuntattu cù i to amichi. '
              'Poi fà un cliccu dirittu quì per esce.')
EXPECTED_FR = {
    'appName': 'Discord', 'openApp': 'Apre Discord', 'mute': 'Ammutulisce', 'deafen': "Disattivà l'ascoltu",
    'suppressed': 'Difesu', 'serverMuted': 'Servore mutu', 'serverDeafened': "Assurdatu nant'à u servore",
    'voiceSettings': 'Apre i parametri vucali è videò', 'checkForUpdates': "Circà l'aghjurnamenti…",
    'acknowledgements': 'Ringraziamenti', 'quitApp': 'Esce da Discord', 'closeHint': CLOSE_HINT,
}
EXPECTED_EN = {**EXPECTED_FR, 'serverMuted': "Mutu nant'à u servore", 'checkForUpdates': "Circà l'aghjurnamenti…"}
GERMAN = {'appName': 'Discord', 'openApp': 'Discord öffnen', 'mute': 'Stummschalten', 'quitApp': 'Discord beenden'}
# Taskbar preview buttons during a call (Windows): tooltips from Discord's messages YqAjXy, wjcRFX, 6vrfgt.
THUMBAR = [{'name': 'MUTE', 'active': True, 'tooltip': 'Ne plus rendre muet'},
           {'name': 'DEAFEN', 'active': False, 'tooltip': 'Mettre en sourdine'},
           {'name': 'DISCONNECT', 'active': True, 'tooltip': 'Déconnecter', 'flags': ['disabled']}]
THUMBAR_EXPECTED = [{'name': 'MUTE', 'active': True, 'tooltip': 'Ùn ammutulisce più'},
                    {'name': 'DEAFEN', 'active': False, 'tooltip': "Disattivà l'ascoltu"},
                    {'name': 'DISCONNECT', 'active': True, 'tooltip': 'Discunnette', 'flags': ['disabled']}]

RUN = r"""
// The bundle comes through a file: Windows limits the length of a command line.
const code = require("fs").readFileSync(process.argv[1], "utf8"), utils = process.argv[2];
const cases = JSON.parse(process.argv[3]);
const Corsu = new Function(code + "\nreturn Corsu;")();
// Vencord's canonicalizeMatch: \i is an identifier; $self the plugin object.
const canonical = re => new RegExp(re.source.replaceAll("\\i", "(?:[A-Za-z_$][\\w$]*)"), re.flags);
const plugin = { trayStrings: Corsu.translateTrayStrings, thumbarButtons: Corsu.translateThumbarButtons };
let patched = utils;
const applied = {};
for (const [name, replace] of [["trayStrings", "$&$1=$self.trayStrings($1);"], ["thumbarButtons", "$&$1=$self.thumbarButtons($1);"]]) {
    const before = patched;
    patched = patched.replace(canonical(Corsu.nativePatch[name]), replace.replaceAll("$self", "plugin"));
    applied[name] = before !== patched;
}
const sent = [];
const I = { isPlatformEmbedded: true }, c = new Proxy({}, { get: (_, key) => key });
const Y = (event, payload) => sent.push([event, payload]);
const g = { thumbar: { setThumbarButtons: payload => sent.push(["THUMBAR", payload]) } };
const NativeUtils = new Function("I", "c", "Y", "g", "plugin",
    "return {sendIPC(event, payload){Y(event, payload)},isSystemDarkMode(){return false}," + patched + "};")(I, c, Y, g, plugin);
const out = { applied, find: utils.includes(Corsu.nativePatch.find), results: {} };
for (const [name, strings] of Object.entries(cases.tray)) {
    NativeUtils.setSystemTrayStrings(strings);
    out.results[name] = sent.pop()[1];
}
NativeUtils.setThumbarButtons(cases.thumbar);
out.results.thumbar = sent.pop()[1];
out.untouched = cases.tray.french.openApp;  // the page keeps its own object
process.stdout.write(JSON.stringify(out));
"""

BUNDLE = r"""
const { build } = require(process.argv[1]);
build({ entryPoints: [process.argv[2]], bundle: true, write: false, format: 'iife', globalName: 'Corsu',
        platform: 'neutral', target: 'es2022', logLevel: 'error',
        plugins: [{ name: 'dictionary', setup(b) {
            b.onResolve({ filter: /dictionary\.json$/ }, () => ({ path: process.argv[3] })); } }] })
  .then(result => process.stdout.write(result.outputFiles[0].text));
"""

SCAN = r"""
const fs = require("fs");
const [bundle, find, ...patterns] = [fs.readFileSync(process.argv[1], "utf8"), process.argv[2], ...process.argv.slice(3)];
// Webpack modules of the bundle: `<id>(e,t,n){...}` entries; count those holding the find text.
const starts = [...bundle.matchAll(/[,{](\d+)\(e,t,n\)\{/g)].map(m => m.index);
const modules = starts.map((start, i) => bundle.slice(start, starts[i + 1] ?? bundle.length)).filter(m => m.includes(find));
const ident = "(?:[A-Za-z_$][\\w$]*)";
const counts = modules.length === 1 ? patterns.map(p => (modules[0].match(new RegExp(p.replaceAll("\\i", ident), "g")) || []).length) : [];
process.stdout.write(JSON.stringify({ modules: modules.length, counts }));
"""


def node(script, *arguments):
    result = subprocess.run(['node', '-e', script, *map(str, arguments)], capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise SystemExit(f'node failed ({result.returncode}):\n{result.stderr}')
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('vencord', type=Path)
    parser.add_argument('--discord-bundle', type=Path)
    arguments = parser.parse_args()
    vencord = arguments.vencord.resolve()
    dictionary = vencord / 'src/userplugins/corsu/dictionary.json'
    if not dictionary.is_file():
        raise SystemExit(f'{dictionary} is missing: run corsu.generate() (installer.prepare_build) first')
    esbuild = next((vencord / 'node_modules').resolve().glob('esbuild/lib/main.js'))
    code = node(BUNDLE, esbuild, ROOT / 'src/discord-plugin/translate.ts', dictionary)
    failures = []

    def check(label, found, expected):
        ok = found == expected
        print(f'{"PASS" if ok else "FAIL"}: {label} = {found!r}' + ('' if ok else f' (expected {expected!r})'))
        if not ok:
            failures.append(label)

    cases = {'tray': {'french': FRENCH, 'english': ENGLISH,
                      'ptb': {**FRENCH, 'appName': 'Discord PTB', 'openApp': 'Ouvrir Discord PTB',
                              'quitApp': 'Quitter Discord PTB'},
                      'german': GERMAN},
             'thumbar': THUMBAR}
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / 'translate.js'
        source.write_text(code, encoding='utf-8')
        out = json.loads(node(RUN, source, NATIVE_UTILS, json.dumps(cases, ensure_ascii=False)))
    check('find text in NativeUtils', out['find'], True)
    check('patch applied: setSystemTrayStrings', out['applied']['trayStrings'], True)
    check('patch applied: setThumbarButtons', out['applied']['thumbarButtons'], True)
    for key, value in EXPECTED_FR.items():
        check(f'tray (French Discord) {key}', out['results']['french'].get(key), value)
    for key, value in EXPECTED_EN.items():
        check(f'tray (English Discord) {key}', out['results']['english'].get(key), value)
    check('tray (Discord PTB) appName', out['results']['ptb']['appName'], 'Discord PTB')
    check('tray (Discord PTB) openApp', out['results']['ptb']['openApp'], 'Apre Discord PTB')
    check('tray (Discord PTB) quitApp', out['results']['ptb']['quitApp'], 'Esce da Discord PTB')
    check('tray (German Discord) left as it is', out['results']['german'], GERMAN)
    check('taskbar preview buttons', out['results']['thumbar'], THUMBAR_EXPECTED)
    check("the page's own object unchanged", out['untouched'], 'Ouvrir Discord')

    built = vencord / 'dist/renderer.js'
    text = built.read_text(encoding='utf-8') if built.is_file() else ''
    check('built bundle carries the tray patch', '$self.trayStrings($1);' in text and ',setSystemTrayApplications' in text, True)
    check('built bundle carries the taskbar patch', '$self.thumbarButtons($1);' in text, True)

    if arguments.discord_bundle:
        patterns = [r'setSystemTrayStrings\((\i)\)\{', r'setThumbarButtons\((\i)\)\{']
        scan = json.loads(node(SCAN, arguments.discord_bundle, ',setSystemTrayApplications', *patterns))
        check(f'{arguments.discord_bundle.name}: modules holding the find text', scan['modules'], 1)
        check(f'{arguments.discord_bundle.name}: matches of each pattern there', scan['counts'], [1, 1])

    if failures:
        print(f'FAIL: {len(failures)} check(s): {", ".join(failures)}')
        return 1
    print('PASS: the tray menu and taskbar preview texts Discord sends to its desktop app are translated '
          '(simulated calls of the patched NativeUtils functions, not the real Discord app).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
