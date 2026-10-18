/*
 * Vencord, a Discord client mod
 * Copyright (c) 2026 Vendicated and contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

import { showNotification } from "@api/Notifications";
import { definePluginSettings } from "@api/Settings";
import definePlugin, { OptionType } from "@utils/types";

import {
    createTranslator, dictionaryFingerprint, nativePatch, setCorrections, translateThumbarButtons, translateTrayStrings,
    translatorRevision
} from "./translate";

// Written by the Corsu app: corrections from its Review page, and whether hovering shows the original text.
const settings = definePluginSettings({
    showOriginal: {
        type: OptionType.BOOLEAN,
        description: "Mustrà u testu d'origine passendu u topu. Show the original text on hover.",
        default: false
    },
    reportMissing: {
        type: OptionType.BOOLEAN,
        description: "Diagnostic: list untranslated texts in the console, with the reason (no names or messages).",
        default: false,
        hidden: true
    },
    corrections: {
        type: OptionType.STRING,
        description: "Currezzioni (JSON). Corrections (JSON).",
        default: "{}",
        hidden: true
    }
});

let translator: ReturnType<typeof createTranslator> | undefined;
let timer: ReturnType<typeof setInterval> | undefined;

export default definePlugin({
    name: "Corsu",
    description: "Traduzzione lucale parziale di l'interfaccia in corsu. I messaghji fermanu invariati.",
    authors: [{ name: "Corsu local", id: 0n }],
    settings,
    // The menu of the notification-area icon and the taskbar preview buttons are drawn by the desktop app from texts
    // the page sends it; they are translated on their way (see translateTrayStrings in translate.ts).
    patches: [
        {
            find: nativePatch.find,
            replacement: [
                { match: nativePatch.trayStrings, replace: "$&$1=$self.trayStrings($1);" },
                { match: nativePatch.thumbarButtons, replace: "$&$1=$self.thumbarButtons($1);" }
            ]
        }
    ],
    trayStrings: translateTrayStrings,
    thumbarButtons: translateThumbarButtons,
    start() {
        try {
            setCorrections(JSON.parse(settings.store.corrections || "{}"));
        } catch {
            setCorrections({});
        }
        // Read on every hover, so switching the option in Vencord's settings applies at once.
        translator = createTranslator(document, { showOriginal: () => Boolean(settings.store.showOriginal) });
        // Off by default and only in the local console: which build is loaded, then every 10 seconds the texts left
        // untranslated that were not reported yet, each with its reason (see report() in translate.ts for what it
        // never gives).
        if (settings.store.reportMissing) {
            console.info("[CorsuMissing] " + JSON.stringify({ revision: translatorRevision, dictionary: dictionaryFingerprint() }));
            timer = setInterval(() => {
                const report = translator?.report();
                if (report?.findings.length) console.info("[CorsuMissing] " + JSON.stringify(report));
            }, 10000);
        }
        translator.start();
        // The translations start from French or English text; another interface language stays as it is.
        const language = document.documentElement.lang || navigator.language;
        if (!/^(fr|en)/i.test(language)) {
            showNotification({
                title: "Corsu",
                body: "Per vede Discord in corsu, sceglite Français o English in Parametri › Lingua. "
                    + "To see Discord in Corsican, choose Français or English in Settings › Language.",
                permanent: true
            });
        }
    },
    stop() {
        if (timer) clearInterval(timer);
        translator?.stop();
        translator = undefined;
    }
});
