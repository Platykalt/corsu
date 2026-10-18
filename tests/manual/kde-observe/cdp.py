"""In the container's Discord page (DevTools): where the page is, whether the Corsu plugin runs, then Discord's own
NativeUtils module (patched by the plugin) called with the strings Discord's page sends in French, as its system tray
manager does after login."""
import json
import sys
import urllib.request

sys.path.insert(0, '/corsu/tests/e2e')
from check_chromium import DevTools  # noqa: E402

import time

READY = ('(() => { try { return Object.keys(Vencord.Webpack.search(",setSystemTrayApplications")).length > 0; } '
         'catch { return false; } })()')
devtools = None


def run(expression):
    result = devtools.call('Runtime.evaluate', {'expression': expression, 'returnByValue': True, 'awaitPromise': True})
    return result.get('result', {}).get('value', result.get('exceptionDetails', {}).get('exception', {}).get('description'))


# Discord reloads its page while starting, and its webpack loads after the page: wait for both, reconnecting.
for attempt in range(300):
    try:
        targets = json.load(urllib.request.urlopen('http://127.0.0.1:9222/json'))
        page = next(t for t in targets if t.get('type') == 'page' and 'discord.com' in t.get('url', ''))
        devtools = DevTools(page['webSocketDebuggerUrl'])
        if run(READY) is True:
            break
    except Exception as error:
        last = error
    time.sleep(1)
print('waited', attempt, 's')


FRENCH = {"appName": "Discord", "openApp": "Ouvrir Discord", "mute": "Rendre muet", "deafen": "Mettre en sourdine",
          "suppressed": "Interdit", "serverMuted": "Serveur muet", "serverDeafened": "Mis en sourdine sur le serveur",
          "voiceSettings": "Ouvrir les paramètres vocaux et vidéo", "checkForUpdates": "Rechercher les mises à jour…",
          "acknowledgements": "Remerciements", "quitApp": "Quitter Discord",
          "closeHint": "Salut ! Discord s'exécutera en arrière-plan pour te permettre de rester en contact avec "
                       "tes ami(e)s. Tu peux faire un clic droit ici pour quitter."}
NATIVE = ('(() => { const ids = Object.keys(Vencord.Webpack.search(",setSystemTrayApplications")); '
          'const exports = Vencord.Webpack.wreq(ids[0]); '
          'const utils = Object.values(exports).find(v => v && typeof v.setSystemTrayStrings === "function"); '
          'return { ids, utils }; })()')
print('url:', run('location.href'))
print('page language:', run('document.documentElement.lang + " / " + navigator.language'))
print('Corsu plugin enabled:', run('Vencord.Plugins.isPluginEnabled("Corsu")'))
print('NativeUtils module:', run('(() => { const { ids, utils } = ' + NATIVE + '; return JSON.stringify({ ids, '
      'patched: String(utils.setSystemTrayStrings).includes("trayStrings"), '
      'code: String(utils.setSystemTrayStrings).slice(0, 140) }); })()'))
print('call:', run('(() => { const { utils } = ' + NATIVE + '; utils.setSystemTrayStrings('
      + json.dumps(FRENCH) + '); return "setSystemTrayStrings called with the French strings"; })()'))
