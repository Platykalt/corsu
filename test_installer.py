import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import corsu
import installer


class InstallerTests(unittest.TestCase):
    def test_declining_or_previewing_makes_no_changes(self):
        for arguments, consent in (([], 'no'), (['--dry-run'], None)):
            with patch.object(installer, 'available_components', return_value=['firefox']), \
                 patch.object(installer, 'discord_location', return_value=None), \
                 patch.object(installer, 'deploy_release') as deploy, \
                 patch.object(corsu, 'install') as install, \
                 patch('builtins.input', return_value=consent) as question, redirect_stdout(io.StringIO()):
                self.assertEqual(installer.main(arguments), 0)
                deploy.assert_not_called()
                install.assert_not_called()
                if consent is None:
                    question.assert_not_called()

    def test_only_selected_components_are_installed(self):
        with patch.object(installer, 'available_components', return_value=['firefox', 'desktop', 'discord']), \
             patch.object(installer, 'discord_location', return_value=Path('/fake/discord')), \
             patch.object(installer, 'deploy_release', return_value=installer.ROOT), \
             patch.object(installer, 'prepare_build') as build, \
             patch.object(installer, 'install_discord') as discord, \
             patch.object(corsu, 'install') as install, \
             patch.object(installer.shutil, 'which', return_value=None), redirect_stdout(io.StringIO()):
            installer.main(['--yes', '--components', 'firefox'])
            install.assert_called_once_with({'firefox'}, qt_system=False)
            discord.assert_not_called()
            build.assert_not_called()

    def test_external_archive_is_restored_and_later_edits_preserved(self):
        for user_edit in (False, True):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with patch.object(corsu, 'DATA', root / 'data'), patch.object(corsu, 'STATE', root / 'data/state.json'), redirect_stdout(io.StringIO()):
                    archive = root / 'app.asar'
                    archive.write_bytes(b'patched archive')
                    corsu.Installer().external_file(archive, b'original archive')
                    if user_edit:
                        archive.write_bytes(b'user archive')
                    corsu.uninstall()
                    self.assertEqual(archive.read_bytes(), b'user archive' if user_edit else b'original archive')

    def test_discord_checksum_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'vendor').mkdir()
            (root / 'vendor/VencordInstallerCli-linux').write_bytes(b'bad binary')
            (root / 'release.json').write_text(json.dumps({'installer_sha256': 'invalid'}))
            with patch.object(installer, 'ROOT', root), patch.object(installer, 'run') as run:
                with self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
                    installer.install_discord(root / 'discord')
                run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
