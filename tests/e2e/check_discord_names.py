#!/usr/bin/env python3
"""The Discord plugin's translator in a real browser page: people's names stay as they wrote them.

Usage: check_discord_names.py CHROME [VENCORD_DIR]
Bundles src/discord-plugin/translate.ts with Vencord's esbuild (a small test dictionary replaces the generated one),
loads it in Chrome headless, builds pages the way Discord renders them (React keeps each component's props on its DOM
nodes, under __reactFiber$…), and checks: friends named "Work" and "Error" keep their names while the same words are
translated as interface labels; a name inside a translated sentence or label is kept; mentions in messages are left
alone and still clickable; search fields (an <input> placeholder and label, the placeholder Slate draws inside an empty
editor, a placeholder beside the editor) are translated with the conversation or server name Discord inserts kept as
written ("Rechercher EnzoParisi, Moz_One"), while what is typed and fields inside messages stay; and all of it still
holds after the page changes conversation.
"""
import json
import os
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

DICTIONARY = {
    'Work': 'Travagliu', 'Error': 'Sbagliu', 'Online': 'In linea', 'Friends': 'Amichi',
    '\u00001\u0000 is typing a message…': '\u00001\u0000 scrive un messaghju…',
    'Send a message to @\u00001\u0000': 'Mandà un messaghju à @\u00001\u0000',
    'Rechercher': 'Circà', 'Rechercher \u00001\u0000': 'Circà \u00001\u0000',
}

PAGE = r'''
const user = (id, username, globalName) => ({ id, username, globalName });
const work = user("111111111111111111", "work.home", "Work"), error = user("222222222222222222", "err", "Error");
// What React leaves on a host node: the fiber, whose memoizedProps and .return chain hold the component props.
function fiber(element, ...chain) {
  let parent = null;
  for (const props of chain.reverse()) parent = { memoizedProps: props, return: parent };
  element.__reactFiber$test = { memoizedProps: { children: element.textContent }, return: parent };
}
document.body.innerHTML = `
  <div class="peopleList"><div class="row"><span id="friend1">Work</span></div>
    <div class="row"><span id="friend2">Error</span></div></div>
  <h2 id="label1">Error</h2><button id="label2">Work</button><div id="tab">Friends</div>
  <div id="dm" aria-label="Work, Online"></div>
  <div id="typing">Work is typing a message…</div><div id="typingSystem">Error is typing a message…</div>
  <div class="composer"><div id="draft" class="placeholder_x">Send a message to @Work</div><div contenteditable="true"></div></div>
  <div id="message-content-1">Hello <span id="mention" class="mention" role="button" data-user-id="111111111111111111">@Work</span></div>
  <div id="profile"><span id="nick">Error</span><div id="bio" class="bio_x">Work</div></div>
  <div class="peopleColumn"><input id="friendSearch" class="input_x" placeholder="Rechercher" aria-label="Rechercher"></div>
  <div class="toolbar_x"><div class="search_x">
    <div id="dmSearch" class="editor_x" role="combobox" contenteditable="true" aria-label="Rechercher EnzoParisi, Moz_One"><div data-slate-node="element"><span data-slate-node="text"><span data-slate-leaf="true"><span id="slatePlaceholder" data-slate-placeholder="true" contenteditable="false">Rechercher EnzoParisi, Moz_One</span><span data-slate-zero-width="n">\ufeff<br></span></span></span></div></div>
    <div class="public-DraftEditorPlaceholder-root"><div id="draftPlaceholder" class="public-DraftEditorPlaceholder-inner">Rechercher Work</div></div>
    <input id="guildSearch" placeholder="Rechercher Mon Serveur" aria-label="Rechercher Mon Serveur"></div></div>
  <div id="typedEditor" contenteditable="true"><span data-slate-string="true" id="typed">Rechercher Work</span></div>
  <div id="message-content-2"><input id="messageField" placeholder="Rechercher"></div>`;
fiber(document.getElementById("friend1"), { user: work }, { friend: work });
fiber(document.getElementById("friend2"), { user: error });
fiber(document.getElementById("label2"), { onClick: () => 0, look: "filled" });
fiber(document.getElementById("dm"), { channel: { id: "333333333333333333", name: "", recipients: [work] } });
fiber(document.getElementById("typing"), { users: [work] });
fiber(document.getElementById("draft"), { channel: { id: "333333333333333333", recipients: [work] } });
fiber(document.getElementById("nick"), { member: { id: "222222222222222222", nick: "Error" } });
// A group DM: Discord composes "EnzoParisi, Moz_One" from its members; no record holds that text as such.
fiber(document.getElementById("slatePlaceholder"), { channel: { id: "555555555555555555", type: 3, name: "",
  recipients: ["666666666666666666", "777777777777777777"] } });
window.clicks = 0;
document.getElementById("mention").addEventListener("click", () => window.clicks++);
window.mentionNode = document.getElementById("mention");
window.translator = Corsu.createTranslator(document);
window.translator.start();
'''

CHANGE = r'''
// Another conversation: React reuses the nodes, gives them new text and new props.
const friend = document.getElementById("friend1");
friend.__reactFiber$test.return.memoizedProps = { user: { id: "444444444444444444", username: "x", globalName: "Online" } };
friend.firstChild.data = "Online";
const label = document.getElementById("label1");
label.firstChild.data = "Work";
// Another conversation: the field gets a new placeholder, Slate draws a new placeholder span.
document.getElementById("guildSearch").setAttribute("placeholder", "Rechercher Error");
const leaf = document.getElementById("slatePlaceholder").parentNode;
document.getElementById("slatePlaceholder").remove();
const span = document.createElement("span");
span.id = "slatePlaceholder";
span.setAttribute("data-slate-placeholder", "true");
span.setAttribute("contenteditable", "false");
span.textContent = "Rechercher Work, Error";
leaf.prepend(span);
'''

READ = r'''
JSON.stringify({
  friend1: document.getElementById("friend1").textContent, friend2: document.getElementById("friend2").textContent,
  label1: document.getElementById("label1").textContent, label2: document.getElementById("label2").textContent,
  tab: document.getElementById("tab").textContent, dm: document.getElementById("dm").getAttribute("aria-label"),
  typing: document.getElementById("typing").textContent, typingSystem: document.getElementById("typingSystem").textContent,
  draft: document.getElementById("draft").textContent,
  message: document.getElementById("message-content-1").textContent, nick: document.getElementById("nick").textContent,
  bio: document.getElementById("bio").textContent,
  friendSearch: document.getElementById("friendSearch").placeholder,
  friendSearchLabel: document.getElementById("friendSearch").getAttribute("aria-label"),
  dmSearchLabel: document.getElementById("dmSearch").getAttribute("aria-label"),
  slatePlaceholder: document.getElementById("slatePlaceholder").textContent,
  draftPlaceholder: document.getElementById("draftPlaceholder").textContent,
  guildSearch: document.getElementById("guildSearch").placeholder,
  typed: document.getElementById("typed").textContent,
  messageField: document.getElementById("messageField").placeholder,
  mentionSame: document.getElementById("mention") === window.mentionNode,
  mentionId: document.getElementById("mention").dataset.userId,
  clicks: (document.getElementById("mention").click(), window.clicks)
})
'''

EXPECTED = {
    'friend1': 'Work', 'friend2': 'Error',                  # friends' names, though "Work" and "Error" are dictionary words
    'label1': 'Sbagliu', 'label2': 'Travagliu', 'tab': 'Amichi',  # the same words as interface labels
    'dm': 'Work, In linea',                                  # a label made of a name and interface text
    'typing': 'Work scrive un messaghju…', 'typingSystem': 'Error scrive un messaghju…',  # names inserted in a translated sentence
    'draft': 'Mandà un messaghju à @Work',
    'message': 'Hello @Work', 'bio': 'Work',                 # what people write is never translated
    'nick': 'Error',                                         # a server nickname
    'mentionSame': True, 'mentionId': '111111111111111111', 'clicks': 1,
    # Search fields: "Rechercher" on the Friends page (an <input>, never reached before), the placeholder over a group
    # DM (in a Slate editor, beside a Draft one, or the field's label) and over a server, names inserted as written.
    'friendSearch': 'Circà', 'friendSearchLabel': 'Circà',
    'dmSearchLabel': 'Circà EnzoParisi, Moz_One', 'slatePlaceholder': 'Circà EnzoParisi, Moz_One',
    'draftPlaceholder': 'Circà Work', 'guildSearch': 'Circà Mon Serveur',
    'typed': 'Rechercher Work', 'messageField': 'Rechercher',  # what is typed, and a field inside a message
}
AFTER_CHANGE = {**EXPECTED, 'friend1': 'Online', 'label1': 'Travagliu', 'clicks': 2,
                'guildSearch': 'Circà Error', 'slatePlaceholder': 'Circà Work, Error'}


def bundle(vencord, dictionary_words=None):
    script = """
const { build } = require(process.argv[1]);
build({ entryPoints: [process.argv[2]], bundle: true, write: false, format: 'iife', globalName: 'Corsu',
        platform: 'browser', target: 'es2022', logLevel: 'error',
        plugins: [{ name: 'dictionary', setup(b) {
            b.onResolve({ filter: /dictionary\\.json$/ }, () => ({ path: process.argv[3] })); } }] })
  .then(result => process.stdout.write(result.outputFiles[0].text));
"""
    with tempfile.TemporaryDirectory() as folder:
        dictionary = Path(folder) / 'dictionary.json'
        dictionary.write_text(json.dumps(dictionary_words or DICTIONARY, ensure_ascii=False), encoding='utf-8')
        esbuild = next(Path(vencord, 'node_modules').resolve().glob('esbuild/lib/main.js'))
        result = subprocess.run(['node', '-e', script, str(esbuild), str(ROOT / 'src/discord-plugin/translate.ts'),
                                 str(dictionary)], capture_output=True, text=True, encoding='utf-8')
        if result.returncode:
            raise SystemExit('esbuild could not bundle translate.ts:\n' + result.stderr)
        return result.stdout


def evaluate(devtools, session, expression):
    result = devtools.call('Runtime.evaluate', {'expression': expression, 'returnByValue': True,
                                                'awaitPromise': True}, session=session)
    if 'exceptionDetails' in result:
        raise SystemExit(f'page error: {result["exceptionDetails"]}')
    return result['result'].get('value')


def compare(label, found, expected):
    wrong = {key: (found.get(key), value) for key, value in expected.items() if found.get(key) != value}
    for key, value in expected.items():
        print(f'{"PASS" if key not in wrong else "FAIL"}: {label} {key} = {found.get(key)!r}')
    return wrong


def run(chrome, vencord, dictionary, page, read, expected, change, after_change):
    """Load the bundled translator and `page` in Chrome headless, read the page, apply `change`, read it again.
    Returns the values that differ from what was expected."""
    code = bundle(vencord, dictionary)
    with tempfile.TemporaryDirectory(prefix='corsu-discord-', ignore_cleanup_errors=True) as profile:
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1', 0))
            port = reserve.getsockname()[1]
        command = [chrome, '--headless=new', '--disable-gpu', f'--user-data-dir={profile}',
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
            target = devtools.call('Target.createTarget', {'url': 'about:blank'})['targetId']
            session = devtools.call('Target.attachToTarget', {'targetId': target, 'flatten': True})['sessionId']
            evaluate(devtools, session, code)
            evaluate(devtools, session, page)
            wrong = compare('start:', json.loads(evaluate(devtools, session, read)), expected)
            evaluate(devtools, session, change)
            # The observer translates in a microtask; give it one turn.
            evaluate(devtools, session, 'new Promise(resolve => setTimeout(resolve, 50))')
            wrong.update({f'after change {key}': value for key, value in
                          compare('after change:', json.loads(evaluate(devtools, session, read)), after_change).items()})
        finally:
            process.terminate()
            process.wait(timeout=15)
    return wrong


def main(chrome, vencord):
    wrong = run(chrome, vencord, DICTIONARY, PAGE, READ, EXPECTED, CHANGE, AFTER_CHANGE)
    # The pages built on Discord's own record shapes and markup (check_discord_content.py) run here too, so the CI
    # job that runs this file checks them.
    import check_discord_content as content
    wrong.update({f'content {key}': value for key, value in content.run_all(chrome, vencord).items()})
    if wrong:
        raise SystemExit(f'FAIL: {wrong}')
    print('PASS: names stay as people wrote them; interface labels around them are translated')


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding='utf-8', errors='replace')
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else str(ROOT / 'Vencord'))
