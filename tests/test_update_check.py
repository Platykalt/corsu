"""Checking for updates (docs/update-diagnosis.md): what made Corsu 0.24.0 say "up to date" while 0.25.1 was out,
and every way a check can fail, which must never read as "up to date". GitHub is a stand-in; the clock is fake."""
from datetime import datetime, timedelta, timezone
import email.message
import http.client
import io
import json
import time
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

import app
import corsu
import update
from tests.test_installer import Isolated

CEST = timezone(timedelta(hours=2))


def at(clock):
    """18 October 2026 at `clock` (HH:MM:SS, Paris summer time), as a timestamp."""
    return datetime.fromisoformat('2026-10-18T' + clock).replace(tzinfo=CEST).timestamp()


def release(version, draft=False, prerelease=False):
    return {'tag_name': 'v' + version, 'draft': draft, 'prerelease': prerelease,
            'html_url': f'https://github.com/Platykalt/corsu/releases/tag/v{version}'}


# What GitHub's list held on 18 October 2026: v0.25.0 is a tag without a release, so it is not in the list at all.
BEFORE = [release('0.24.0'), release('0.23.0'), release('0.22.0')]
AFTER = [release('0.25.1')] + BEFORE
PUBLISHED = datetime(2026, 10, 18, 11, 15, 51, tzinfo=timezone.utc).timestamp()  # v0.25.1, from GitHub


def http_error(code, **headers):
    message = email.message.Message()
    for name, value in headers.items():
        message[name.replace('_', '-')] = value
    return urllib.error.HTTPError(update.API, code, 'error', message, io.BytesIO(b''))


class CutShort(io.BytesIO):
    """An answer whose connection closes before its announced length."""

    def __init__(self):
        super().__init__(b'[{"tag')

    def read(self, *arguments):
        raise http.client.IncompleteRead(b'[{"tag', 4000)


class FakeGitHub:
    """urlopen for the releases list: AFTER once v0.25.1 is published on the fake clock, or what `answer` says."""

    def __init__(self, clock):
        self.clock, self.calls, self.answer = clock, [], None

    def __call__(self, request, timeout=None):
        self.calls.append(self.clock[0])
        answer = self.answer
        if isinstance(answer, BaseException):
            raise answer
        if callable(answer):
            return answer()
        if answer is None:
            answer = AFTER if self.clock[0] >= PUBLISHED else BEFORE
        return io.BytesIO(answer if isinstance(answer, bytes) else json.dumps(answer).encode())


class Checking(Isolated):
    running = '0.24.0'

    def setUp(self):
        super().setUp()
        self.clock = [at('10:49:40')]
        self.github = FakeGitHub(self.clock)
        for patcher in (patch.object(update.time, 'time', lambda: self.clock[0]),
                        patch.object(update.urllib.request, 'urlopen', self.github),
                        patch.object(update, 'current', lambda: self.running)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def install_copy(self, version):
        folder = self.release(version, files={'src/app.py': 'print("copy")\n'})
        corsu.save_state({'files': {}, 'components': ['firefox'],
                          'release': {'version': version, 'folder': str(folder), 'installed_at': 1}})
        return folder


class CacheTests(Checking):
    def test_a_window_opened_hours_after_a_release_asks_github_again(self):
        # 10:49: the 0.23.0 window asks GitHub and saves "0.24.0 is the latest", then updates to 0.24.0.
        self.assertEqual(update.check(force=True)['status'], 'up_to_date')
        # 16:13, v0.25.1 out since 13:15: until 0.25.1 the saved answer counted for 6 hours, so it said "up to date"
        # without asking. Now an answer older than an hour is asked again.
        self.clock[0] = at('16:13:13')
        info = update.check()
        self.assertEqual((info['status'], info['latest'], info['fresh'], info['checked']),
                         ('available', '0.25.1', True, at('16:13:13')))
        self.assertEqual(len(self.github.calls), 2)

    def test_a_saved_answer_keeps_its_date_and_is_not_fresh(self):
        update.check(force=True)
        self.clock[0] = at('11:20:00')
        info = update.check()
        self.assertEqual((info['status'], info['fresh'], info['checked']), ('up_to_date', False, at('10:49:40')))
        self.assertEqual(len(self.github.calls), 1)
        # The window opening asks again past OPEN_MAX_AGE; the button always does.
        self.assertTrue(update.check(max_age=app.OPEN_MAX_AGE)['fresh'])
        self.assertTrue(update.check(force=True)['fresh'])

    def test_an_answer_saved_before_this_copy_was_installed_is_asked_again(self):
        # 0.24.0 saved "latest 0.24.0" a minute ago; then the one-line install put 0.25.1 in place. Used as it is, the
        # new window would call itself a development version (0.25.1 "newer than the latest release 0.24.0").
        update.check(force=True)
        self.running = '0.25.1'
        self.clock[0] = PUBLISHED + 60
        self.install_copy('0.25.1')
        (self.data / update.CACHE).write_text(json.dumps({'format': 2, 'checked': PUBLISHED, 'latest': '0.24.0'}))
        info = update.check()
        self.assertEqual((info['status'], info['latest'], info['fresh']), ('up_to_date', '0.25.1', True))

    def test_a_clock_set_back_does_not_make_an_old_answer_fresh(self):
        update.check(force=True)
        self.clock[0] = at('09:00:00')
        self.assertTrue(update.check()['fresh'])

    def test_a_damaged_cache_is_asked_again(self):
        (self.data).mkdir(parents=True, exist_ok=True)
        for content in ('{', '[]', json.dumps({'format': 2, 'checked': 'soon', 'latest': '0.24.0'}),
                        json.dumps({'format': 2, 'checked': at('10:49:00'), 'latest': ['0.24.0']})):
            (self.data / update.CACHE).write_text(content, encoding='utf-8')
            self.assertEqual(update.check()['latest'], '0.24.0', content)
            self.assertTrue(update.check()['status'] == 'up_to_date')
        self.assertEqual(len(self.github.calls), 4)


class AnswerTests(Checking):
    def test_tags_without_release_drafts_and_prereleases_are_never_offered(self):
        self.github.answer = [release('0.27.0', draft=True), release('0.26.0', prerelease=True),
                              {'tag_name': 'v0.25.1-rc1', 'draft': False, 'prerelease': False}, *AFTER]
        info = update.check(force=True)
        self.assertEqual((info['latest'], info['tag'], info['status']), ('0.25.1', 'v0.25.1', 'available'))
        # Compared as numbers, not as text: 0.25.1 is newer than 0.24.0 and 0.9.0 older than 0.10.0.
        self.assertEqual(update.status_of('0.24.0', '0.25.1'), 'available')
        self.assertEqual(update.status_of('0.10.0', '0.9.0'), 'ahead')

    def test_a_development_copy_newer_than_the_latest_release(self):
        self.running = '0.26.0'
        info = update.check(force=True)
        self.assertEqual((info['status'], info['latest']), ('ahead', '0.24.0'))
        self.clock[0] = PUBLISHED + 60
        self.assertEqual(update.check(force=True)['status'], 'ahead')

    def test_an_installed_copy_newer_than_this_window_means_restart_not_install(self):
        self.install_copy('0.25.1')
        self.clock[0] = PUBLISHED + 60
        info = update.check(force=True)
        self.assertEqual((info['current'], info['installed'], info['latest'], info['status']),
                         ('0.24.0', '0.25.1', '0.25.1', 'up_to_date'))
        self.install_copy('0.24.0')
        self.assertEqual(update.check(force=True)['status'], 'available')

    def test_no_failure_reads_as_up_to_date(self):
        cases = {
            'network': urllib.error.URLError('Name or service not known'),
            'network ': TimeoutError('timed out'),
            'rate_limit': http_error(403, X_RateLimit_Remaining='0', X_RateLimit_Reset=str(int(at('11:30:00')))),
            'rate_limit ': http_error(429, Retry_After='120'),
            'http': http_error(502),
            'http ': http_error(404),
            'bad_response': b'{"releases": "cut',
            'bad_response ': {'message': 'Moved Permanently'},
            'bad_response  ': [],
            'bad_response   ': [release('0.26.0', prerelease=True), release('0.27.0', draft=True)],
            'bad_response    ': CutShort,
        }
        for kind, answer in cases.items():
            with self.subTest(kind=kind.strip()):
                (self.data / update.CACHE).unlink(missing_ok=True)
                self.github.answer = answer
                info = update.check(force=True)
                self.assertEqual((info['status'], info['error_kind'], info['fresh']), ('unknown', kind.strip(), False))
                self.assertTrue(info['error'])
                self.assertIsNone(info['latest'])

    def test_a_failure_keeps_the_last_good_answer_with_its_date_but_says_it_failed(self):
        update.check(force=True)
        self.clock[0] = at('16:13:13')
        self.github.answer = urllib.error.URLError('offline')
        info = update.check()
        self.assertEqual((info['status'], info['latest'], info['checked'], info['error_kind']),
                         ('unknown', '0.24.0', at('10:49:40'), 'network'))
        # Not asked again at once (GitHub's limit), and still not "up to date" meanwhile.
        calls = len(self.github.calls)
        self.clock[0] = at('16:20:00')
        self.assertEqual(update.check()['status'], 'unknown')
        self.assertEqual(len(self.github.calls), calls)
        # After RETRY_AFTER, asked again; the button asks at once.
        self.github.answer = None
        self.clock[0] = at('16:29:00')
        self.assertEqual(update.check()['status'], 'available')

    def test_the_rate_limit_reset_given_by_github_is_waited_for(self):
        self.github.answer = http_error(403, X_RateLimit_Remaining='0', X_RateLimit_Reset=str(int(at('11:30:00'))))
        self.assertEqual(update.check()['error_kind'], 'rate_limit')
        self.github.answer = None
        self.clock[0] = at('11:20:00')  # past RETRY_AFTER, before the reset
        self.assertEqual(update.check()['status'], 'unknown')
        self.assertEqual(len(self.github.calls), 1)
        self.clock[0] = at('11:30:01')
        self.assertEqual(update.check()['status'], 'up_to_date')
        self.assertEqual(update.check(force=True)['fresh'], True)

    def test_the_command_line_check_prints_a_failure_as_unknown(self):
        self.github.answer = http_error(500)
        with patch('sys.stdout', new_callable=io.StringIO) as output:
            self.assertEqual(update.main(['--check']), 0)
        self.assertEqual(json.loads(output.getvalue())['status'], 'unknown')


class WindowTests(Checking):
    """The window's side (app.py): one check when it opens, then again by itself while it stays open."""

    def setUp(self):
        super().setUp()
        for patcher in (patch.object(app.time, 'time', lambda: self.clock[0]),
                        patch.object(app, 'running_version', lambda: self.running),
                        patch.dict(app.UPDATE, {'info': None, 'checking': False, 'auto_started': None,
                                                'restart_error': None})):
            patcher.start()
            self.addCleanup(patcher.stop)
        app.UPDATE.pop('attempted', None)

    def wait(self):
        deadline = time.monotonic() + 10
        while app.UPDATE['checking'] and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertFalse(app.UPDATE['checking'])

    def open_window(self):
        self.assertTrue(app.start_check(None, max_age=app.OPEN_MAX_AGE))
        self.wait()

    def test_the_18_october_timeline(self):
        update.check(force=True)                  # 10:49, the 0.23.0 window finds 0.24.0, then updates to it
        self.clock[0] = at('10:50:04')            # app --replace 7744: the 0.24.0 window opens
        self.open_window()
        self.assertEqual((app.UPDATE['info']['status'], app.UPDATE['info']['latest']), ('up_to_date', '0.24.0'))
        self.clock[0] = at('11:40:00')            # the page polls /api/state: not yet an hour
        self.assertFalse(app.refresh_update(None))
        self.clock[0] = at('13:20:00')            # v0.25.1 published at 13:15:51
        self.assertTrue(app.refresh_update(None))
        self.wait()
        self.assertEqual((app.UPDATE['info']['status'], app.UPDATE['info']['latest']), ('available', '0.25.1'))
        self.assertTrue(app.UPDATE['info']['fresh'])

    def test_a_second_launch_showing_this_window_checks_like_an_opening(self):
        self.open_window()
        self.clock[0] = at('11:05:00')
        self.assertTrue(app.refresh_update(None, app.OPEN_MAX_AGE))
        self.wait()
        self.clock[0] = at('11:06:00')
        self.assertFalse(app.refresh_update(None, app.OPEN_MAX_AGE))

    def test_automatic_updates_start_when_corsu_is_opened_not_in_the_hourly_check(self):
        job = MagicMock(running=False)
        with patch.object(app, 'preferences', return_value={'auto_update': True}), \
                patch.object(app, 'start_update', return_value=True) as start:
            self.open_window()
            self.clock[0] = at('13:20:00')
            self.assertTrue(app.refresh_update(job))
            self.wait()
            self.assertEqual(app.UPDATE['info']['status'], 'available')
            start.assert_not_called()
            self.clock[0] = at('13:40:00')  # a second launch shows the window: Corsu is being opened
            self.assertTrue(app.refresh_update(job, app.OPEN_MAX_AGE, automatic=True))
            self.wait()
            start.assert_called_once_with(job, 'fr' if corsu.french() else 'en', '0.25.1')

    def test_no_refresh_before_the_first_check_nor_during_a_job(self):
        self.assertFalse(app.refresh_update(None))
        self.open_window()
        self.clock[0] = at('15:00:00')
        self.assertFalse(app.refresh_update(MagicMock(running=True)))
        self.assertTrue(app.refresh_update(MagicMock(running=False)))
        self.wait()

    def test_a_newer_copy_opens_its_own_window_instead_of_showing_an_older_one(self):
        # The one-line installer or a launcher of the new copy, while a window of an older copy is still open: that
        # window would show its old code and its old answer about updates.
        with patch.object(app, 'read_session', return_value=('http://localhost:7744/', 'k' * 43)), \
                patch.object(app, 'local_call', return_value={'ticket': 'T'}), \
                patch.object(app, 'local_state', return_value={'version': '0.24.0'}), \
                patch('sys.stdout', new_callable=io.StringIO) as output:
            self.running = '0.25.1'
            self.assertIsNone(app.running_session())
            self.assertIn('0.24.0', output.getvalue())
            self.running = '0.24.0'
            self.assertEqual(app.running_session(), 'http://localhost:7744/#t=T')
            self.running = '0.23.0'  # an older copy shows the newer window already open
            self.assertEqual(app.running_session(), 'http://localhost:7744/#t=T')

    def test_the_restart_is_offered_for_a_newer_installed_copy_only(self):
        folder = self.install_copy('0.25.1')
        state = corsu.load_state()
        self.assertEqual(app.restart_info(state, app.Job())['available'], True)
        self.running = '0.26.0'  # a development copy: the older installed one is not offered
        self.assertEqual(app.restart_info(state, app.Job())['available'], False)
        self.assertTrue(folder.exists())


if __name__ == '__main__':
    unittest.main()
