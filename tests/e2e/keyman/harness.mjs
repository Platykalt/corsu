// Runs Corsu's Keyman lexical models inside the real Keyman for Android web engine, headless.
//
//   node harness.mjs --assets DIR --keyboard sil_euro_latin.js --model ID=FILE.model.js [--model ...]
//                    --chrome CHROME --scenarios scenarios.json --out log.json
//
// Each scenario runs once per model, unless it names its own ("model": null runs it without one).
//
// DIR is the assets/ folder of an official Keyman for Android APK (keyboard.html, keymanweb-webview.js,
// android-host.js...). The page gets a stand-in for the app's Java bridge (window.jsInterface) that keeps the
// text field, and the harness calls the same JavaScript entry points the Java side calls on a phone:
// setKeymanLanguage, enableSuggestions, updateKMText and updateKMSelectionRange. Keys are pressed with real touch
// taps at their centre on the on-screen keyboard (so the gesture engine computes its fat-finger distribution, as
// on a phone); letters only reachable by a long press are raised directly as Keyman's subkey popup does.
// Suggestions are read from and accepted through the banner's PredictionContext.
//
// Needs puppeteer-core (resolved from NODE_PATH or a node_modules folder next to this file). HARNESS_DEBUG=1 prints
// taps and page messages; HARNESS_SCREENSHOT=file.png saves the keyboard as first shown (headless page only).
import { createServer } from 'node:http';
import { readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { extname, join, resolve } from 'node:path';

const require = createRequire(import.meta.url);
const puppeteer = require('puppeteer-core');

function parseArguments(argv) {
  const options = { models: {} };
  for (let i = 0; i < argv.length; i += 2) {
    const [name, value] = [argv[i], argv[i + 1]];
    if (name === '--model') {
      const [id, file] = value.split('=');
      options.models[id] = resolve(file);
    } else {
      options[name.replace(/^--/, '')] = value;
    }
  }
  for (const required of ['assets', 'keyboard', 'chrome', 'scenarios', 'out']) {
    if (!options[required]) throw new Error(`--${required} is required`);
  }
  return options;
}

const USER_AGENTS = {
  android: 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36',
  iphone: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
};

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.ttf': 'font/ttf',
                '.gif': 'image/gif', '.svg': 'image/svg+xml', '.map': 'application/json' };

function serve(options) {
  const server = createServer(async (request, response) => {
    // The engine asks for "//kmwosk.css" (root "./" plus "/"): collapse repeated slashes.
    const path = decodeURIComponent(request.url.split(/[?#]/)[0]).replace(/\/{2,}/g, '/');
    let file = null;
    if (path.startsWith('/models/')) {
      file = options.models[path.slice('/models/'.length).replace(/\.model\.js$/, '')];
    } else if (path === '/packages/sil_euro_latin/sil_euro_latin.js') {
      file = resolve(options.keyboard);
    } else if (!path.includes('..')) {
      file = join(resolve(options.assets), path);
    }
    try {
      const body = await readFile(file);
      response.writeHead(200, { 'Content-Type': (TYPES[extname(file)] || 'application/octet-stream') + '; charset=utf-8' });
      response.end(body);
    } catch {
      if (process.env.HARNESS_DEBUG) console.error('404', path);
      response.writeHead(404);
      response.end();
    }
  });
  return new Promise(done => server.listen(0, '127.0.0.1', () => done(server)));
}

// The Java bridge, reduced to what the web engine calls. insertText(dn, s, dr) is how KeymanWeb edits the
// app's text field: delete dn code points before the caret and dr after it, then insert s.
function bridge() {
  const field = { text: '', start: 0, end: 0, log: [] };
  window.__field = field;
  const points = text => Array.from(text);
  window.jsInterface = {
    getDeviceType: () => 'AndroidMobile',
    getKeyboardHeight: () => 260 * window.devicePixelRatio,
    getKeyboardWidth: () => 400,
    getDefaultBannerHeight: () => 40 * window.devicePixelRatio,
    initialKeyboard: () => '',
    beepKeyboard: () => {},
    setIsChiral: () => {},
    dispatchKey: (code) => field.log.push({ dispatchKey: code }),
    insertText(dn, s, dr) {
      // A selection is replaced first, as Android's InputConnection does.
      const before = points(field.text.slice(0, field.start));
      const after = points(field.text.slice(field.end));
      before.splice(before.length - dn, dn);
      after.splice(0, dr || 0);
      const left = before.join('') + s;
      field.text = left + after.join('');
      field.start = field.end = left.length;
      field.log.push({ dn, s, dr: dr || 0 });
    },
  };
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const scenarios = JSON.parse(await readFile(options.scenarios, 'utf-8'));
  const server = await serve(options);
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await puppeteer.launch({
    executablePath: options.chrome, headless: true,
    args: ['--no-sandbox', '--disable-gpu', '--no-first-run'],
  });
  const results = [];
  try {
    const runs = scenarios.flatMap(scenario => scenario.model !== undefined ? [scenario]
      : Object.keys(options.models).map(model => ({ ...scenario, model })));
    for (const scenario of runs) {
      const page = await browser.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(String(error)));
      if (process.env.HARNESS_DEBUG) page.on('console', message => console.error('page:', message.text()));
      // A scenario may give another user agent (the prediction worker sees it too): "iphone" is the one of
      // Keyman for iPhone's web view, to check what the models do when the app is not Android.
      await page.emulate({ viewport: { width: 400, height: 700, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
                           userAgent: USER_AGENTS[scenario.userAgent ?? 'android'] });
      await page.evaluateOnNewDocument(bridge);
      await page.goto(`${base}/keyboard.html`, { waitUntil: 'load' });
      await page.waitForFunction(() => window.keyman && keyman.osk && keyman.core, { timeout: 20000 });
      const model = scenario.model;
      const setup = await page.evaluate(async (model, setting, base) => {
        setKeymanLanguage({ KN: 'EuroLatin (SIL)', KI: 'Keyboard_sil_euro_latin', KLC: 'co', KL: 'Corsican',
                            KF: base + '/packages/sil_euro_latin/sil_euro_latin.js', KP: 'sil_euro_latin' });
        const deadline = Date.now() + 20000;
        while (!(keyman.core.activeKeyboard && keyman.osk.vkbd) && Date.now() < deadline) {
          await new Promise(r => setTimeout(r, 50));
        }
        // What KMKeyboard.onConfigurationChanged sends once the keyboard is shown (Java sizes in device pixels).
        setBannerHeight(40 * devicePixelRatio);
        setOskWidth(400 * devicePixelRatio);
        setOskHeight(260 * devicePixelRatio);
        await new Promise(r => setTimeout(r, 300));
        if (model) {
          // The quotes and shape are the ones KMManager.registerLexicalModel sends.
          enableSuggestions({ id: model, languages: ['co'], path: `${base}/models/${model}.model.js`,
                              CustomHelpLink: '' }, setting);
          while (keyman.core.languageProcessor.state !== 'configured' && Date.now() < deadline) {
            await new Promise(r => setTimeout(r, 50));
          }
        }
        return { keyboard: keyman.core.activeKeyboard?.id, state: keyman.core.languageProcessor.state,
                 version: keyman.version || null, layer: keyman.osk.vkbd.layerId };
      }, model, scenario.setting ?? 3, base);
      if (process.env.HARNESS_SCREENSHOT) await page.screenshot({ path: process.env.HARNESS_SCREENSHOT });
      const steps = await runSteps(page, scenario.steps);
      results.push({ name: scenario.name, model, setting: scenario.setting ?? 3, userAgent: scenario.userAgent ?? 'android',
                     setup, steps, errors });
      await page.close();
    }
  } finally {
    await browser.close();
    server.close();
  }
  await writeFile(options.out, JSON.stringify(results, null, 1));
}

// Installed in the page: locating keys, settling predictions, reading the banner, moving the caret.
function installHelpers() {
  const field = window.__field;
  const vkbd = () => keyman.osk.vkbd;
  const context = () => keyman.osk.bannerController.predictionContext;
  let generation = 0;
  keyman.core.languageProcessor.on('suggestionsready', () => generation++);
  keyman.core.languageProcessor.on('invalidatesuggestions', () => generation++);

  // Keys whose only job is to change layer (EuroLatin: Shift, 123, abc, currencies, symbols).
  const LAYER_KEY = /^K_(SHIFT|CAPS|NUMERALS|NUMLOCK|LOWER|UPPER|CURRENCIES|SYMBOLS)$|^T_/;
  const textOf = spec => spec.text || (/^U_[0-9A-F]{4,6}$/.test(spec.id || '')
    ? String.fromCodePoint(parseInt(spec.id.slice(2), 16)) : '');
  const matches = (spec, target) => target.startsWith('K_') && target.length > 1
    ? spec.id === target : textOf(spec) === target && !LAYER_KEY.test(spec.id || '');

  // Key specs of a layer, read from the layout (asking the layer group for a layer it has not built yet would
  // build and attach it, which shifts the page).
  function layerSpecs(layerId) {
    const layer = (vkbd().layerGroup.spec.layer || []).find(layer => layer.id === layerId);
    return (layer?.row || []).flatMap(row => row.key);
  }
  // The keys on screen, with their buttons.
  function shownKeys() {
    return vkbd().layerGroup.activeLayer.rows.flatMap(row => row.keys);
  }

  window.__h = {
    async settle() {
      // Predictions are answered by a web worker; wait until no new batch arrives for a while.
      let seen = -1;
      for (let i = 0; i < 100 && seen !== generation; i++) {
        seen = generation;
        await new Promise(r => setTimeout(r, 120));
      }
    },
    // Where to tap for a character or a K_ key: on the current layer, a base key's centre; failing that, the key
    // that switches to the layer holding it; failing that, a long-press subkey on the current layer.
    locate(target) {
      const current = vkbd().layerId;
      const rect = key => {
        const box = key.btn.getBoundingClientRect();
        return { kind: 'tap', x: box.left + box.width / 2, y: box.top + box.height / 2, id: key.spec.id, layer: current };
      };
      const base = shownKeys().find(key => matches(key.spec, target));
      if (base) return rect(base);
      for (const key of shownKeys()) {
        const sub = (key.spec.sk || []).concat(Object.values(key.spec.flick || {})).find(spec => matches(spec, target));
        if (sub) return { kind: 'longpress', base: key.spec.id, id: sub.id, text: textOf(sub), layer: current };
      }
      for (const layerId of ['default', 'shift', 'numeric', 'symbol']) {
        const reachable = spec => matches(spec, target)
          || (spec.sk || []).concat(Object.values(spec.flick || {})).some(sub => matches(sub, target));
        if (layerId === current || !layerSpecs(layerId).some(reachable)) continue;
        const switcher = shownKeys().find(key => key.spec.nextlayer === layerId
                                                        && LAYER_KEY.test(key.spec.id));
        // Layer keys are modipress gestures in Keyman; their key event is raised directly.
        if (switcher) return { kind: 'longpress', base: switcher.spec.id, id: switcher.spec.id, text: '', switchTo: layerId };
      }
      return { kind: 'missing', target, layer: current };
    },
    // A long-press subkey or a flick raises its key event directly, as Keyman's SubkeyPopup and Flick handlers do.
    longpress(baseId, subId, text) {
      const key = shownKeys().find(key => key.spec.id === baseId);
      const sub = baseId === subId ? key.spec : (key.spec.sk || []).concat(Object.values(key.spec.flick || {}))
        .find(spec => spec.id === subId && textOf(spec) === text);
      vkbd().raiseKeyEvent(vkbd().keyEventFromSpec(sub), null);
    },
    async accept(choice) {
      const list = context().currentSuggestions;
      const suggestion = list.find(s => s.displayAs === choice) || (Number.isInteger(choice) ? list[choice] : null);
      if (!suggestion) throw new Error(`no suggestion ${JSON.stringify(choice)}`);
      await context().accept(suggestion);
    },
    // What KMKeyboard.updateSelectionRange does when the app reports a caret move: send the text, then the range.
    moveCaret(start, end) {
      field.start = start;
      field.end = end;
      updateKMText({ text: field.text });
      updateKMSelectionRange(start, end);
    },
    snapshot(step) {
      const prediction = context();
      return {
        step, text: field.text, caret: [field.start, field.end], layer: vkbd().layerId,
        suggestions: prediction.currentSuggestions.map(s => s.displayAs),
        tags: prediction.currentSuggestions.map(s => s.tag || ''),
        selected: prediction.selected ? prediction.selected.displayAs : null,
      };
    },
  };
}

// Every step records the field, the caret, the OSK layer and the banner once predictions have settled.
async function runSteps(page, steps) {
  await page.evaluate(installHelpers);
  const settle = () => page.evaluate(() => __h.settle());
  async function press(target) {
    for (let attempt = 0; attempt < 3; attempt++) {
      const where = await page.evaluate(target => __h.locate(target), target);
      if (where.kind === 'missing') throw new Error(`no key for ${JSON.stringify(target)} on layer ${where.layer}`);
      if (where.kind === 'longpress') {
        await page.evaluate((base, id, text) => __h.longpress(base, id, text), where.base, where.id, where.text);
      } else {
        // A real touch tap at the key's centre: the gesture engine computes the fat-finger distribution.
        if (process.env.HARNESS_DEBUG) console.error(JSON.stringify(where));
        await page.touchscreen.tap(where.x, where.y);
      }
      await settle();
      if (!where.switchTo) return;
      // Let the on-screen keyboard draw the new layer before reading key positions on it.
      await new Promise(r => setTimeout(r, 250));
    }
    throw new Error(`could not reach the layer for ${JSON.stringify(target)}`);
  }
  const out = [];
  await settle();
  out.push(await page.evaluate(() => __h.snapshot({ start: true })));
  for (const step of steps) {
    try {
      if (step.type !== undefined) {
        for (const ch of Array.from(step.type)) {
          await press(ch === ' ' ? 'K_SPACE' : ch === '\n' ? 'K_ENTER' : ch);
        }
      } else if (step.key) {
        await press(step.key);
      } else if (step.accept !== undefined) {
        await page.evaluate(choice => __h.accept(choice), step.accept);
        await settle();
      } else if (step.caret !== undefined || step.setText !== undefined) {
        const [start, end] = await page.evaluate(step => {
          if (step.setText !== undefined) window.__field.text = step.setText;
          const length = window.__field.text.length;
          const at = step.caret ?? step.at ?? length;
          const [a, b] = Array.isArray(at) ? at : [at, at];
          return [a < 0 ? length + a + 1 : a, b < 0 ? length + b + 1 : b];
        }, step);
        await page.evaluate((start, end) => __h.moveCaret(start, end), start, end);
        await settle();
      }
      out.push(await page.evaluate(step => __h.snapshot(step), step));
    } catch (error) {
      out.push({ step, error: String(error) });
    }
  }
  return out;
}

main().catch(error => { console.error(error); process.exit(1); });
