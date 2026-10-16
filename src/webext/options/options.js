// Corsu web options: one switch per site adapter, and how the original text is shown. Stored in storage.local
// (not storage.sync, which would copy the settings to the browser account's servers).
"use strict";
const api = globalThis.browser ?? globalThis.chrome;
const adapters = Object.values(globalThis.CorsuWeb?.adapters || {});

async function load() {
    const settings = await api.storage.local.get({ sites: {}, showOriginal: "tooltip" });
    const list = document.getElementById("sites");
    for (const adapter of adapters) {
        const label = document.createElement("label");
        const box = document.createElement("input");
        box.type = "checkbox";
        box.checked = settings.sites[adapter.id] ?? adapter.id === "github";
        box.addEventListener("change", async () => {
            const current = (await api.storage.local.get({ sites: {} })).sites;
            current[adapter.id] = box.checked;
            await api.storage.local.set({ sites: current });
        });
        label.append(box, " " + adapter.name + " (" + adapter.hosts.join(", ") + ")");
        list.append(label);
    }
    for (const radio of document.querySelectorAll("input[name=showOriginal]")) {
        radio.checked = radio.value === settings.showOriginal;
        radio.addEventListener("change", () => api.storage.local.set({ showOriginal: radio.value }));
    }
}
load();
