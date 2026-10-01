/*
 * Vencord, a Discord client mod
 * Copyright (c) 2026 Vendicated and contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

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
    },
    stop() {
        translator?.stop();
        translator = undefined;
    }
});
