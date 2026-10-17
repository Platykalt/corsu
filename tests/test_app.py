import http.client
import ipaddress
import json
import socket
import struct
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import app


class SetupWindowTests(unittest.TestCase):
    def setUp(self):
        self.job = app.Job()
        self.server = app.Server(('127.0.0.1', 0), app.make_handler(self.job, [0.0], 0))
        self.port = self.server.server_address[1]
        self.server.RequestHandlerClass = app.make_handler(self.job, [0.0], self.port)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def request(self, method, path, corsu=False, host=None, body=None, origin=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        headers = {'Host': host or f'127.0.0.1:{self.port}', 'Content-Type': 'application/json'}
        if corsu:
            headers['X-Corsu'] = '1'
        if origin:
            headers['Origin'] = origin
        connection.request(method, path, body=json.dumps(body or {}) if method == 'POST' else None, headers=headers)
        response = connection.getresponse()
        return response.status, response.read()

    def test_page_is_served_at_its_address(self):
        status, body = self.request('GET', '/')
        self.assertEqual(status, 200)
        self.assertIn(b'<title>Corsu</title>', body)
        self.assertEqual(self.request('GET', '/', host=f'localhost:{self.port}')[0], 200)
        # A rebound domain name pointing at 127.0.0.1 gets nothing.
        self.assertEqual(self.request('GET', '/', host='attacker.example')[0], 403)

    def test_actions_need_corsus_page(self):
        with patch.object(self.job, 'start', return_value=True) as start:
            self.assertEqual(self.request('POST', '/api/uninstall')[0], 403)
            self.assertEqual(self.request('POST', '/api/uninstall', corsu=True, host='attacker.example')[0], 403)
            self.assertEqual(self.request('POST', '/api/uninstall', corsu=True, origin='https://attacker.example')[0], 403)
            start.assert_not_called()
            self.assertEqual(self.request('POST', '/api/uninstall', corsu=True,
                                          origin=f'http://localhost:{self.port}')[0], 200)
            start.assert_called_once_with('uninstall', ['--uninstall', '--yes'], 'fr')

    def test_connections_from_another_user_are_refused(self):
        with patch.object(app.corsu, 'PLATFORM', 'linux'), patch.object(app, 'peer_uid', return_value=-5), \
                patch.object(app.os, 'getuid', create=True, return_value=1000):
            self.assertEqual(self.request('POST', '/api/logs', corsu=True)[0], 403)

    @unittest.skipUnless(sys.platform.startswith('linux') and Path('/proc/net/tcp').exists(), 'Linux only')
    def test_this_users_requests_pass_and_unknown_callers_are_refused(self):
        # The real check: this user's requests pass every time (the caller's connection is open while it is looked
        # up); a caller that cannot be identified is refused.
        with patch.object(app.corsu, 'PLATFORM', 'linux'), patch.object(app, 'set_preference') as save:
            for _ in range(50):
                self.assertEqual(self.request('POST', '/api/preferences', corsu=True, body={'auto_update': 'x'})[0], 400)
            with patch.object(app, 'peer_uid', return_value=None):
                self.assertEqual(self.request('POST', '/api/preferences', corsu=True, body={'auto_update': True})[0], 403)
        save.assert_not_called()

    def test_state_needs_corsus_page(self):
        self.assertEqual(self.request('GET', '/api/state')[0], 404)
        with patch.object(app, 'snapshot', return_value={'installed': False}):
            status, body = self.request('GET', '/api/state', corsu=True)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['job']['running'], False)

    def test_the_next_port_is_used_when_the_fixed_one_is_taken(self):
        with patch.object(app, 'PORTS', range(self.port, self.port + 3)):
            server = app.listen(self.job, [0.0])
        try:
            self.assertEqual(server.server_address[1], self.port + 1)
        finally:
            server.server_close()

    def test_only_known_parts_reach_the_installer(self):
        with patch.object(self.job, 'start', return_value=True) as start:
            self.request('POST', '/api/switch', corsu=True, body={'components': ['firefox', '--uninstall'], 'on': False,
                                                                     'language': 'fr'})
            start.assert_called_once_with('switch', ['--disable', 'firefox'], 'fr')
            start.reset_mock()
            self.request('POST', '/api/pause', corsu=True, body={'hours': 1})
            start.assert_called_once_with('switch', ['--disable', 'terminal', '--hours', '1.0'], 'fr')


if __name__ == '__main__':
    unittest.main()


HEADER = '  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode'


def proc(address, port):
    """An address and port written as /proc/net/tcp{,6} writes them (32-bit words in the kernel's byte order)."""
    packed = ipaddress.ip_address(address).packed
    words = ''.join('%08X' % struct.unpack('=I', packed[i:i + 4])[0] for i in range(0, len(packed), 4))
    return f'{words}:{port:04X}'


def row(local, remote, state, uid):
    return f'   0: {proc(*local)} {proc(*remote)} {state} 00000000:00000000 00:00000000 00000000 {uid:5d}        0 0'


class PeerUidTests(unittest.TestCase):
    """peer_uid against fake /proc/net tables. The window listens on 127.0.0.1:7744; its caller is 127.0.0.1:50000."""

    CLIENT, SERVER = ('127.0.0.1', 50000), ('127.0.0.1', 7744)

    def lookup(self, tcp=(), tcp6=(), client=CLIENT, server=SERVER, missing=()):
        tables = {'tcp': tcp, 'tcp6': tcp6}

        def read_text(path, *arguments, **keywords):
            if path.name in missing:
                raise PermissionError(path)
            return '\n'.join([HEADER, *tables[path.name]]) + '\n'

        with patch.object(app.Path, 'read_text', read_text):
            return app.peer_uid(client, server)

    def test_the_live_connection_gives_its_user(self):
        self.assertEqual(self.lookup([row(self.CLIENT, self.SERVER, '01', 1000)]), 1000)

    def test_closed_or_closing_connections_do_not_count(self):
        # TIME_WAIT rows show uid 0; FIN_WAIT, CLOSE_WAIT, LAST_ACK, CLOSING... are no live caller either.
        for state in ('02', '03', '04', '05', '06', '07', '08', '09', '0B', '0C'):
            self.assertIsNone(self.lookup([row(self.CLIENT, self.SERVER, state, 0)]), state)
        closed = [row(self.CLIENT, self.SERVER, '06', 0), row(self.CLIENT, self.SERVER, '01', 1000)]
        self.assertEqual(self.lookup(closed), 1000)
        self.assertEqual(self.lookup(closed[::-1]), 1000)

    def test_the_windows_own_sockets_are_not_the_caller(self):
        # Its end of the connection (local and remote swapped) and its listening socket belong to the window's user.
        own = [row(self.SERVER, ('0.0.0.0', 0), '0A', 1000), row(self.SERVER, self.CLIENT, '01', 1000)]
        self.assertIsNone(self.lookup(own))
        # A caller using the window's port as its own port, from another loopback address: the window's end of
        # that connection has the same ports both ways and must not be taken for the caller's.
        client = ('127.0.0.2', 7744)
        rows = [row(self.SERVER, ('0.0.0.0', 0), '0A', 1000), row(self.SERVER, client, '01', 1000),
                row(client, self.SERVER, '01', 1001)]
        self.assertEqual(self.lookup(rows, client=client), 1001)
        self.assertEqual(self.lookup(rows[::-1], client=client), 1001)

    def test_only_the_full_address_and_port_pair_counts(self):
        rows = [row(('127.0.0.1', 50000), ('93.184.216.34', 443), '01', 1000),  # same local port, elsewhere
                row(('192.168.1.5', 50000), ('127.0.0.1', 7744), '01', 1000),  # same ports, other addresses
                row(('127.0.0.1', 50000), ('127.0.0.2', 7744), '01', 1000),
                row(('127.0.0.1', 50001), self.SERVER, '01', 1000)]
        self.assertIsNone(self.lookup(rows))
        self.assertEqual(self.lookup([*rows, row(self.CLIENT, self.SERVER, '01', 1001)]), 1001)

    def test_ipv6_tables_and_ipv4_mapped_addresses(self):
        # A dual-stack client socket talking IPv4 appears in tcp6 with ::ffff:127.0.0.1.
        mapped = row(('::ffff:127.0.0.1', 50000), ('::ffff:127.0.0.1', 7744), '01', 1000)
        self.assertEqual(self.lookup(tcp6=[mapped]), 1000)
        self.assertEqual(self.lookup(tcp6=[mapped], client=('::ffff:127.0.0.1', 50000)), 1000)
        # ::1 is not 127.0.0.1.
        self.assertIsNone(self.lookup(tcp6=[row(('::1', 50000), ('::1', 7744), '01', 1000)]))
        self.assertEqual(self.lookup(tcp6=[row(('::1', 50000), ('::1', 7744), '01', 1000)],
                                     client=('::1', 50000, 0, 0), server=('::1', 7744, 0, 0)), 1000)

    def test_unknown_or_ambiguous_callers_have_no_user(self):
        self.assertIsNone(self.lookup())
        self.assertIsNone(self.lookup(missing=('tcp', 'tcp6')))
        live = row(self.CLIENT, self.SERVER, '01', 1000)
        self.assertEqual(self.lookup([live], missing=('tcp6',)), 1000)
        self.assertEqual(self.lookup([live], tcp6=[row(('::ffff:127.0.0.1', 50000), ('::ffff:127.0.0.1', 7744), '01', 1000)]), 1000)
        self.assertIsNone(self.lookup([live, row(self.CLIENT, self.SERVER, '01', 1001)]))
        self.assertIsNone(self.lookup([live, 'garbage', row(self.CLIENT, self.SERVER, '01', 0)]))
        self.assertEqual(self.lookup(['garbage', '   1: XYZ:12 0100007F:1E40 01 0 0 0 1000', live]), 1000)


@unittest.skipUnless(sys.platform.startswith('linux') and Path('/proc/net/tcp').exists(), 'Linux only')
class PeerUidSocketTests(unittest.TestCase):
    def test_a_real_connection(self):
        listener = socket.create_server(('127.0.0.1', 0))
        self.addCleanup(listener.close)
        client = socket.create_connection(listener.getsockname())
        self.addCleanup(client.close)
        accepted, address = listener.accept()
        self.addCleanup(accepted.close)
        self.assertEqual(address, client.getsockname())
        self.assertEqual(app.peer_uid(address, accepted.getsockname()), app.os.getuid())

    def test_a_caller_on_the_windows_port_from_another_loopback_address(self):
        # The caller binds 127.0.0.2 with the window's own port, so the window's end of the connection has that port
        # both ways. Before 0.25 the lookup took that row (the window's user) for the caller's. The kernel's real
        # tables are used with every row but the caller's own given to another user, as when the caller is not the
        # window's user.
        listener = socket.create_server(('127.0.0.1', 0))
        self.addCleanup(listener.close)
        client = socket.socket()
        self.addCleanup(client.close)
        try:
            client.bind(('127.0.0.2', listener.getsockname()[1]))
            client.connect(listener.getsockname())
        except OSError as error:
            self.skipTest(f'127.0.0.2 unavailable: {error}')
        accepted, address = listener.accept()
        self.addCleanup(accepted.close)
        tables = {name: Path('/proc/net', name).read_text() for name in ('tcp', 'tcp6') if Path('/proc/net', name).exists()}
        own = app.endpoint(address)

        def others(text):
            lines = text.splitlines()
            for index, line in enumerate(lines[1:], 1):
                fields = line.split()
                if app.proc_address(fields[1]) != own:
                    lines[index] = ' '.join([*fields[:7], '4242', *fields[8:]])
            return '\n'.join(lines) + '\n'

        changed = {name: others(text) for name, text in tables.items()}
        self.assertIn('4242', changed['tcp'])
        with patch.object(app.Path, 'read_text', lambda path, *a, **k: changed.get(path.name, '')):
            self.assertEqual(app.peer_uid(address, accepted.getsockname()), app.os.getuid())
            self.assertEqual(app.peer_uid(accepted.getsockname(), address), 4242)

    def test_closed_callers_are_refused(self):
        listener = socket.create_server(('127.0.0.1', 0))
        self.addCleanup(listener.close)
        client = socket.create_connection(listener.getsockname())
        accepted, address = listener.accept()
        self.addCleanup(accepted.close)
        client.close()
        self.assertIsNone(app.peer_uid(address, accepted.getsockname()))
