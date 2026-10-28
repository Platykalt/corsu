"""No console window for Corsu's technical commands on Windows, and the process list read once per moment.

The bug (0.28.2): Corsu's window runs under pythonw.exe, which has no console, so every console program it started
(PowerShell for the process list, Minecraft's Java processes and the Start menu shortcut, tasklist) opened a console
window of its own: windows flashed the whole time the window was open. The real check is
tests/e2e/check_windows_consoles.py on the Windows runner; these run anywhere, with the commands replaced.
"""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import app
import corsu
import installer
import minecraft
import update
from apps import programs

SRC = Path(__file__).resolve().parent.parent / 'src'
NO_WINDOW = 0x08000000


def answer(stdout=''):
    return MagicMock(returncode=0, stdout=stdout, stderr='')


class Hidden(unittest.TestCase):
    def setUp(self):
        patch.object(corsu, 'PLATFORM', 'windows').start()
        self.window = patch.object(corsu, 'console_window', return_value=0).start()
        self.addCleanup(patch.stopall)

    def test_windows_gets_no_console_and_keeps_the_rest(self):
        options = corsu.hidden(capture_output=True, text=True, creationflags=0x200)
        self.assertEqual(options, {'capture_output': True, 'text': True, 'creationflags': 0x200 | NO_WINDOW})

    def test_output_not_given_goes_to_this_process_streams(self):
        # The installer the window starts writes into a pipe: its children must write there too, not into a console
        # of their own that nobody sees.
        out, err = MagicMock(), MagicMock()
        with patch.object(sys, 'stdout', out), patch.object(sys, 'stderr', err):
            options = corsu.hidden(check=True)
        self.assertEqual(options, {'check': True, 'creationflags': NO_WINDOW, 'stdout': out, 'stderr': err})
        out.flush.assert_called_once_with()

    def test_output_given_by_the_caller_is_kept(self):
        with patch.object(sys, 'stderr', MagicMock()) as err:
            options = corsu.hidden(stdout=subprocess.PIPE)
        self.assertEqual((options['stdout'], options['stderr']), (subprocess.PIPE, err))

    def test_no_stream_at_all_is_devnull(self):
        # pythonw.exe: sys.stdout and sys.__stdout__ are None.
        with patch.multiple(sys, stdout=None, stderr=None, __stdout__=None, __stderr__=None):
            options = corsu.hidden(check=True)
        self.assertEqual((options['stdout'], options['stderr']), (subprocess.DEVNULL, subprocess.DEVNULL))

    def test_a_stream_without_file_falls_back(self):
        broken = MagicMock()
        broken.fileno.side_effect = OSError('no file')
        real = MagicMock()
        with patch.multiple(sys, stdout=broken, __stdout__=real):
            self.assertIs(corsu.hidden()['stdout'], real)

    def test_in_a_terminal_children_share_its_console(self):
        # A console window already open: a child opens none, and prints into that terminal.
        self.window.return_value = 0x1234
        out, err = MagicMock(), MagicMock()
        with patch.object(sys, 'stdout', out), patch.object(sys, 'stderr', err):
            options = corsu.hidden(check=True)
        self.assertEqual(options, {'check': True, 'stdout': out, 'stderr': err})

    def test_other_systems_unchanged(self):
        self.window.side_effect = AssertionError('not asked elsewhere')
        for platform in ('linux', 'macos'):
            with patch.object(corsu, 'PLATFORM', platform):
                self.assertEqual(corsu.hidden(check=True), {'check': True})


class EveryTechnicalCommand(unittest.TestCase):
    """Each command the window (or the installer it starts) runs on Windows is started without a console."""

    def setUp(self):
        # As under pythonw.exe (the window): no console window of its own.
        patch.object(corsu, 'console_window', return_value=0).start()
        self.addCleanup(patch.stopall)

    def flags(self, mock):
        self.assertTrue(mock.call_args_list, 'nothing was started')
        for call in mock.call_args_list:
            self.assertTrue(call.kwargs.get('creationflags', 0) & NO_WINDOW, call)

    def test_process_list(self):
        with patch.object(corsu, 'PLATFORM', 'windows'), patch('subprocess.run', return_value=answer('C:\\a.exe\n')) as run:
            self.assertEqual(corsu.read_running_executables(), {'C:\\a.exe'})
        self.flags(run)

    def test_minecraft_java_processes(self):
        with patch.object(corsu, 'PLATFORM', 'windows'), patch('subprocess.run', return_value=answer('')) as run:
            self.assertEqual(minecraft.running_folders(), set())
        self.flags(run)

    def test_start_menu_shortcut(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / 'Corsu.lnk').write_bytes(b'L')
            with patch.object(corsu, 'PLATFORM', 'windows'), patch.object(corsu, 'START_MENU', Path(folder), create=True), \
                    patch.object(app.subprocess, 'run', return_value=answer('C:\\p.exe\nC:\\app.py\n')) as run:
                self.assertEqual(app.shortcut_command(), ['C:\\p.exe', 'C:\\app.py'])
        self.flags(run)

    def test_notepad_version(self):
        with patch.object(corsu, 'PLATFORM', 'windows'), patch('subprocess.run', return_value=answer('8.9.8\n')) as run:
            self.assertEqual(programs.NotepadPlusPlus().version('C:\\npp\\notepad++.exe'), '8.9.8')
        self.flags(run)

    def test_discord_clients(self):
        with patch.object(corsu, 'PLATFORM', 'windows'), \
                patch.object(installer.subprocess, 'run', return_value=answer('"Discord.exe","1"\n')) as run:
            self.assertTrue(installer.clients_running())
        self.flags(run)

    def test_installer_commands(self):
        with patch.object(corsu, 'PLATFORM', 'windows'), patch.object(installer.subprocess, 'run') as run:
            installer.run(['git', 'status'])
        self.flags(run)

    def test_update_runs_the_new_installer_without_console(self):
        process = MagicMock(stdout=iter(['@progress 10 x\n']), returncode=0)
        process.wait.return_value = 0
        with patch.object(corsu, 'PLATFORM', 'windows'), patch.object(update.subprocess, 'Popen', return_value=process) as popen:
            update.run_installer(['python.exe', 'installer.py'])
        self.flags(popen)
        # Its output is still read: progress and errors reach the window.
        self.assertEqual(popen.call_args.kwargs['stdout'], subprocess.PIPE)

    def test_no_powershell_or_tasklist_started_with_a_console(self):
        """Any call in src/ that names powershell or tasklist passes through corsu.hidden()."""
        missing = []
        for path in SRC.rglob('*.py'):
            text = path.read_text(encoding='utf-8')
            for node in ast.walk(ast.parse(text)):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ('run', 'Popen') \
                        and getattr(node.func.value, 'id', None) == 'subprocess':
                    segment = ast.get_source_segment(text, node) or ''
                    if ("'powershell'" in segment or "'tasklist'" in segment) and 'hidden(' not in segment:
                        missing.append(f'{path.relative_to(SRC)}:{node.lineno}')
        self.assertEqual(missing, [])


class FailuresStayVisible(unittest.TestCase):
    """Without a console, a failing command still says why: its exit code and error text reach Corsu. Real commands,
    on this system (on the Windows unit-test runner, with CREATE_NO_WINDOW for real)."""

    def test_exit_code_and_stderr_are_kept(self):
        result = subprocess.run([sys.executable, '-c', 'import sys; print("out"); sys.stderr.write("boom\\n"); sys.exit(3)'],
                                **corsu.hidden(capture_output=True, text=True, timeout=60))
        self.assertEqual((result.returncode, result.stdout.strip(), result.stderr.strip()), (3, 'out', 'boom'))

    def test_a_failing_installer_command_reaches_the_window_log(self):
        # The installer, started by the window as a job, runs a technical command that fails: its output and exit
        # code reach the job's lines (what the window shows under "Show details") and the job is marked failed.
        script = ('import sys; sys.path.insert(0, sys.argv[1]); import installer; '
                  'installer.run([sys.executable, "-c", "import sys; print(\'child says no\', flush=True); sys.exit(5)"])')
        job = app.Job()
        job.run([sys.executable, '-c', script, str(SRC)], {**os.environ, 'PYTHONIOENCODING': 'utf-8'})
        text = '\n'.join(job.lines)
        self.assertFalse(job.ok)
        self.assertIn('child says no', text)
        self.assertIn('exit status 5', text)


class ProcessListCache(unittest.TestCase):
    """One window refresh checks several programs: the process list is read once, then again a moment later."""

    def setUp(self):
        self.reads = 0
        self.now = [100.0]
        patch.dict(corsu.RUNNING, {'time': None, 'paths': None}).start()
        patch.object(corsu.time, 'monotonic', lambda: self.now[0]).start()
        self.result = {'C:\\a.exe'}
        patch.object(corsu, 'read_running_executables', self.read).start()
        self.addCleanup(patch.stopall)

    def read(self):
        self.reads += 1
        return None if self.result is None else set(self.result)

    def test_read_once_within_the_moment_then_again(self):
        first = corsu.running_executables()
        self.now[0] += 1.5
        self.assertEqual(corsu.running_executables(), first)
        self.assertEqual(self.reads, 1)
        self.now[0] += 1.0
        self.result = {'C:\\b.exe'}
        self.assertEqual(corsu.running_executables(), {'C:\\b.exe'})
        self.assertEqual(self.reads, 2)

    def test_fresh_when_asked(self):
        corsu.running_executables()
        corsu.running_executables(max_age=0)
        self.assertEqual(self.reads, 2)

    def test_unknown_stays_unknown_and_copies_are_independent(self):
        self.result = None
        self.assertIsNone(corsu.running_executables())
        self.result = {'C:\\a.exe'}
        self.now[0] += 5
        copy = corsu.running_executables()
        copy.add('C:\\changed.exe')
        self.assertEqual(corsu.running_executables(), {'C:\\a.exe'})

    def test_clock_going_back_reads_again(self):
        corsu.running_executables()
        self.now[0] -= 10
        corsu.running_executables()
        self.assertEqual(self.reads, 2)

    def test_programs_checked_in_one_refresh_share_one_reading(self):
        for name in ('WinMergeU.exe', 'SumatraPDF.exe', 'filezilla.exe', 'HandBrake.exe'):
            programs.running(name)
        self.assertEqual(self.reads, 1)


if __name__ == '__main__':
    unittest.main()
