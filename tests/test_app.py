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
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), app.make_handler('secret', self.job, [0.0]))
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def request(self, method, path, key=None, host=None, body=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        headers = {'Host': host or f'127.0.0.1:{self.port}', 'Content-Type': 'application/json'}
        if key:
            headers['X-Corsu-Key'] = key
        connection.request(method, path, body=json.dumps(body or {}) if method == 'POST' else None, headers=headers)
        response = connection.getresponse()
        return response.status, response.read()

    def test_page_is_served_without_the_key(self):
        status, body = self.request('GET', '/')
        self.assertEqual(status, 200)
        self.assertIn(b'<title>Corsu</title>', body)

    def test_actions_need_the_key_and_a_local_host(self):
        with patch.object(self.job, 'start', return_value=True) as start:
            self.assertEqual(self.request('POST', '/api/uninstall')[0], 403)
            self.assertEqual(self.request('POST', '/api/uninstall', key='wrong')[0], 403)
            self.assertEqual(self.request('POST', '/api/uninstall', key='secret', host='attacker.example')[0], 403)
            start.assert_not_called()
            self.assertEqual(self.request('POST', '/api/uninstall', key='secret')[0], 200)
            start.assert_called_once_with('uninstall', ['--uninstall', '--yes'], 'fr')

    def test_state_needs_the_key(self):
        self.assertEqual(self.request('GET', '/api/state')[0], 404)
        with patch.object(app, 'snapshot', return_value={'installed': False}):
            status, body = self.request('GET', '/api/state', key='secret')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['job']['running'], False)

    def test_only_known_parts_reach_the_installer(self):
        with patch.object(self.job, 'start', return_value=True) as start:
            self.request('POST', '/api/switch', key='secret', body={'components': ['firefox', '--uninstall'], 'on': False,
                                                                     'language': 'fr'})
            start.assert_called_once_with('switch', ['--disable', 'firefox'], 'fr')
            start.reset_mock()
            self.request('POST', '/api/pause', key='secret', body={'hours': 1})
            start.assert_called_once_with('switch', ['--disable', 'terminal', '--hours', '1.0'], 'fr')


if __name__ == '__main__':
    unittest.main()
