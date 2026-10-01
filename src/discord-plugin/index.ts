/*
 * Vencord, a Discord client mod
 * Copyright (c) 2026 Vendicated and contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

import { showNotification } from "@api/Notifications";
import definePlugin from "@utils/types";

import { createTranslator } from "./translate";

let translator: ReturnType<typeof createTranslator> | undefined;

export default definePlugin({
    name: "Corsu",
    description: "Traduzzione lucale parziale di l'interfaccia in corsu. I messaghji fermanu invariati.",
    authors: [{ name: "Corsu local", id: 0n }],
    start() {
        translator = createTranslator(document);
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
        translator?.stop();
        translator = undefined;
    }
});
