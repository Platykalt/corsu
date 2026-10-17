#!/usr/bin/env python3
"""Start a translated Firefox headless in a throwaway profile and read real interface strings.

Usage: check_firefox.py FIREFOX_EXECUTABLE
Fails when a checked string is still English or French (or not the Corsican given): that catches a missing French
pack, a broken omni.ja, labels the lexicon no longer covers and .properties arguments (%S) the engine misses.
"""
import json
import pathlib
import socket
import subprocess
import sys
import tempfile
import time

# (resource, message id, attribute or None, English text, French text)
CHECKS = [
    ('browser/menubar.ftl', 'menu-file', 'label', 'File', 'Fichier'),
    ('browser/menubar.ftl', 'menu-tools', 'label', 'Tools', 'Outils'),
    ('browser/menubar.ftl', 'menu-help', 'label', 'Help', 'Aide'),
    ('browser/aboutSessionRestore.ftl', 'restore-page-error-title', None,
     'Sorry. We’re having trouble getting your pages back.', 'Désolé, nous ne parvenons pas à récupérer vos pages.'),
    ('browser/aboutSessionRestore.ftl', 'restore-page-try-again-button', 'label', 'Restore Session', 'Restaurer la session'),
    ('browser/genai.ftl', 'genai-menu-ask-generic-2', 'label', 'Ask an AI chatbot', 'Demander à un chatbot IA'),
    # A heading (Firefox View, sidebar), not the button "Apre l’unghjette" an imported Android row once gave it.
    ('browser/firefoxView.ftl', 'firefoxview-opentabs-nav', None, 'Open tabs', 'Onglets ouverts', 'Unghjette aperte'),
]

# Older interface text still lives in .properties files: (file, key, English, French). Mozilla writes their
# arguments %S and %1$S.
PROPERTIES = [
    ('chrome://devtools/locale/menus.properties', 'browserConsoleCmd.label', 'Browser Console', 'Console du navigateur'),
    ('chrome://devtools/locale/menus.properties', 'devtoolsRemoteDebugging.label', 'Remote Debugging', 'Débogage distant'),
    ('chrome://browser/locale/downloads/downloads.properties', 'fileDeleted', 'File deleted', 'Fichier supprimé'),
    ('chrome://browser/locale/downloads/downloads.properties', 'fileMovedOrMissing', 'File moved or missing',
     'Fichier déplacé ou manquant'),
    ('chrome://mozapps/locale/downloads/unknownContentType.properties', 'title', 'Opening %S', 'Ouverture de %S'),
]

SCRIPT = '''
const [checks, properties, done] = [arguments[0], arguments[1], arguments[arguments.length - 1]];
(async () => {
  const result = [];
  for (const [resource, id, attribute] of checks) {
    const l10n = new Localization([resource]);
    const [message] = await l10n.formatMessages([{id}]);
    let value = message ? message.value : null;
    if (message && attribute) value = (message.attributes || []).find(a => a.name === attribute)?.value ?? null;
    result.push(value);
  }
  for (const [url, key] of properties) {
    try { result.push(Services.strings.createBundle(url).GetStringFromName(key)); } catch (error) { result.push(null); }
  }
  done({values: result, locale: Services.locale.appLocaleAsBCP47});
})().catch(error => done({error: String(error)}));
'''


def receive(connection):
    length = b''
    while not length.endswith(b':'):
        chunk = connection.recv(1)
        if not chunk:
            raise EOFError('Marionette closed')
        length += chunk
    count = int(length[:-1])
    data = b''
    while len(data) < count:
        chunk = connection.recv(count - len(data))
        if not chunk:
            raise EOFError('Marionette closed')
        data += chunk
    return json.loads(data)


def main(executable):
    with tempfile.TemporaryDirectory(prefix='corsu-check-', ignore_cleanup_errors=True) as directory:
        profile = pathlib.Path(directory)
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1', 0))
            port = reserve.getsockname()[1]
        (profile / 'user.js').write_text(
            f'user_pref("marionette.port", {port});\nuser_pref("browser.shell.checkDefaultBrowser", false);\n'
            'user_pref("datareporting.policy.dataSubmissionEnabled", false);\n', encoding='utf-8')
        log = (profile / 'log').open('w', encoding='utf-8')
        process = subprocess.Popen([executable, '--headless', '--no-remote', '--profile', directory, '--marionette',
                                    '--remote-allow-system-access', 'about:blank'], stdout=log, stderr=log)
        connection = None
        try:
            deadline = time.monotonic() + 90
            while connection is None:
                try:
                    connection = socket.create_connection(('127.0.0.1', port), timeout=1)
                except OSError:
                    if process.poll() is not None or time.monotonic() > deadline:
                        log.flush()
                        raise RuntimeError('Firefox did not start:\n' + (profile / 'log').read_text(encoding='utf-8'))
                    time.sleep(0.3)
            connection.settimeout(60)
            receive(connection)
            counter = 0

            def command(name, params):
                nonlocal counter
                counter += 1
                data = json.dumps([0, counter, name, params]).encode()
                connection.sendall(str(len(data)).encode() + b':' + data)
                response = receive(connection)
                if response[2]:
                    raise RuntimeError(response[2])
                return response[3]

            command('WebDriver:NewSession', {'capabilities': {'alwaysMatch': {}}})
            command('Marionette:SetContext', {'value': 'chrome'})
            result = command('WebDriver:ExecuteAsyncScript', {
                'script': SCRIPT, 'args': [[check[:3] for check in CHECKS], [check[:2] for check in PROPERTIES]],
                'newSandbox': True,
                'sandbox': 'default', 'scriptTimeout': 30000})['value']
            if 'error' in result:
                raise RuntimeError(result['error'])
            failures = []
            expected = [(f'{resource} {identifier}{"." + attribute if attribute else ""}', english, french, corsican)
                        for resource, identifier, attribute, english, french, *corsican in CHECKS]
            expected += [(f'{url.rsplit("/", 1)[1]} {key}', english, french, [])
                         for url, key, english, french in PROPERTIES]
            for (label, english, french, corsican), value in zip(expected, result['values']):
                status = 'FAIL' if not value or value in (english, french) or (corsican and value != corsican[0]) \
                    else 'PASS'
                print(f'{status}: {label} = {value!r}')
                if status == 'FAIL':
                    failures.append(label)
            print(f'Interface locale: {result["locale"]}')
            if failures:
                raise SystemExit('Untranslated in the running Firefox: ' + ', '.join(failures))
        finally:
            if connection:
                connection.close()
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            log.close()


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors='replace')
    main(sys.argv[1])
