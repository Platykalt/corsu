/*
 * Vencord, a Discord client mod
 * Copyright (c) 2026 Vendicated and contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

import dictionary from "./dictionary.json";

const words: Record<string, string> = dictionary;
// Corrections made in the Corsu app's Review page; they win over the dictionary.
let corrections: Record<string, string> = {};

export function setCorrections(value: Record<string, string> | undefined) {
    corrections = value ?? {};
}
// What people write is never touched: messages, bios, statuses, embeds and the text being typed.
const contentArea = [
    // Code blocks sit inside messages (markup); a bare <pre> elsewhere is an interface tooltip.
    "script", "style", "textarea", "input", "[contenteditable]", "[data-corsu-ignore]",
    '[id^="message-content"]', '[id^="message-accessories"]', '[class*="messageContent"]', '[class*="markup"]',
    '[class*="embed"]', '[class*="attachment"]', '[class*="topic"]', '[class*="customStatus"]', '[class*="bio"]',
    '[class*="aboutMe"]', '[class*="forumPost"]', '[class*="searchResult"]'
].join(",");
// Names of people, servers, channels and roles: only labels around them change (templates like "Send a message in
// {channel}" and dates); a name itself is never looked up in the dictionary.
const nameArea = [
    '[id^="chat-messages"]', '[id^="message-reply-context"]',
    '[class*="username"]', '[class*="displayName"]', '[class*="nickname"]', '[class*="globalName"]',
    '[class*="channelName"]', '[class*="guildName"]', '[class*="roleName"]', '[class*="activity"]',
    '[class*="member"] [class*="name"]', 'a[href^="/channels/"]:not([href="/channels/@me"])', '[class*="threadName"]'
].join(",");
const protectedArea = contentArea + "," + nameArea;

// Discord shows dates in its interface language; give the day and month their Corsican names.
const days: Record<string, string> = { lundi: "luni", mardi: "marti", mercredi: "mercuri", jeudi: "ghjovi",
    vendredi: "venneri", samedi: "sabbatu", dimanche: "dumenica" };
const months: Record<string, string> = { janvier: "ghjennaghju", février: "ferraghju", mars: "marzu", avril: "aprile",
    mai: "maghju", juin: "ghjugnu", juillet: "lugliu", août: "aostu", septembre: "sittembre", octobre: "ottobre",
    novembre: "nuvembre", décembre: "dicembre" };
const datePattern = new RegExp(`\\b(${Object.keys(days).join("|")}|${Object.keys(months).join("|")}|Aujourd’hui|Aujourd'hui|Hier|Demain)\\b`, "gi");
const relative: Record<string, string> = { "aujourd’hui": "Oghje", "aujourd'hui": "Oghje", hier: "Eri", demain: "Dumane" };

function translateDate(text: string): string | undefined {
    if (!/\d/.test(text) || !/^[\p{L}\d\s:,./’'-]+$/u.test(text)) return undefined;
    let changed = false;
    const result = text.replace(datePattern, word => {
        const lower = word.toLowerCase();
        const value = days[lower] ?? months[lower] ?? relative[lower];
        if (!value) return word;
        changed = true;
        return word[0] === word[0].toUpperCase() ? value[0].toUpperCase() + value.slice(1) : value;
    });
    return changed ? result : undefined;
}

// Templates with names or numbers inside ("Send a message in {channel}"), indexed by the first or last word of
// their fixed text so that each label only tries a handful of them.
type Template = { pattern: RegExp; value: string; fixed: number; };
let templates: Map<string, Template[]> | undefined;
const escape = (text: string) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

function templateIndex() {
    if (templates) return templates;
    templates = new Map();
    for (const [key, value] of [...Object.entries(words), ...Object.entries(corrections)]) {
        if (!key.includes("\u0000")) continue;
        const parts = key.split(/\u0000\d+\u0000/);
        const fixed = parts.join("").trim().length;
        if (!parts.some(part => /[\p{L}]{2}/u.test(part))) continue;
        const order: number[] = [];
        key.replace(/\u0000(\d+)\u0000/g, (_, index) => { order.push(Number(index)); return ""; });
        const pattern = new RegExp("^" + parts.map(escape).join("(.+?)") + "$", "s");
        const head = parts[0].trim().split(/\s+/)[0]?.toLowerCase();
        const tail = parts[parts.length - 1].trim().split(/\s+/).pop()?.toLowerCase();
        const index = head ? "^" + head : "$" + (tail ?? "");
        const entry = { pattern, fixed, value: value.replace(/\u0000(\d+)\u0000/g, (_, n) => `\u0000${order.indexOf(Number(n)) + 1}\u0000`) };
        if (!templates.has(index)) templates.set(index, []);
        templates.get(index)!.push(entry);
    }
    // The most specific template wins.
    for (const list of templates.values()) list.sort((a, b) => b.fixed - a.fixed);
    return templates;
}

function fromTemplate(text: string): string | undefined {
    const key = normalize(text);
    const words = key.trim().split(/\s+/);
    const candidates = [...(templateIndex().get("^" + words[0]?.toLowerCase()) ?? []),
        ...(templateIndex().get("$" + words[words.length - 1]?.toLowerCase()) ?? [])].sort((a, b) => b.fixed - a.fixed);
    for (const { pattern, value, fixed } of candidates) {
        const match = key.match(pattern);
        // Too little fixed text ("Send {x}") would match labels that only start the same way; such short templates
        // apply only when what they capture is a number ("{count} mentions").
        if (match && fixed < 12 && !match.slice(1).every(group => /^[\d\s.,\u00a0\u202f+]+$/.test(group))) continue;
        if (match) return value.replace(/\u0000(\d+)\u0000/g, (_, n) => match[Number(n)] ?? "");
    }
    return undefined;
}

// Labels made of several parts, like "Unread messages, Server name, Screen share active": translate the parts that
// are interface text and leave the names as they are.
function composite(text: string): string | undefined {
    if (!text.includes(", ") || text.length > 240) return undefined;
    const parts = text.split(/(,\s+)/);
    let changed = false;
    const output = parts.map((part, index) => {
        if (index % 2) return part;
        const found = resolve(part.trim(), false) ?? fromTemplate(part.trim());
        if (found === undefined) return part;
        changed = true;
        return part.replace(part.trim(), found);
    });
    return changed ? output.join("") : undefined;
}

// Kept in step with engine.py: placeholders, trailing punctuation, letter case and
// composed labels. Placeholders always survive translation unchanged.
const placeholder = /\{\s*[$-]?[\w.-]+(?:\([^{}]*\))?\s*\}|%(?:\d+\$)?[0-9]*\.?[0-9]*(?:ll|l|h)?[sdiufgexXop]|%[Ln]?\d+|\$\{[A-Za-z_]\w*\}|\{\d+\}/g;
const separators = /(\s*[\u00a0\u202f ]?[:—–/·|]\s+|\n|\s+-\s+)/;

function normalize(text: string): string {
    return text.replace(/[\u2019\u02bc]/g, "'").replace(/[\u00a0\u202f\u2009]/g, " ");
}

function direct(text: string): string | undefined {
    const key = normalize(text);
    if (Object.hasOwn(corrections, key)) return corrections[key];
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
    const templated = fromTemplate(text);
    if (templated !== undefined) return templated;
    // A label followed by a count, written with or without spaces: "Members—3", "Membres — 3", "Online – 12".
    const counted = text.match(/^(.*?\p{L})(\s*[—–:-]\s*|\s+)(\d[\d\s.,\u00a0\u202f]*)$/u);
    if (counted) {
        const label = resolve(counted[1], false);
        if (label !== undefined) return label + counted[2] + counted[3];
    }
    if (!segments) return undefined;
    const parts = text.split(separators);
    if (parts.length < 3) return composite(text) ?? translateDate(text);
    const output: string[] = [];
    for (const [index, part] of parts.entries()) {
        if (index % 2 || !/[^\W\d_]/.test(part)) { output.push(part); continue; }
        const piece = resolve(part.trim(), false);
        if (piece === undefined) return composite(text);
        output.push(part.replace(part.trim(), piece));
    }
    return output.join("");
}

// Inside names only templates and dates apply, so a name that happens to be a dictionary word stays as it is.
function nameLabel(value: string): string {
    const match = value.match(/^(\s*)(.*?)(\s*)$/s);
    if (!match || !match[2]) return value;
    const result = fromTemplate(match[2]) ?? translateDate(match[2]);
    return result === undefined ? value : match[1] + result + match[3];
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

// With showOriginal, hovering a translated label shows the text it replaced: a way to learn while using Discord.
export function createTranslator(doc: Document, options: { showOriginal?: boolean; } = {}) {
    const originalText = new WeakMap<Text, { original: string; translated: string; }>();
    const originalAttrs = new WeakMap<Element, Map<string, { original: string; translated: string; }>>();
    const pending = new Set<Node>();
    let scheduled = false;
    let running = false;

    function text(node: Text) {
        const parent = node.parentElement;
        if (!parent || parent.closest(contentArea)) return;
        const value = node.data;
        const previous = originalText.get(node);
        if (previous && previous.translated === value) return;
        const translated = parent.closest(nameArea) ? nameLabel(value) : translateLabel(value);
        if (translated === value) return;
        originalText.set(node, { original: value, translated });
        node.data = translated;
        if (options.showOriginal && !parent.hasAttribute("title")) {
            parent.setAttribute("title", value.trim());
            parent.setAttribute("data-corsu-title", "");
        }
    }

    function attributes(element: Element) {
        if (element.closest(contentArea) && !element.matches("input,textarea")) return;
        const inName = Boolean(element.closest(nameArea));
        for (const name of ["aria-label", "title", "placeholder"]) {
            const value = element.getAttribute(name);
            if (!value) continue;
            let saved = originalAttrs.get(element);
            if (saved?.get(name)?.translated === value) continue;
            const translated = inName ? nameLabel(value) : translateLabel(value);
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
            if (root.closest(contentArea)) return;
            attributes(root);
        }
        const walker = doc.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
            acceptNode(node) {
                return node instanceof Element && node.matches(contentArea)
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

    // Diagnostic: visible texts that still look French or English, and whether a protection rule skipped them.
    const reported = new Set<string>();
    function report() {
        const found: string[] = [];
        const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
        let node: Node | null;
        while ((node = walker.nextNode())) {
            const text = (node as Text).data.trim();
            const parent = (node as Text).parentElement;
            if (!parent || text.length < 2 || text.length > 160 || !/[A-Za-zÀ-ÿ]{2}/.test(text)) continue;
            if (parent.closest("script,style") || !(parent as HTMLElement).offsetParent) continue;
            if (translateLabel(text) !== text || reported.has(text)) continue;
            if (!/[éèêàçùûôîâ]|\b(le|la|les|des|un|une|de|du|et|à|en|pour|the|and|to|of|your)\b|^[A-Z][a-zé]+$/i.test(text)) continue;
            reported.add(text);
            const skipped = parent.closest(protectedArea);
            found.push((skipped ? "P " + (skipped.className || skipped.tagName).toString().slice(0, 40) + " | " : "") + text);
        }
        return found;
    }

    return {
        report,
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
                if (node instanceof Element && node.hasAttribute("data-corsu-title")) {
                    node.removeAttribute("title");
                    node.removeAttribute("data-corsu-title");
                }
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
