#!/usr/bin/env python3
"""Right-click selected text in a translated Firefox and read the "Search <engine> for <selection>" menu item.

Usage: check_firefox_context_menu.py FIREFOX_EXECUTABLE [SCREENSHOT.png]
Runs headless in a throwaway profile (check_firefox.marionette). browser.properties contextMenuSearch takes the
engine as %1$S and the selection as %2$S; the Corsican sentence puts them the other way round, so a translation that
lost the numbers would swap them. The check formats the string directly, then opens the real context menu on a
selection, with the default engine and with another installed one (names read from Services.search), and checks the
selection is shown untouched, Firefox's truncation (15 UTF-16 units, no split surrogate pair, then the locale's
ellipsis) included, and that the access key is a letter of the label (Firefox otherwise appends it in brackets).
With SCREENSHOT, Firefox runs on a nested headless weston instead and the open menu is photographed: see `main`.
"""
import html
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from check_firefox import marionette  # noqa: E402

BUNDLE = 'chrome://browser/locale/browser.properties'
CORSICAN = 'Circà « %2$S » cù %1$S'
FRENCH = 'Recherche %1$S pour « %2$S »'
ENGLISH = 'Search %1$S for “%2$S”'
ELEMENT = 'element-6066-11e4-a52e-4f735466cecf'

# Values the formatter must pass through as they are: Mozilla's own %S/%1$S markers, $ (special in JS replace),
# HTML, both apostrophes and both kinds of quotes.
FORMAT_VALUES = ['Corsica', 'L’isula d\'Elba è bella', '« citazione » “quote” "plain"', '%S %1$S %2$S $1 $& $$',
                 'Tom & Jerry <b>bold</b>', 'àèìòù ÀÈÌÒÙ ç']
# Selections in the page (the menu shows at most 15 UTF-16 units before the ellipsis).
SELECTIONS = ['Corsica', 'L’isula', "d'Elba", '« Aiò »', '“quote”', '%S %1$S $ & <b>', 'àèìòù', '$1 $&',
              'Una selezzione di testu assai longa per vede u taglju', '  spazii   multipli  è  longhi  ',
              'abcdefghijklmn😀xyz']

# Firefox 157 moved the search service from Services.search to a module.
SEARCH = '''
const search = Services.search ??
  ChromeUtils.importESModule("moz-src:///toolkit/components/search/SearchService.sys.mjs").SearchService;
'''

STATE = SEARCH + '''
const done = arguments[arguments.length - 1];
(async () => {
  await search.init();
  const bundle = Services.strings.createBundle(arguments[0]);
  const engines = (await search.getVisibleEngines()).map(engine => engine.name);
  const engine = search.defaultEngine.name;
  done({template: bundle.GetStringFromName("contextMenuSearch"),
        accesskey: bundle.GetStringFromName("contextMenuSearch.accesskey"),
        formatted: arguments[1].map(value => bundle.formatStringFromName("contextMenuSearch", [engine, value])),
        engine, engines, ellipsis: Services.locale.ellipsis, locale: Services.locale.appLocaleAsBCP47});
})().catch(error => done({error: String(error)}));
'''

SET_DEFAULT = SEARCH + '''
const [name, done] = [arguments[0], arguments[arguments.length - 1]];
(async () => {
  const reason = search.CHANGE_REASON?.USER ?? Ci.nsISearchService.CHANGE_REASON_USER;
  await search.setDefault(search.getEngineByName(name), reason);
  done(search.defaultEngine.name);
})().catch(error => done({error: String(error)}));
'''

WAIT_MENU = '''
const done = arguments[arguments.length - 1];
const menu = document.getElementById("contentAreaContextMenu");
const read = () => {
  const item = document.getElementById("context-searchselect");
  // The label Firefox draws, with the access key in <span class="accesskey"> (or appended as " (R)" when the
  // label has no such letter).
  const text = item.querySelector(".menu-highlightable-text");
  done({state: menu.state, hidden: item.hidden, label: item.label, accesskey: item.accessKey,
        shown: text ? text.textContent : null, underlined: text?.querySelector(".accesskey")?.textContent ?? null,
        html: text ? text.innerHTML : null});
};
if (menu.state === "open") read(); else menu.addEventListener("popupshown", read, {once: true});
'''

CLOSE_MENU = '''
const done = arguments[arguments.length - 1];
const menu = document.getElementById("contentAreaContextMenu");
if (menu.state === "closed") done(true);
else { menu.addEventListener("popuphidden", () => done(true), {once: true}); menu.hidePopup(); }
'''

SELECT = '''
const element = document.getElementById(arguments[0]);
const range = document.createRange();
range.selectNodeContents(element);
const selection = window.getSelection();
selection.removeAllRanges();
selection.addRange(range);
return selection.toString();
'''


def shown(selection, ellipsis):
    """What nsContextMenu puts in the label: SelectionUtils.trimSelection collapses white space, then
    showAndFormatSearchContextItem keeps 15 UTF-16 units (16 not to split a surrogate pair) and adds the ellipsis."""
    text = ' '.join(selection.split())
    units = text.encode('utf-16-le')
    if len(units) // 2 > 15:
        keep = 16 if 0xDC00 <= int.from_bytes(units[30:32], 'little') <= 0xDFFF else 15
        text = units[:keep * 2].decode('utf-16-le') + ellipsis
    return text


def page():
    rows = ''.join(f'<p id="s{index}" style="font-size:20px;margin:6px">{html.escape(text)}</p>'
                   for index, text in enumerate(SELECTIONS))
    return 'data:text/html;charset=utf-8,' + urllib.parse.quote(f'<!doctype html><title>corsu</title><body>{rows}')


def async_script(command, script, *arguments):
    result = command('WebDriver:ExecuteAsyncScript', {'script': script, 'args': list(arguments), 'newSandbox': True,
                                                      'sandbox': 'default', 'scriptTimeout': 30000})['value']
    if isinstance(result, dict) and 'error' in result:
        raise RuntimeError(result['error'])
    return result


def open_menu(command, index):
    """Select paragraph `index` in the page and right-click it like a person would; returns the item's state."""
    command('Marionette:SetContext', {'value': 'content'})
    selected = command('WebDriver:ExecuteScript', {'script': SELECT, 'args': [f's{index}']})['value']
    element = command('WebDriver:FindElement', {'using': 'css selector', 'value': f'#s{index}'})['value']
    command('WebDriver:PerformActions', {'actions': [{
        'type': 'pointer', 'id': 'mouse', 'parameters': {'pointerType': 'mouse'},
        'actions': [{'type': 'pointerMove', 'origin': {ELEMENT: element[ELEMENT]}, 'x': 0, 'y': 0},
                    {'type': 'pointerDown', 'button': 2}, {'type': 'pointerUp', 'button': 2}]}]})
    command('WebDriver:ReleaseActions', {})
    command('Marionette:SetContext', {'value': 'chrome'})
    return selected, async_script(command, WAIT_MENU)


def picture(path):
    """Take the nested compositor's screen with weston-screenshooter (it writes wayland-screenshot-*.png in its
    working folder) and move it to `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        subprocess.run(['weston-screenshooter'], cwd=directory, check=True, timeout=60)
        shutil.move(next(pathlib.Path(directory).glob('*.png')), path)


def main(executable, screenshot=None):
    """Without SCREENSHOT the whole check runs headless. With it, Firefox runs on the WAYLAND_DISPLAY of the
    environment, which must be a nested `weston --backend=headless --debug` (never the desktop: refused when
    WAYLAND_DISPLAY is unset or wayland-0), and the screen is saved to SCREENSHOT while the long selection's menu
    is open."""
    if screenshot and os.environ.get('WAYLAND_DISPLAY', 'wayland-0') == 'wayland-0':
        raise SystemExit('A screenshot needs WAYLAND_DISPLAY set to a nested headless weston.')
    failures = []

    def expect(label, value, wanted):
        status = 'PASS' if value == wanted else 'FAIL'
        print(f'{status}: {label} = {value!r}' + ('' if status == 'PASS' else f' (expected {wanted!r})'))
        if status == 'FAIL':
            failures.append(label)

    arguments, environment = ['--headless'], None
    if screenshot:
        # Wayland only, so Firefox cannot fall back to the desktop's X server.
        environment = {name: value for name, value in os.environ.items() if name != 'DISPLAY'}
        arguments, environment['GDK_BACKEND'], environment['MOZ_ENABLE_WAYLAND'] = [], 'wayland', '1'
    with marionette(executable, arguments, environment) as command:
        state = async_script(command, STATE, BUNDLE, FORMAT_VALUES)
        print(f'Interface locale: {state["locale"]}; engines: {state["engines"]}; default: {state["engine"]!r}; '
              f'ellipsis: {state["ellipsis"]!r}')
        expect('contextMenuSearch', state['template'], CORSICAN)
        if state['template'] in (FRENCH, ENGLISH):
            failures.append('contextMenuSearch is not Corsican')
        accesskey = state['accesskey']
        print(f'contextMenuSearch.accesskey = {accesskey!r}')
        if len(accesskey) != 1 or accesskey.lower() not in CORSICAN.replace('%1$S', '').replace('%2$S', '').lower():
            failures.append('the access key is not a letter of the label: Firefox would show it in brackets')
        if state['ellipsis'] != '…':
            failures.append(f'unexpected ellipsis {state["ellipsis"]!r}')
        for value, formatted in zip(FORMAT_VALUES, state['formatted']):
            expect(f'formatted with {value!r}', formatted, f'Circà « {value} » cù {state["engine"]}')

        others = [name for name in state['engines'] if name != state['engine']]
        if not others:
            failures.append('only one search engine is installed: cannot check another one')
        command('Marionette:SetContext', {'value': 'content'})
        command('WebDriver:Navigate', {'url': page()})
        command('Marionette:SetContext', {'value': 'chrome'})
        for engine in [state['engine'], *others[:1]]:
            expect('default engine', async_script(command, SET_DEFAULT, engine), engine)
            for index, text in enumerate(SELECTIONS):
                selected, item = open_menu(command, index)
                label = f'menu, {engine}, {text!r}'
                if item['state'] != 'open' or item['hidden']:
                    print(f'FAIL: {label}: menu {item["state"]}, item hidden {item["hidden"]}')
                    failures.append(label)
                else:
                    expect(label, item['label'], f'Circà « {shown(selected, state["ellipsis"])} » cù {engine}')
                    # Drawn as the label, with the access key underlined inside it (no " (R)" added). macOS menus
                    # have no access keys: the label is drawn plain there.
                    underlined = '' if sys.platform == 'darwin' else accesskey.lower()
                    if item['shown'] != item['label'] or (item['underlined'] or '').lower() != underlined:
                        print(f'FAIL: {label}: drawn as {item["html"]!r}')
                        failures.append(label + ' (drawn label)')
                if screenshot and engine == state['engine'] and index == 8:
                    time.sleep(1)
                    picture(pathlib.Path(screenshot))
                    print(f'Screenshot of the open menu: {screenshot} ({item["label"]!r})')
                async_script(command, CLOSE_MENU)
            print(f'Drawn label of the last item: {item["html"]!r}')
        expect('engine put back', async_script(command, SET_DEFAULT, state['engine']), state['engine'])
    if failures:
        raise SystemExit('Context menu search is wrong in the running Firefox: ' + ', '.join(failures))
    print('PASS: context menu search on selected text')


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors='replace')
    main(*sys.argv[1:3])
