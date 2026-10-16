"""Real programs on Windows (CI runner): 7-Zip (preinstalled), VLC and Notepad++ (installed by the workflow).

For each: Corsu finds it and its Corsican file (Notepad++'s default install lacks it: Corsu fetches the official one), sets its language in the real registry or settings folder, and
switching off gives the previous value back. The programs' windows are not opened: this checks the files and settings
the programs read at start, not their display.
"""
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))


def main():
    data = Path(tempfile.mkdtemp(prefix='corsu-apps-'))
    os.environ['CORSU_USER_LEXICON'] = os.devnull
    import corsu
    corsu.DATA, corsu.STATE = data, data / 'state.json'
    import apps
    from apps import settings
    found = {app_id: app.find() for app_id, app in apps.registry().items()}
    for app_id, installations in found.items():
        for item in installations:
            print(f'{app_id}: {item.describe()} at {item.location}; Corsican file {item.catalog}; reason {item.reason}')
    wanted = ['7zip', 'vlc', 'notepadpp']
    for app_id in wanted:
        assert any(item.usable for item in found[app_id]), f'{app_id}: not usable here'
    settings.registry_set(r'Software\7-Zip', 'Lang', ('en', 1))
    corsu.install(wanted)
    corsu.install(wanted)  # a second run (update, repair) must not take Corsican for the original language
    assert settings.registry_get(r'Software\7-Zip', 'Lang')[0] == 'co'
    assert settings.registry_get(r'Software\VideoLAN\VLC', 'Lang')[0] == 'co'
    native = Path(os.environ['APPDATA']) / 'Notepad++/nativeLang.xml'
    assert 'Corsu' in native.read_text(encoding='utf-8', errors='replace') or 'corsu' in native.read_text(
        encoding='utf-8', errors='replace').lower(), 'nativeLang.xml is not the Corsican file'
    corsu.disable(wanted)
    assert settings.registry_get(r'Software\7-Zip', 'Lang')[0] == 'en', '7-Zip did not get its language back'
    assert settings.registry_get(r'Software\VideoLAN\VLC', 'Lang') is None, 'VLC kept a language it did not have'
    assert not native.exists(), 'nativeLang.xml should be gone (there was none before)'
    corsu.enable(wanted)
    assert settings.registry_get(r'Software\7-Zip', 'Lang')[0] == 'co', 'switching on again did not set Corsican'
    # The person picks German in 7-Zip afterwards: removing Corsu leaves that choice.
    settings.registry_set(r'Software\7-Zip', 'Lang', ('de', 1))
    corsu.uninstall()
    assert settings.registry_get(r'Software\7-Zip', 'Lang')[0] == 'de', 'uninstall undid a language chosen in 7-Zip'
    assert settings.registry_get(r'Software\VideoLAN\VLC', 'Lang') is None, 'uninstall left VLC in Corsican'
    assert not native.exists(), 'uninstall left nativeLang.xml'
    print('7-Zip, VLC and Notepad++: switched to Corsican twice, back, on again, and a later choice kept on uninstall')


if __name__ == '__main__':
    main()
