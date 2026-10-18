#!/usr/bin/env python3
"""The « Report a translation » page and a speakers' review set, in headless Chrome or Chromium.

Usage: check_report.py CHROME OUTPUT_DIR
Serves the window with its own server (src/app.py: the page, its files, every check and the window's key) answering a
sample state (window_screens.py), opens it as Corsu does (a ticket after '#'), goes to the report page, fills it in
as a person would (input events), and checks: the report shown, private paths and addresses replaced, buttons
disabled until the required fields are there, the prefilled GitHub issue opened only by the click (window.open is
recorded, nothing is loaded), no request to anything but the window's own address. Then opens a review set page
(review/sets/mc01-1.html) from the disk, answers three questions and reads its reply back with
tools/review_sets.py. Screenshots go to OUTPUT_DIR. HOME is a temporary folder and the browser profile is a
throwaway one: nothing of the person's own Corsu, browser or files is read or written.
"""
import base64
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import urllib.parse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'tools'))

FILL = r'''(() => {
  const type = (id, value) => { const node = document.getElementById(id); node.value = value; node.dispatchEvent(new Event("input", { bubbles: true })); };
  const select = document.getElementById("rp-app"); select.value = "discord"; select.dispatchEvent(new Event("change", { bubbles: true }));
  type("rp-version", "1.0.162");
  type("rp-seen", "Bio du serveur");
  type("rp-where", "Profil du serveur, titre de la section");
  type("rp-proposal", "Biugrafia di u servore");
  type("rp-notes", "Vu dans /home/ana/.config/discord ; ana@example.org");
  return true;
})()'''

STATE = r'''(() => ({
  text: document.getElementById("rp-text").value,
  issueDisabled: document.getElementById("rp-issue").disabled,
  replaced: !document.getElementById("rp-replaced").hidden,
  heading: document.querySelector("#report h1").textContent,
  visible: !document.getElementById("report").hidden,
  hostOnly: performance.getEntriesByType("resource").every(entry => new URL(entry.name).host === location.host),
  opened: window.__opened || null,
  overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
}))()'''

ANSWER = r'''(() => {
  const pick = (item, kind) => { const input = document.querySelector(`input[name="q-${item}"][value="${kind}"]`); input.checked = true; input.dispatchEvent(new Event("change", { bubbles: true })); };
  pick("01.01", "ok");
  pick("01.02", "other");
  const proposal = document.getElementById("q-01.02-proposal"); proposal.value = "Ghjucà inseme"; proposal.dispatchEvent(new Event("input", { bubbles: true }));
  const comment = document.getElementById("q-01.03-comment"); comment.value = "Ozzioni hè ghjustu"; comment.dispatchEvent(new Event("input", { bubbles: true }));
  window.__opened = null; window.open = (...args) => { window.__opened = args; return null; };
  document.getElementById("issue").click();
  return { reply: document.getElementById("reply").value, opened: window.__opened,
    hostOnly: performance.getEntriesByType("resource").length === 0 };
})()'''


def evaluate(devtools, session, expression):
    answer = devtools.call('Runtime.evaluate', {'expression': expression, 'returnByValue': True, 'awaitPromise': True},
                           session=session)
    if 'exceptionDetails' in answer:
        raise RuntimeError(json.dumps(answer['exceptionDetails'])[:500])
    return answer['result'].get('value')


def screenshot(devtools, session, path):
    data = devtools.call('Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': True}, session=session)['data']
    Path(path).write_bytes(base64.b64decode(data))
    print('saved', path)


def open_target(devtools, width, height, scheme, language=None):
    target = devtools.call('Target.createTarget', {'url': 'about:blank'})['targetId']
    session = devtools.call('Target.attachToTarget', {'targetId': target, 'flatten': True})['sessionId']
    devtools.call('Page.enable', session=session)
    devtools.call('Emulation.setDeviceMetricsOverride', {'width': width, 'height': height, 'deviceScaleFactor': 1,
                                                         'mobile': False}, session=session)
    devtools.call('Emulation.setEmulatedMedia', {'features': [{'name': 'prefers-color-scheme', 'value': scheme}]},
                  session=session)
    if language:
        devtools.call('Page.addScriptToEvaluateOnNewDocument', {'source':
                      f'try {{ localStorage.setItem("corsu-language", "{language}"); }} catch (e) {{}}'}, session=session)
    return target, session


def main(arguments):
    executable, output = arguments[0], Path(arguments[1])
    output.mkdir(parents=True, exist_ok=True)
    failures = []

    def check(condition, message):
        print(('PASS ' if condition else 'FAIL ') + message)
        if not condition:
            failures.append(message)

    with tempfile.TemporaryDirectory(prefix='corsu-report-') as temporary:
        os.environ['HOME'] = temporary
        os.environ['XDG_DATA_HOME'] = str(Path(temporary) / 'data')
        os.environ['XDG_CONFIG_HOME'] = str(Path(temporary) / 'config')
        import window_screens
        import review_sets
        holder = [window_screens.states()['active']]
        server = window_screens.serve(window_screens.APP, holder, temporary)
        process, devtools = window_screens.chrome(executable, Path(temporary) / 'profile', 16)
        try:
            scenes = [('report-fr-light', 'fr', 1040, 900, 'light'), ('report-co-dark', 'co', 1040, 900, 'dark'),
                      ('report-en-narrow', 'en', 420, 1400, 'light')]
            for name, language, width, height, scheme in scenes:
                target, session = open_target(devtools, width, height, scheme, language)
                try:
                    devtools.call('Page.navigate', {'url': server.opening()}, session=session)
                    time.sleep(1.5)
                    evaluate(devtools, session, 'document.querySelector(\'[data-page="report"]\').click()')
                    time.sleep(0.5)
                    before = evaluate(devtools, session, STATE)
                    check(before['visible'] and before['issueDisabled'], f'{name}: page shown, issue button disabled while empty')
                    evaluate(devtools, session, FILL)
                    time.sleep(2)  # past one refresh of the window (1.5 s): what was typed stays
                    after = evaluate(devtools, session, STATE)
                    check(not after['issueDisabled'], f'{name}: issue button enabled once filled in')
                    check('Bio du serveur' in after['text'] and 'Biugrafia di u servore' in after['text'],
                          f'{name}: report shows the text and the proposal')
                    check('ana' not in after['text'] and after['replaced'], f'{name}: path and address replaced, and said')
                    check(after['opened'] is None, f'{name}: nothing opened before the click')
                    check(after['hostOnly'], f'{name}: no request outside the window address')
                    check(not after['overflow'], f'{name}: no horizontal scrolling')
                    screenshot(devtools, session, output / f'{name}.png')
                    evaluate(devtools, session, 'window.open = (...args) => { window.__opened = args; return null; }; '
                                                'document.getElementById("rp-issue").click(); true')
                    opened = evaluate(devtools, session, STATE)['opened']
                    url = opened[0] if opened else ''
                    fields = dict(urllib.parse.parse_qsl(url.split('?', 1)[1])) if '?' in url else {}
                    check(url.startswith('https://github.com/Platykalt/corsu/issues/new?') and fields.get('template') == 'translation.yml'
                          and fields.get('app') == 'Discord' and fields.get('seen') == 'Bio du serveur'
                          and 'ana' not in url, f'{name}: prefilled issue on the click ({len(url)} characters)')
                finally:
                    devtools.call('Target.closeTarget', {'targetId': target})

            for name, scheme, width in (('review-set-light', 'light', 1000), ('review-set-dark-narrow', 'dark', 420)):
                target, session = open_target(devtools, width, 1600, scheme)
                try:
                    devtools.call('Page.navigate', {'url': (ROOT / 'review/sets/mc01-1.html').as_uri()}, session=session)
                    time.sleep(1)
                    result = evaluate(devtools, session, ANSWER)
                    answers = review_sets.parse_reply(result['reply'])
                    found = [(answer['item'], answer['answer'], answer['proposal'], answer['comment']) for answer in answers
                             if answer['answer'] != 'skip' or answer['comment']]
                    check(found == [('01.01', 'ok', None, None), ('01.02', 'other', 'Ghjucà inseme', None),
                                    ('01.03', 'skip', None, 'Ozzioni hè ghjustu')], f'{name}: reply read back by review_sets.py')
                    check(answers[0]['texts'][0]['source_hash'] == 'e28ffad47afc', f'{name}: reply carries the source hash')
                    opened = result['opened'] or ['']
                    check(opened[0].startswith('https://github.com/Platykalt/corsu/issues/new?') and 'Ghjuc' in urllib.parse.unquote_plus(opened[0]),
                          f'{name}: issue prefilled with the reply on the click')
                    check(result['hostOnly'], f'{name}: the page loads nothing')
                    devtools.call('Runtime.evaluate', {'expression': 'window.scrollTo(0, 0)'}, session=session)
                    screenshot(devtools, session, output / f'{name}.png')
                finally:
                    devtools.call('Target.closeTarget', {'targetId': target})
        finally:
            process.terminate()
            process.wait(timeout=20)
            server.shutdown()
    print(f'{len(failures)} failure(s)')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
