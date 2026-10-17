#!/usr/bin/env python3
"""The BUILT Discord plugin (Vencord's dist/renderer.js) with the REAL generated dictionary, in headless Chrome.

Usage: check_discord_built.py CHROME [VENCORD_DIR] [--strict]
The other Discord checks bundle src/discord-plugin/translate.ts with a small test dictionary. This one takes the
translator out of the bundle Discord actually loads (VENCORD_DIR/dist/renderer.js, built by installer.prepare_build
after corsu.generate()), with the dictionary embedded in it, and checks:
- the bundle: the translator revision, the dictionary fingerprint the diagnostic reports (it must equal the one computed
  from VENCORD_DIR/src/userplugins/corsu/dictionary.json), "Bio" kept as "Bio" (no "Organicu" anywhere);
- simulated pages (the markup and React props of Discord's web client, as in check_discord_activity.py): the activity
  line in the direct message list and the Friends tab, games, rich presence and custom statuses equal to dictionary
  words, names, server, channel and role names, a label mixing a name, long, emoji, right-to-left and separator names,
  the profile's "Bio" heading and the bio itself, repeated passes and a second translator over a translated page;
- the hidden diagnostic: what it prints for synthetic personal data.
Known limits (left as they are on this branch) are printed as KNOWN and only fail with --strict.
This is a simulated page, not an observation of the real Discord app.
"""
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
from check_chromium import DevTools  # noqa: E402
from check_discord_content import HELPERS  # noqa: E402
from check_discord_names import evaluate  # noqa: E402
from check_discord_activity import fingerprint  # noqa: E402

# Takes the Corsu module out of the minified bundle: from the dictionary literal (found by one of its entries) to the
# plugin's settings, and finds the minified names of its functions from the plugin's start() and their own code.
EXTRACT = r"""
const fs = require("fs");
const s = fs.readFileSync(process.argv[1], "utf8");
const start = s.lastIndexOf("var ", s.indexOf('"Dans un appel":'));
const end = s.search(/var \w+=\w+\(\{showOriginal:/);
if (start < 0 || end < start) throw new Error("Corsu module not found in the bundle");
const body = s.slice(start, end), plugin = s.slice(end, s.indexOf("permanent:", end));
const pick = (text, pattern) => (text.match(pattern) || [])[1];
const names = {
  createTranslator: pick(plugin, /=(\w+)\(document,\{showOriginal/),
  setCorrections: pick(plugin, /try\{(\w+)\(JSON\.parse/),
  dictionaryFingerprint: pick(plugin, /dictionary:(\w+)\(\)/),
  revision: pick(plugin, /revision:(\w+),dictionary/),
  translateLabel: pick(body, /function (\w+)\(e,i=new Set\)\{let a=e\.match/),
};
for (const [key, value] of Object.entries(names)) if (!value) throw new Error("not found in the bundle: " + key);
const exported = Object.entries(names).map(([key, value]) => `${key}:${value}`).join(",");
fs.writeFileSync(process.argv[2], `(function(){${body}\nwindow.CorsuBuilt={${exported}};})();\n`);
"""

CASES = HELPERS + r'''
window.cases = [];
const ID = n => String(n).repeat(18).slice(0, 18);
const user = (n, g) => ({ id: ID(n), username: "u" + n, globalName: g });
const work = user(1, "Work"), error = user(2, "Error"), paris = user(3, "Paris"), sep = user(4, "Paul | Work"),
      longName = user(5, "Work ".repeat(70).trim()), emoji = user(6, "🔥🔥"), rtl = user(7, "محمد Work");
const dm = p => ({ id: "9" + p.id.slice(1), type: 1, name: "", recipients: [p.id],
  rawRecipients: [{ id: p.id, username: p.username, global_name: p.globalName }], nicks: {} });
const status = (p, activities, voiceChannel = null) => ({ user: p, activities, voiceChannel, applicationStream: null });
const row = (p, activities) => ({ user: p, activities, applicationStream: null, status: "online" });
const game = name => ({ type: 0, name, application_id: "999999999999999999" });
const custom = state => ({ type: 4, name: "Custom Status", state, emoji: null });
// strict: false marks a known limit of this branch (expected = what should happen).
function add(name, html, chain, expected, attr, strict = true) { cases.push({ name, html, chain, expected, attr, strict }); }
const subtext = inner => `<div class="userInfo__0a06e"><div class="subtext__0a06e"><div class="container_c9d15c">${inner}</div></div></div>`;
const dmLine = inner => `<a class="link__972a0 channelNameFade__972a0" href="/channels/@me/1"><div class="subText__20a53">${inner}</div></a>`;
const card = inner => `<div class="userProfile_x"><div class="activityCard_x">${inner}</div></div>`;

add("DM list call label", dmLine(`<div id="t" class="activityStatusText__972a0">Dans un appel</div>`),
  [{ variant: "x" }, { text: "Dans un appel" }, { channel: dm(work) }, status(work, [], dm(work)),
   { channel: dm(work), user: work, activities: [], voiceChannel: dm(work) }], "In una chjama");
add("DM list call aria-label", dmLine(`<div id="t" class="textWithIconContainer_c9d15c" aria-label="Dans un appel (Work)"></div>`),
  [{ text: "Dans un appel", "aria-label": "Dans un appel (Work)" }, { channel: dm(work) }, status(work, [], dm(work))],
  "In una chjama (Work)", "aria-label");
add("DM list call aria-label, name with separator", dmLine(`<div id="t" class="textWithIconContainer_c9d15c" aria-label="Dans un appel (Paul | Work)"></div>`),
  [{ text: "Dans un appel" }, { channel: dm(sep) }, status(sep, [], dm(sep))], "In una chjama (Paul | Work)", "aria-label");
add("Friends tab call label", subtext(`<div id="t" class="statusText__19b6d">Dans un appel</div>`),
  [{ variant: "x" }, { text: "Dans un appel" }, { channel: dm(work) }, status(error, [], dm(work)), row(error, [])], "In una chjama");
for (const name of ["Work", "Control", "Terminal", "Paris", "Dans un appel", "Bio"]) {
  const playing = [game(name)];
  add("game " + name, subtext(`<div id="t" class="statusText__19b6d">${name}</div>`),
    [{ variant: "x" }, { text: name }, { activity: playing[0] }, status(work, playing), row(work, playing)], name);
  add("game aria-label " + name, subtext(`<div id="t" class="textWithIconContainer_c9d15c" aria-label="Joue à ${name}"></div>`),
    [{ text: name, "aria-label": "Joue à " + name }, { activity: playing[0] }, status(work, playing), row(work, playing)],
    "Ghjoca à " + name, "aria-label");
}
for (const text of ["Dans un appel", "Work", "Bio", "En ligne", "Ne pas déranger", "Envoyer", "Créer un salon", "Joue à Work"]) {
  const typed = [custom(text)];
  add("custom status (Friends) " + text, subtext(`<div id="t" class="statusText__19b6d">${text}</div>`),
    [{ variant: "x" }, { customStatusActivity: typed[0] }, status(error, typed), row(error, typed)], text);
  add("custom status (DM list) " + text, dmLine(`<div id="t" class="activityStatusText__972a0">${text}</div>`),
    [{ variant: "x" }, { customStatusActivity: typed[0] }, status(error, typed), { channel: dm(error), user: error, activities: typed }], text);
}
{
  const typed = [{ ...custom("Dans un appel"), emoji: { name: "🔥" } }];
  add("custom status after its emoji", subtext(`<div class="statusText__19b6d"><img alt="🔥"><span id="t"> Dans un appel</span></div>`),
    [{ children: " Dans un appel" }, { customStatusActivity: typed[0] }, status(error, typed), row(error, typed)], " Dans un appel");
}
{
  const presence = { type: 0, name: "Control", details: "Work", state: "Dans un appel", party: { size: [1, 4] },
    assets: { large_text: "Paris", small_text: "Bio" }, buttons: ["Envoyer"] };
  const props = [{ activity: presence, user: work }];
  add("rich presence name", card(`<div id="t" class="activityName_x">Control</div>`), props, "Control");
  add("rich presence details", card(`<div id="t" class="details_x">Work</div>`), props, "Work");
  add("rich presence state", card(`<div id="t" class="state_x">Dans un appel</div>`), props, "Dans un appel");
  add("rich presence image text", card(`<div id="t" class="assets_x" aria-label="Paris"></div>`), props, "Paris", "aria-label");
  add("rich presence button", card(`<button id="t">Envoyer</button>`), props, "Envoyer");
  add("rich presence details in an activity-classed header", card(`<h3 id="t" class="activityHeader_x">Work</h3>`), props, "Work");
  add("activity card label around the game", card(`<h3 id="t" class="activityHeader_x">Joue à Control</h3>`), props, "Ghjoca à Control");
  // A value from the records with text added by Discord (the party size): the template "Dans un appel ({1})" must not
  // take it (it did in Corsu 0.23.0).
  add("rich presence state with party size", card(`<div id="t" class="state_x">Dans un appel (1 sur 4)</div>`), props,
    "Dans un appel (1 sur 4)");
}
// KNOWN (also in 0.23.0): a game shown under another name than its record's (the application's name).
add("game shown under another name than its record", subtext(`<div id="t" class="statusText__19b6d">Control</div>`),
  [{ variant: "x" }, { activity: game("control.exe") }, status(work, [game("control.exe")]), row(work, [game("control.exe")])],
  "Control", undefined, false);
add("friend named Work", `<div class="discordTag__0a06e"><span id="t" class="username__0a06e">Work</span></div>`, [{ user: work }, row(work, [])], "Work");
add("friend named Error", `<div class="discordTag__0a06e"><span id="t" class="username__0a06e">Error</span></div>`, [{ user: error }, row(error, [])], "Error");
add("channel named General", `<a id="t" href="/channels/4/5">General</a>`, [{ channel: { id: ID(5), name: "General", guild_id: ID(4) } }], "General");
add("role named Moderator", `<span id="t" class="roleName_x">Moderator</span>`, [{ role: { id: ID(6), name: "Moderator" } }], "Moderator");
add("server named Paris in a tooltip", `<div id="t" class="tooltip_x">Paris</div>`, [{ guild: { id: ID(4), name: "Paris" } }], "Paris");
add("label and name", `<div id="t" class="title_x">Dans un appel, Work</div>`, [{ user: work, voiceChannel: dm(work) }], "In una chjama, Work");
add("aria-label holding a name", `<div id="t" aria-label="Work"></div>`, [{ user: work }], "Work", "aria-label");
add("title holding a name", `<div id="t" title="Error"></div>`, [{ user: error }], "Error", "title");
add("very long name in a label", `<div id="t" aria-label="Dans un appel (${longName.globalName})"></div>`,
  [{ user: longName, voiceChannel: dm(longName) }], `In una chjama (${longName.globalName})`, "aria-label");
add("very long name", `<div id="t" class="username_x">${longName.globalName}</div>`, [{ user: longName }], longName.globalName);
add("emoji name in a label", `<div id="t" aria-label="Dans un appel (🔥🔥)"></div>`, [{ user: emoji, voiceChannel: dm(emoji) }], "In una chjama (🔥🔥)", "aria-label");
add("right-to-left name in a label", `<div id="t" aria-label="Dans un appel (محمد Work)"></div>`, [{ user: rtl, voiceChannel: dm(rtl) }], "In una chjama (محمد Work)", "aria-label");
add("game named like a template", subtext(`<div id="t" class="statusText__19b6d">Bobby de Paris</div>`),
  [{ variant: "x" }, { activity: game("Bobby de Paris") }, status(paris, [game("Bobby de Paris")])], "Bobby de Paris");
add("profile Bio heading", `<div class="userProfile_x"><h2 id="t" class="defaultColor_x">Bio</h2></div>`, [{ user: work }], "Bio");
add("bio text Bio", `<div class="userBio_x"><div id="t" class="markup_x">Bio</div></div>`, [{ user: work }], "Bio");
add("bio text Dans un appel", `<div class="bio_x"><span id="t">Dans un appel</span></div>`, [{ user: work }], "Dans un appel");
add("Créer un salon", `<button id="t">Créer un salon</button>`, [], "Creà un canale");
add("message", `<div id="message-content-1" class="markup_x"><span id="t">Dans un appel</span></div>`, [], "Dans un appel");

for (const c of cases) {
  const host = document.createElement("div");
  host.innerHTML = c.html;
  document.body.append(host);
  c.element = host.querySelector("#t");
  c.element.removeAttribute("id");
  if (c.chain.length) mount(c.element, ...c.chain);
}
'''

RUN = r'''
(async () => {
const settle = () => new Promise(resolve => setTimeout(resolve, 30));
const read = c => c.attr ? c.element.getAttribute(c.attr) : c.element.textContent;
window.translator = CorsuBuilt.createTranslator(document);
translator.start();
await settle();
const first = cases.map(read);
// The page writes back what it shows, three times; then a second translator (fresh memory) reads the translated page.
for (let pass = 0; pass < 3; pass++) {
  for (const c of cases) {
    if (c.attr) c.element.setAttribute(c.attr, c.element.getAttribute(c.attr));
    else for (const node of c.element.childNodes) if (node.nodeType === Node.TEXT_NODE) node.data = node.data;
  }
  await settle();
}
const second = CorsuBuilt.createTranslator(document);
second.start();
await settle();
second.stop();
return JSON.stringify(cases.map((c, index) => ({ name: c.name, expected: c.expected, strict: c.strict, first: first[index], last: read(c) })));
})()
'''

# The diagnostic with synthetic personal data in places Discord shows what people chose without a name class or
# React records nearby. Nothing of it should be printed.
PRIVACY = HELPERS + r'''
(async () => {
const bob = { id: "111111111111111111", username: "bob.prive", globalName: "Bobette Secretnom" };
document.body.innerHTML = `
  <div class="connectedAccountNameText_x">Jérôme Martindale</div>
  <div class="pronouns_x">elle/la sienne</div>
  <div class="voiceChannelStatus_x">On joue à des jeux de la nuit</div>
  <div class="channel_x"><span class="username_x">Paris</span></div>
  <div class="subText_x"><div class="activityStatusText_x">En route pour Ajaccio avec Léa</div></div>
  <div id="emoji" aria-label=":chat_de_Mélanie:"></div>
  <div class="userBio_x"><div class="markup_x">Ma bio très privée</div></div>
  <div id="message-content-9" class="markup_x">Message ultra secret de Bobette</div>
  <div id="withRecords">Appel avec Bobette Secretnom en cours</div>`;
mount(document.getElementById("withRecords"), { user: bob });
const translator = CorsuBuilt.createTranslator(document);
translator.start();
await new Promise(resolve => setTimeout(resolve, 30));
const fresh = document.createElement("div");
fresh.textContent = "Jérôme Martindale, Envoyer";
document.body.append(fresh);
const output = JSON.stringify(translator.report());
return JSON.stringify(["Jérôme", "Martindale", "elle/la sienne", "nuit", "Paris", "Ajaccio", "Léa", "Mélanie", "bio très",
  "secret", "Bobette", "Secretnom", "bob.prive"].filter(word => output.includes(word)));
})()
'''


def extract(vencord, folder):
    bundle = Path(vencord, 'dist/renderer.js')
    script = Path(folder, 'translator.js')
    result = subprocess.run(['node', '-e', EXTRACT, str(bundle), str(script)], capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(f'FAIL: could not take the translator out of {bundle}:\n{result.stderr}')
    page = Path(folder, 'page.html')
    page.write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><body><script src="translator.js"></script>',
                    encoding='utf-8')
    return bundle.read_text(encoding='utf-8'), page.as_uri()


def main(chrome, vencord, strict):
    failures, known = [], []
    dictionary = json.loads(Path(vencord, 'src/userplugins/corsu/dictionary.json').read_text(encoding='utf-8'))
    expected_fingerprint = fingerprint(dictionary)
    with tempfile.TemporaryDirectory(prefix='corsu-built-', ignore_cleanup_errors=True) as folder:
        bundle, url = extract(vencord, folder)
        checks = {'"Bio" is "Bio" in the dictionary': dictionary.get('Bio') == 'Bio',
                  'no "Organicu" in the bundle': 'Organicu' not in bundle,
                  'bundle has Bio:"Bio"': 'Bio:"Bio"' in bundle}
        for name, ok in checks.items():
            print(f'{"PASS" if ok else "FAIL"}: {name}')
            if not ok:
                failures.append(name)
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1', 0))
            port = reserve.getsockname()[1]
        command = [chrome, '--headless=new', '--disable-gpu', f'--user-data-dir={folder}/profile',
                   f'--remote-debugging-port={port}', '--no-first-run', 'about:blank']
        if sys.platform.startswith('linux'):
            command.insert(1, '--no-sandbox')
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(120):
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/version', timeout=2) as response:
                        endpoint = json.load(response)['webSocketDebuggerUrl']
                    break
                except OSError:
                    time.sleep(0.5)
            devtools = DevTools(endpoint)

            def page():
                target = devtools.call('Target.createTarget', {'url': url})['targetId']
                session = devtools.call('Target.attachToTarget', {'targetId': target, 'flatten': True})['sessionId']
                for _ in range(200):
                    if evaluate(devtools, session, 'Boolean(window.CorsuBuilt)'):
                        return session
                    time.sleep(0.2)
                raise SystemExit('FAIL: the built translator did not load')

            session = page()
            loaded = json.loads(evaluate(devtools, session, 'JSON.stringify({revision: CorsuBuilt.revision, '
                                                            'dictionary: CorsuBuilt.dictionaryFingerprint()})'))
            print(f'built plugin: revision {loaded["revision"]}, dictionary {loaded["dictionary"]} '
                  f'(dictionary.json: {expected_fingerprint})')
            if loaded['dictionary'] != expected_fingerprint:
                failures.append('fingerprint')
            evaluate(devtools, session, CASES)
            for case in json.loads(evaluate(devtools, session, RUN)):
                ok = case['first'] == case['expected'] and case['last'] == case['first']
                tag = 'PASS' if ok else ('FAIL' if case['strict'] else 'KNOWN')
                print(f'{tag}: {case["name"]} = {case["first"]!r}' + ('' if case['last'] == case['first'] else
                                                                      f' then {case["last"]!r}')
                      + ('' if ok else f' (expected {case["expected"]!r})'))
                if not ok:
                    (failures if case['strict'] else known).append(case['name'])
            leaked = json.loads(evaluate(devtools, page(), PRIVACY))
            print(f'{"PASS" if not leaked else "FAIL"}: diagnostic prints none of the synthetic personal data'
                  + (f' (printed: {leaked})' if leaked else ''))
            if leaked:
                failures.append('diagnostic privacy')
        finally:
            process.terminate()
            process.wait(timeout=15)
    if failures or (strict and known):
        raise SystemExit(f'FAIL: {failures + (known if strict else [])}')
    print(f'PASS: the built plugin keeps names and activities and translates Discord\'s labels'
          + (f' ({len(known)} known limits)' if known else ''))


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding='utf-8', errors='replace')
    arguments = [argument for argument in sys.argv[1:] if argument != '--strict']
    main(arguments[0], arguments[1] if len(arguments) > 1 else str(ROOT / 'Vencord'), '--strict' in sys.argv)
