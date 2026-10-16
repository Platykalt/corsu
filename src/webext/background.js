/*
 * Corsu web extension: background script (service worker in Chromium, event page in Firefox).
 * Serves the glossaries packaged with the extension to the content script, and relays the keyboard toggle.
 */
"use strict";
const api = globalThis.browser ?? globalThis.chrome;
const cache = new Map();

async function readJSON(path) {
    if (!cache.has(path)) {
        cache.set(path, fetch(api.runtime.getURL(path)).then(response => response.json()));
    }
    return cache.get(path);
}

// Only the glossary files named here can be read: the site id is checked against this table.
const GLOSSARIES = { github: "glossary/github.json" };

api.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type !== "corsu:glossary" || !Object.hasOwn(GLOSSARIES, message.site)) return false;
    Promise.all([readJSON(GLOSSARIES[message.site]), readJSON("glossary/shared.json")])
        .then(([site, shared]) => sendResponse({ site, shared }), () => sendResponse(null));
    return true;
});

api.commands?.onCommand.addListener((command, tab) => {
    if (command === "toggle-original" && tab?.id !== undefined) {
        api.tabs.sendMessage(tab.id, { type: "corsu:toggle" }).catch(() => {});
    }
});
