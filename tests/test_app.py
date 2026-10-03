import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import app


class SetupWindowTests(unittest.TestCase):
    def setUp(self):
        self.job = app.Job()
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), app.make_handler(self.job, [0.0], 0))
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
