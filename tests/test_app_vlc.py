"""VLC's experimental complement in the Corsu window: the snapshot carries vlc_complement.status() for VLC's row, the
/api/vlc-complement endpoint writes the preference and runs the installer for VLC alone, and the page shows the
switch in VLC's row (off by default, disabled with the reason when it cannot be used, or while VLC is off).
Everything runs in a temporary data folder; the installer is never started."""
import http.client
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import MagicMock, patch

import app
from apps import vlc_complement
import update
from tests import test_app_ui as ui

AVAILABLE = {'enabled': False, 'available': True, 'reason': None, 'translations': 1234}
SNAP = {'enabled': False, 'available': False, 'reason': 'not for the Snap of VLC', 'translations': 1234}


class Isolated(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp(prefix='corsu-app-vlc-'))
        self.data = self.folder / 'data'
        self.data.mkdir()
        patches = [patch.object(app.corsu, 'DATA', self.data), patch.object(app.corsu, 'STATE', self.data / 'installation.json'),
                   patch.object(app.corsu, 'HOME', self.folder / 'home'), patch.object(app, 'SESSION', self.data / 'setup-session.json'),
                   patch.dict(app.UPDATE, {'info': None, 'checking': False, 'auto_started': None, 'restart_error': None}),
                   patch.dict(app.COMPLEMENT, {'time': 0.0, 'status': None}),
                   patch.object(app, 'detected', return_value={'vlc'})]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        self.addCleanup(shutil.rmtree, self.folder, True)

    def write_state(self, components=('vlc',), disabled=()):
        app.corsu.STATE.write_text(json.dumps({'files': {}, 'components': list(components), 'disabled': list(disabled)}),
                                   encoding='utf-8')

    def preference(self):
        return update.preferences()['vlc_complement']


class SnapshotTests(Isolated):
    def test_vlcs_row_carries_the_complement_status(self):
        self.write_state()
        with patch.object(vlc_complement, 'status', return_value=dict(AVAILABLE)) as status:
            vlc = next(item for item in app.snapshot()['items'] if item['name'] == 'vlc')
            self.assertEqual(vlc['complement'], AVAILABLE)
            # The choice is read fresh (the command line may have changed it); the rest is kept a little while.
            update.set_preference('vlc_complement', True)
            vlc = next(item for item in app.snapshot()['items'] if item['name'] == 'vlc')
        self.assertTrue(vlc['complement']['enabled'])
        status.assert_called_once()
        self.assertFalse(self.preference() is False)

    def test_off_by_default_and_unavailable_says_why(self):
        self.write_state()
        with patch.object(app.corsu, 'PLATFORM', 'windows'), patch.object(vlc_complement.corsu, 'PLATFORM', 'windows'):
            vlc = next(item for item in app.snapshot()['items'] if item['name'] == 'vlc')
        self.assertFalse(vlc['complement']['enabled'])
        self.assertFalse(vlc['complement']['available'])
        self.assertIn('Linux', vlc['complement']['reason'])

    def test_only_for_vlcs_row(self):
        self.write_state(components=())
        with patch.object(vlc_complement, 'status') as status:
            items = app.snapshot()['items']
        status.assert_not_called()
        vlc = next(item for item in items if item['name'] == 'vlc')
        self.assertNotIn('complement', vlc)
        self.assertFalse([item for item in items if 'complement' in item])

    def test_a_failing_status_leaves_the_row_without_the_switch(self):
        self.write_state()
        with patch.object(vlc_complement, 'status', side_effect=OSError('broken')):
            vlc = next(item for item in app.snapshot()['items'] if item['name'] == 'vlc')
        self.assertIsNone(vlc['complement'])


class EndpointTests(Isolated):
    def setUp(self):
        super().setUp()
        self.job = app.Job()
        self.server = app.Server(('127.0.0.1', 0), app.make_handler(self.job, [0.0], 0))
        self.port = self.server.server_address[1]
        self.server.RequestHandlerClass = app.make_handler(self.job, [0.0], self.port)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        status = patch.object(vlc_complement, 'status', return_value=dict(AVAILABLE))
        self.status = status.start()
        self.addCleanup(status.stop)

    def request(self, body, corsu=True):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        headers = {'Host': f'127.0.0.1:{self.port}', 'Content-Type': 'application/json'}
        if corsu:
            headers.update({'X-Corsu': '1', 'X-Corsu-Key': app.ACCESS.key})
        connection.request('POST', '/api/vlc-complement', body=json.dumps(body), headers=headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read() or b'null')

    def test_on_and_off_run_the_installer_for_vlc_and_write_the_preference(self):
        self.write_state()
        with patch.object(self.job, 'start', return_value=True) as start:
            self.assertEqual(self.request({'on': True, 'language': 'en'}), (200, {'started': True}))
            start.assert_called_once_with('switch', ['--vlc-complement', 'on', '--yes', '--components', 'vlc'], 'en')
            self.assertIs(self.preference(), True)
            start.reset_mock()
            self.assertEqual(self.request({'on': False}), (200, {'started': True}))
            # Off: VLC applied again with its own catalogue; VLC's switch (--disable) is never used.
            start.assert_called_once_with('switch', ['--vlc-complement', 'off', '--yes', '--components', 'vlc'], 'fr')
        self.assertIs(self.preference(), False)
        self.assertFalse(app.corsu.is_disabled('vlc', app.corsu.load_state()))

    def test_busy_changes_nothing(self):
        self.write_state()
        with patch.object(self.job, 'start', return_value=False):
            self.assertEqual(self.request({'on': True}), (409, {'started': False}))
        self.assertIs(self.preference(), False)

    def test_refused_when_unavailable_or_vlc_off_or_not_a_boolean(self):
        self.write_state()
        self.status.return_value = dict(SNAP)
        with patch.object(self.job, 'start') as start:
            self.assertEqual(self.request({'on': True}), (400, {'error': 'not for the Snap of VLC'}))
            self.assertEqual(self.request({'on': 'yes'})[0], 400)
            self.assertEqual(self.request({'on': True}, corsu=False)[0], 403)
            self.status.return_value = dict(AVAILABLE)
            self.write_state(disabled=['vlc'])
            status, body = self.request({'on': True})
            self.assertEqual(status, 400)
            self.assertIn('VLC', body['error'])
            start.assert_not_called()
        self.assertIs(self.preference(), False)

    def test_off_while_vlc_is_off_only_records_the_choice(self):
        self.write_state(disabled=['vlc'])
        update.set_preference('vlc_complement', True)
        with patch.object(self.job, 'start') as start:
            status, body = self.request({'on': False})
        start.assert_not_called()
        self.assertEqual((status, body['started']), (200, False))
        self.assertIs(self.preference(), False)


# The page: VLC's row in each case, in the three languages.
HARNESS = ui.HARNESS[:ui.HARNESS.index('const out = vm.runInContext(`')] + r'''
const out = vm.runInContext(`
  const clean = value => value == null ? value : value.replace(/[\\u00a0\\u202f]/g, " ");
  const result = {};
  for (const lang of ["en", "fr", "co"]) {
    language = lang;
    result[lang] = {};
    for (const [name, scenario] of Object.entries(fixture)) {
      state = scenario;
      restartHints.clear();
      render();
      const row = $("switches").children.find(row => row.find(node => node.id === "switch-vlc").length);
      const own = row.find(node => node.id === "switch-vlc")[0];
      const input = row.find(node => node.id === "switch-vlc-complement")[0];
      const option = row.find(node => node.attributes.class && node.attributes.class.startsWith("option"))[0];
      const why = row.find(node => node.id === "switch-vlc-complement-why")[0];
      const badge = row.find(node => node.attributes.class && node.attributes.class.startsWith("badge"))[0];
      result[lang][name] = {
        rowClass: row.attributes.class || null, own: { checked: "checked" in own.attributes },
        complement: input ? { checked: "checked" in input.attributes, disabled: "disabled" in input.attributes,
          describedby: input.attributes["aria-describedby"] } : null,
        text: option ? clean(option.textContent) : null, why: why ? why.textContent : null,
        badge: badge ? badge.textContent : null,
      };
      if (input && name === "available") {
        input.listeners.change.forEach(listener => listener({ target: { checked: true } }));
        render();
        const again = $("switches").children.find(row => row.find(node => node.id === "switch-vlc").length);
        const label = again.children.find(node => node.attributes && node.attributes.class === "label");
        result[lang].hintAfterChange = label.children.filter(node => node.attributes && node.attributes.class === "hint").map(node => node.textContent);
      }
    }
  }
  JSON.stringify(result);
`, context);
process.stdout.write(out);
'''

IDLE = {'title': None, 'lines': [], 'running': False, 'ok': None, 'progress': None, 'result': None, 'busy': False}


def scenario(complement, vlc=None, job=None):
    fields = {'activation': 'active', 'coverage': None, 'validation': None, 'updated': None, 'instances': [],
              'complement': complement, **(vlc or {})}
    item = ui.entry('VLC', **fields)
    return {**ui.FIXTURE, 'items': [item], 'job': {**IDLE, **(job or {})}}


SCENARIOS = {
    'available': scenario(dict(AVAILABLE)),
    'enabled_restart': scenario({**AVAILABLE, 'enabled': True}, vlc={'activation': 'restart_required'}),
    'unavailable': scenario(dict(SNAP)),
    'unavailable_but_on': scenario({**SNAP, 'enabled': True}),
    'vlc_off': scenario(dict(AVAILABLE), vlc={'on': False, 'activation': 'inactive'}),
    'busy': scenario(dict(AVAILABLE), job={'title': 'switch', 'running': True}),
    'none': scenario(None),
}
KEYS = ['complement_label', 'complement_detail', 'complement_detail_count', 'complement_vlc_off', 'complement_unavailable']


class TextTests(unittest.TestCase):
    def test_texts_exist_in_every_language_with_the_same_placeholders(self):
        import re
        found = ui.texts()
        for language in ('co', 'fr', 'en'):
            for key in KEYS:
                self.assertTrue(found[language].get(key), f'{key} missing in {language}')
                self.assertEqual(set(re.findall(r'\{\w+\}', found[language][key])),
                                 set(re.findall(r'\{\w+\}', found['en'][key])), f'{key} in {language}')
        self.assertEqual(found['fr']['complement_label'] + ' : ' + found['fr']['complement_detail'][0].lower()
                         + found['fr']['complement_detail'][1:],
                         'Complément expérimental : traductions supplémentaires produites et revues par IA, '
                         'non relues par un locuteur.')
        self.assertEqual(found['co']['complement_label'], 'Cumplementu sperimentale')
        self.assertEqual(found['en']['complement_label'], 'Experimental complement')


@unittest.skipUnless(shutil.which('node'), 'node is not installed')
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as folder:
            harness, fixture = Path(folder) / 'harness.js', Path(folder) / 'fixture.json'
            harness.write_text(HARNESS, encoding='utf-8')
            fixture.write_text(json.dumps(SCENARIOS), encoding='utf-8')
            done = subprocess.run(['node', str(harness), str(ui.PAGE), str(fixture)], capture_output=True, text=True,
                                  encoding='utf-8', timeout=60)
        if done.returncode:
            raise AssertionError(done.stderr)
        cls.result = json.loads(done.stdout)
        cls.en = cls.result['en']

    def test_off_by_default_beside_vlcs_own_switch(self):
        view = self.en['available']
        self.assertEqual(view['complement'], {'checked': False, 'disabled': False,
                                              'describedby': 'switch-vlc-complement-detail'})
        self.assertTrue(view['own']['checked'])
        self.assertEqual(view['text'], 'Experimental complement1,234 extra translations made and reviewed by AI, '
                                       'not proofread by a speaker.')
        self.assertIn('tall', view['rowClass'])
        self.assertIn('1 234 traductions supplémentaires', self.result['fr']['available']['text'])
        self.assertIn('Cumplementu sperimentale', self.result['co']['available']['text'])

    def test_a_change_asks_for_vlc_to_restart(self):
        self.assertEqual(self.en['hintAfterChange'], ['Restart VLC to see the change.'])
        self.assertEqual(self.result['fr']['hintAfterChange'], ['Redémarrez VLC pour voir le changement.'])
        view = self.en['enabled_restart']
        self.assertTrue(view['complement']['checked'])
        self.assertEqual(view['badge'], 'Restart needed')

    def test_unavailable_is_disabled_with_the_reason(self):
        view = self.en['unavailable']
        self.assertEqual(view['complement']['checked'], False)
        self.assertTrue(view['complement']['disabled'])
        self.assertEqual(view['why'], 'Not available here: not for the Snap of VLC.')
        self.assertIn('switch-vlc-complement-why', view['complement']['describedby'])
        self.assertEqual(self.result['fr']['unavailable']['why'], 'Indisponible ici : not for the Snap of VLC.')
        # Chosen earlier but unusable here: it can still be switched off.
        self.assertEqual(self.en['unavailable_but_on']['complement']['disabled'], False)
        self.assertTrue(self.en['unavailable_but_on']['complement']['checked'])

    def test_disabled_while_vlc_is_off_or_a_job_runs(self):
        view = self.en['vlc_off']
        self.assertTrue(view['complement']['disabled'])
        self.assertFalse(view['own']['checked'])
        self.assertEqual(view['why'], 'Switch VLC to Corsican first.')
        self.assertEqual(self.result['co']['vlc_off']['why'], 'Mettite prima VLC in corsu.')
        self.assertTrue(self.en['busy']['complement']['disabled'])
        self.assertIsNone(self.en['busy']['why'])

    def test_no_switch_without_a_status(self):
        self.assertIsNone(self.en['none']['complement'])
        self.assertIsNone(self.en['none']['rowClass'])

    def test_no_key_shows_through(self):
        for language, views in self.result.items():
            shown = json.dumps(views, ensure_ascii=False)
            self.assertNotRegex(shown, r'\bcomplement_[a-z_]+\b', language)
            self.assertNotIn('undefined', shown, language)


if __name__ == '__main__':
    unittest.main()
