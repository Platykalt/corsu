/*
 * Vencord, a Discord client mod
 * Copyright (c) 2026 Vendicated and contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

import { showNotification } from "@api/Notifications";
import { definePluginSettings } from "@api/Settings";
import definePlugin, { OptionType } from "@utils/types";

import { createTranslator, setCorrections } from "./translate";

// Written by the Corsu app: corrections from its Review page, and whether hovering shows the original text.
const settings = definePluginSettings({
    showOriginal: {
        type: OptionType.BOOLEAN,
        description: "Mustrà u testu d'origine passendu u topu. Show the original text on hover.",
        default: false,
        restartNeeded: true
    },
    reportMissing: {
        type: OptionType.BOOLEAN,
        description: "Diagnostic: list untranslated texts in the console.",
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
    start() {
        try {
            setCorrections(JSON.parse(settings.store.corrections || "{}"));
        } catch {
            setCorrections({});
        }
        translator = createTranslator(document, { showOriginal: settings.store.showOriginal });
        if (settings.store.reportMissing) {
            timer = setInterval(() => {
                const found = translator?.report() ?? [];
                if (found.length) console.info("[CorsuMissing] " + JSON.stringify(found));
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
