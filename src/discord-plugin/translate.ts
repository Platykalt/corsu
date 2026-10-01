/*
 * Vencord, a Discord client mod
 * Copyright (c) 2026 Vendicated and contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

import dictionary from "./dictionary.json";

const words: Record<string, string> = dictionary;
// What people write is never translated: messages, names of people, servers, channels and roles, statuses,
// bios, embeds, and the text being typed. Everything else is interface; a text is replaced only when it matches a
// lexicon entry as a whole, so ordinary words inside content are left alone.
const protectedArea = [
    "script", "style", "pre", "code", "textarea", "input", "[contenteditable]", "[data-corsu-ignore]",
    '[id^="chat-messages"]', '[id^="message-content"]', '[id^="message-accessories"]', '[id^="message-reply-context"]',
    '[class*="messageContent"]', '[class*="markup"]', '[class*="embed"]', '[class*="attachment"]',
    '[class*="username"]', '[class*="displayName"]', '[class*="nickname"]', '[class*="globalName"]',
    '[class*="channelName"]', '[class*="guildName"]', '[class*="roleName"]', '[class*="topic"]',
    '[class*="activity"]', '[class*="customStatus"]', '[class*="bio"]', '[class*="aboutMe"]',
    '[class*="member"] [class*="name"]', 'a[href^="/channels/"]:not([href="/channels/@me"])',
    '[class*="threadName"]', '[class*="forumPost"]', '[class*="searchResult"]'
].join(",");

// Kept in step with engine.py: placeholders, trailing punctuation, letter case and
// composed labels. Placeholders always survive translation unchanged.
const placeholder = /\{\s*[$-]?[\w.-]+(?:\([^{}]*\))?\s*\}|%(?:\d+\$)?[0-9]*\.?[0-9]*(?:ll|l|h)?[sdiufgexXop]|%[Ln]?\d+|\$\{[A-Za-z_]\w*\}|\{\d+\}/g;
const separators = /(\s*[\u00a0\u202f ]?[:—–/·|]\s+|\n|\s+-\s+)/;

function normalize(text: string): string {
    return text.replace(/[\u2019\u02bc]/g, "'").replace(/[\u00a0\u202f\u2009]/g, " ");
}

function direct(text: string): string | undefined {
    const key = normalize(text);
    if (Object.hasOwn(words, key)) return words[key];
    const tokens: string[] = [];
    const skeleton = key.replace(placeholder, found => {
        if (!tokens.includes(found)) tokens.push(found);
        return `\u0000${tokens.indexOf(found) + 1}\u0000`;
    });
    if (!tokens.length || !Object.hasOwn(words, skeleton)) return undefined;
    let failed = false;
    const result = words[skeleton].replace(/\u0000(\d+)\u0000/g, (_, index) => {
        const token = tokens[Number(index) - 1];
        if (token === undefined) failed = true;
        return token ?? "";
    });
    return failed ? undefined : result;
}

function resolve(text: string, segments = true): string | undefined {
    const found = direct(text);
    if (found !== undefined) return found;
    const trailing = text.match(/^(.*?)([\s\u00a0]*(?:\.\.\.|…|:|\?|!|;|\.))$/s);
    if (trailing && trailing[1].trim()) {
        const inner = resolve(trailing[1].trimEnd(), false);
        if (inner !== undefined) return inner + trailing[2];
    }
    const lower = text[0]?.toLowerCase() !== text[0] ? text[0].toLowerCase() + text.slice(1)
        : text[0]?.toUpperCase() + text.slice(1);
    if (lower !== text) {
        const other = direct(lower);
        if (other !== undefined) {
            return text[0] === text[0].toUpperCase()
                ? other[0].toUpperCase() + other.slice(1) : other[0].toLowerCase() + other.slice(1);
        }
    }
    if (!segments) return undefined;
    const parts = text.split(separators);
    if (parts.length < 3) return undefined;
    const output: string[] = [];
    for (const [index, part] of parts.entries()) {
        if (index % 2 || !/[^\W\d_]/.test(part)) { output.push(part); continue; }
        const piece = resolve(part.trim(), false);
        if (piece === undefined) return undefined;
        output.push(part.replace(part.trim(), piece));
    }
    return output.join("");
}

export function translateLabel(value: string): string {
    const match = value.match(/^(\s*)(.*?)(\s*)$/s);
    if (!match || !match[2]) return value;
    const [, before, core, after] = match;
    const result = resolve(core);
    if (result === undefined || result === core) return value;
    // Never change a placeholder or markup contract.
    const signature = (text: string) => (text.match(placeholder) ?? []).sort().join("\u0001");
    if (signature(core) !== signature(result)) return value;
    return before + result + after;
}

export function createTranslator(doc: Document) {
    const originalText = new WeakMap<Text, { original: string; translated: string; }>();
    const originalAttrs = new WeakMap<Element, Map<string, { original: string; translated: string; }>>();
    const pending = new Set<Node>();
    let scheduled = false;
    let running = false;

    function text(node: Text) {
        const parent = node.parentElement;
        if (!parent || parent.closest(protectedArea)) return;
        const value = node.data;
        const previous = originalText.get(node);
        if (previous && previous.translated === value) return;
        const translated = translateLabel(value);
        if (translated === value) return;
        originalText.set(node, { original: value, translated });
        node.data = translated;
    }

    function attributes(element: Element) {
        if (element.closest(protectedArea) && !element.matches("input,textarea")) return;
        for (const name of ["aria-label", "title", "placeholder"]) {
            const value = element.getAttribute(name);
            if (!value) continue;
            let saved = originalAttrs.get(element);
            if (saved?.get(name)?.translated === value) continue;
            const translated = translateLabel(value);
            if (translated === value) continue;
            if (!saved) originalAttrs.set(element, saved = new Map());
            saved.set(name, { original: value, translated });
            element.setAttribute(name, translated);
        }
    }

    function walk(root: Node) {
        if (!root.isConnected) return;
        if (root.nodeType === Node.TEXT_NODE) { text(root as Text); return; }
        if (root instanceof Element) {
            if (root.closest(protectedArea)) return;
            attributes(root);
        }
        const walker = doc.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
            acceptNode(node) {
                return node instanceof Element && node.matches(protectedArea)
                    ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
            }
        });
        let node: Node | null;
        while ((node = walker.nextNode())) {
            if (node.nodeType === Node.TEXT_NODE) text(node as Text);
            else attributes(node as Element);
        }
    }

    function flush() {
        scheduled = false;
        if (!running) { pending.clear(); return; }
        const roots = Array.from(pending);
        pending.clear();
        for (const root of roots) {
            if (!roots.some(other => other !== root && other.contains(root))) walk(root);
        }
    }

    const observer = new MutationObserver(records => {
        for (const record of records) {
            if (record.type === "childList") {
                for (const node of record.addedNodes) pending.add(node);
            } else pending.add(record.target);
        }
        // A microtask runs before the next paint, so the original text never shows.
        if (pending.size && !scheduled) { scheduled = true; queueMicrotask(flush); }
    });

    return {
        start() {
            if (running) return;
            running = true;
            walk(doc.documentElement);
            observer.observe(doc.documentElement, {
                subtree: true, childList: true, characterData: true,
                attributes: true, attributeFilter: ["aria-label", "title", "placeholder"]
            });
        },
        stop() {
            if (!running) return;
            running = false;
            observer.disconnect();
            pending.clear();
            const walker = doc.createTreeWalker(doc.documentElement, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
            let node: Node | null;
            while ((node = walker.nextNode())) {
                if (node.nodeType === Node.TEXT_NODE) {
                    const saved = originalText.get(node as Text);
                    if (saved && (node as Text).data === saved.translated) (node as Text).data = saved.original;
                } else {
                    const element = node as Element;
                    for (const [name, saved] of originalAttrs.get(element) ?? []) {
                        if (element.getAttribute(name) === saved.translated) element.setAttribute(name, saved.original);
                    }
                }
            }
        }
    };
}
