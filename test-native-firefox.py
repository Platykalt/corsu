"""Read only public browser UI labels in an isolated headless test profile."""
import json
import pathlib
import socket
import subprocess
import sys
import tempfile
import time


with tempfile.TemporaryDirectory(prefix='corsu-native-') as directory:
    profile = pathlib.Path(directory)
    with socket.socket() as reserve:
        reserve.bind(('127.0.0.1', 0))
        port = reserve.getsockname()[1]
    (profile / 'user.js').write_text(f'user_pref("marionette.port", {port});\nuser_pref("browser.shell.checkDefaultBrowser", false);\n')
    with (profile / 'log').open('w') as log:
        process = subprocess.Popen([sys.argv[1], '--headless', '--no-remote', '--profile', directory,
                                    '--marionette', '--remote-allow-system-access', 'about:blank'], stdout=log, stderr=log)
        connection = None
        try:
            deadline = time.monotonic() + 40
            while time.monotonic() < deadline:
                try:
                    connection = socket.create_connection(('127.0.0.1', port), timeout=1)
                    break
                except OSError:
                    if process.poll() is not None:
                        raise RuntimeError((profile / 'log').read_text())
                    time.sleep(0.2)
            if connection is None:
                raise TimeoutError('Marionette did not start')
            connection.settimeout(20)
            def receive():
                length = b''
                while not length.endswith(b':'):
                    chunk = connection.recv(1)
                    if not chunk: raise EOFError('Marionette closed')
                    length += chunk
                count = int(length[:-1])
                data = b''
                while len(data) < count:
                    chunk = connection.recv(count - len(data))
                    if not chunk: raise EOFError('Marionette closed')
                    data += chunk
                return json.loads(data)
            receive()
            counter = 0
            def command(name, params):
                global counter
                counter += 1
                data = json.dumps([0, counter, name, params]).encode()
                connection.sendall(str(len(data)).encode() + b':' + data)
                response = receive()
                if response[2]: raise RuntimeError(response[2])
                return response[3]
            command('WebDriver:NewSession', {'capabilities': {'alwaysMatch': {}}})
            command('Marionette:SetContext', {'value': 'chrome'})
            result = command('WebDriver:ExecuteAsyncScript', {
                'script': 'const done = arguments[arguments.length - 1]; document.l10n.ready.then(() => done(["menu-file", "menu-tools", "menu-help"].map(id => document.querySelector(`[data-l10n-id="${id}"]`)?.getAttribute("label"))));',
                'args': [], 'newSandbox': True, 'sandbox': 'default', 'scriptTimeout': 15000})
            assert result['value'] == ['Schedariu', 'Arnesi', 'Aiutu'], result
            print('PASS: real Firefox chrome menus:', result['value'])
        finally:
            if connection: connection.close()
            process.terminate()
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
