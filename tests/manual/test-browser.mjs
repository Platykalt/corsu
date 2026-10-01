import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createRequire } from 'node:module';
const require = createRequire(new URL('./Vencord/package.json', import.meta.url));
const { build } = require('esbuild');
const puppeteer = require('puppeteer-core');

const bundled = await build({
  entryPoints: [new URL('./Vencord/src/userplugins/corsu/translate.ts', import.meta.url).pathname],
  bundle: true, write: false, format: 'iife', globalName: 'Corsu', platform: 'browser'
});
const profile = await mkdtemp(join(tmpdir(), 'corsu-browser-test-'));
let browser;
try {
  browser = await puppeteer.launch({
    browser: 'firefox', executablePath: process.argv[2], headless: true,
    userDataDir: profile, args: ['--no-remote'], timeout: 45000
  });
  const page = await browser.newPage();
  await page.setContent(`<button id="save" aria-label="Save">Save</button>
    <div role="tab" id="friends">Amis</div>
    <div id="chat-messages-123"><button id="message">Save</button></div>
    <button><span class="username_test" id="username">Friends</span></button>
    <textarea id="draft">Save</textarea><div contenteditable="true" id="editor">Friends</div>
    <p id="plain">Friends</p><input id="input" value="Save" placeholder="Search">
    <pre><button id="code">Save</button></pre>
    <div class="formTitle_test" id="settingsTitle">Data &amp; Privacy</div>
    <div role="switch" id="switch" aria-label="Enable">Enable</div>`);
  await page.addScriptTag({ content: bundled.outputFiles[0].text });
  await page.evaluate(() => { window.translator = Corsu.createTranslator(document); window.translator.start(); });
  const initial = await page.evaluate(() => Object.fromEntries([...document.querySelectorAll('[id]')].map(el => [el.id, el.textContent])));
  assert.equal(initial.save, 'Salvà');
  assert.equal(initial.friends, 'Amichi');
  assert.equal(initial.message, 'Save');
  assert.equal(initial.username, 'Friends');
  assert.equal(initial.draft, 'Save');
  assert.equal(initial.editor, 'Friends');
  assert.equal(initial.plain, 'Friends');
  assert.equal(initial.code, 'Save');
  assert.equal(initial.settingsTitle, 'Dati è cunfidenzialità');
  assert.equal(initial.switch, 'Attivà');
  assert.deepEqual(await page.$eval('#input', el => [el.value, el.placeholder]), ['Save', 'Circà']);
  await page.evaluate(() => {
    document.querySelector('#save').textContent = 'Close';
    const button = document.createElement('button'); button.id = 'dynamic'; button.textContent = 'Settings'; document.body.append(button);
  });
  await page.waitForFunction(() => document.querySelector('#dynamic').textContent === 'Paràmetri');
  assert.equal(await page.$eval('#save', el => el.textContent), 'Chjode');
  await page.evaluate(() => window.translator.stop());
  assert.equal(await page.$eval('#save', el => el.textContent), 'Close');
  assert.equal(await page.$eval('#save', el => el.getAttribute('aria-label')), 'Save');
  assert.equal(await page.$eval('#dynamic', el => el.textContent), 'Settings');
  assert.equal(await page.$eval('#input', el => el.placeholder), 'Search');
  assert.equal(await page.$eval('#settingsTitle', el => el.textContent), 'Data & Privacy');
  assert.equal(await page.$eval('#switch', el => el.getAttribute('aria-label')), 'Enable');
  console.log('PASS: Firefox starts; dynamic UI translates; messages, names, drafts, and code are preserved; disabling restores labels.');
} finally {
  if (browser) await browser.close();
  await rm(profile, { recursive: true, force: true });
}
