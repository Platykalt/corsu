/*
 * Corsu web extension: content script. Runs on the sites listed in manifest.json, after core/engine.js and the
 * adapters. Reads the per-site switch from storage.local, gets the glossary from the extension's own files (via
 * the background script, so no file is exposed to the page), and translates the interface zones. Nothing is sent
 * anywhere: the extension has no network access beyond the pages it runs on and does no remote translation.
 */
(async function () {
    "use strict";
    const api = globalThis.browser ?? globalThis.chrome;
    const { adapterFor, compileGlossary, createTranslator } = globalThis.CorsuWeb;
    const adapter = adapterFor(globalThis.CorsuWeb.adapters || {}, location.hostname);
    if (!adapter) return;

    const settings = await api.storage.local.get({ sites: {}, showOriginal: "tooltip" });
    // Sites are off until switched on in the options page, except the pilot site, on by default.
    const enabled = site => settings.sites[site] ?? site === "github";
    const glossaries = await api.runtime.sendMessage({ type: "corsu:glossary", site: adapter.id });
    if (!glossaries) return;
    const table = compileGlossary(glossaries.site, glossaries.shared);

    // Batch DOM work at idle time; the timeout bounds how long English labels can stay visible on busy pages.
    const schedule = callback => (globalThis.requestIdleCallback
        ? requestIdleCallback(callback, { timeout: 150 }) : setTimeout(callback, 50));
    const translator = createTranslator({ adapter, glossary: table, schedule, showOriginal: settings.showOriginal });
    const observer = new MutationObserver(records => translator.handleMutations(records));

    function start() {
        translator.run(document.documentElement);
        document.documentElement.setAttribute("data-corsu", "on");
        observer.observe(document.documentElement, {
            subtree: true, childList: true, characterData: true,
            attributes: true, attributeFilter: [...adapter.attributes, "placeholder"],
        });
    }
    function stop() {
        observer.disconnect();
        translator.stop();
        document.documentElement.removeAttribute("data-corsu");
    }

    if (enabled(adapter.id)) start();

    api.storage.onChanged.addListener((changes, area) => {
        if (area !== "local") return;
        if (changes.showOriginal) translator.setShowOriginal(changes.showOriginal.newValue);
        if (changes.sites) {
            settings.sites = changes.sites.newValue || {};
            if (enabled(adapter.id) && !translator.active) start();
            else if (!enabled(adapter.id) && translator.active) stop();
        }
    });

    // Keyboard command (see manifest "commands"): show the site's own text, then Corsican again.
    api.runtime.onMessage.addListener(message => {
        if (message?.type !== "corsu:toggle" || !enabled(adapter.id)) return;
        if (translator.active) stop(); else start();
    });
})();
