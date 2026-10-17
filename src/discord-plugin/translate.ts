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

// What people chose themselves (user names, display names, server nicknames, server, channel and role names) is
// recognised by where it comes from, not by its look: Discord renders it from its own records, which the React
// components above the text hold in their props (a user, member, guild, channel or role object, with a numeric id).
// A text equal to one of those names is never looked up, even when it is also a dictionary word ("Work", "Error"),
// and inside a label or sentence only the interface text around it changes.
const snowflake = /^\d{15,21}$/;
const nameFields = ["username", "globalName", "global_name", "nick", "nickname", "displayName", "display_name", "name"];
// Discord's records: a channel keeps its DM recipients' ids in `recipients` and the people themselves in
// `rawRecipients`, with group DM nicknames in `nicks` (by user id); a server member is identified by `userId`.
const holders = ["user", "author", "member", "guildMember", "guild", "channel", "role", "recipient", "recipients",
    "rawRecipients", "users", "members", "message", "currentUser", "otherUser", "friend", "relationship", "entry", "item"];
const isId = (id: unknown) => (typeof id === "string" && snowflake.test(id)) || typeof id === "bigint";

function collectNames(value: unknown, into: Set<string>, depth: number) {
    if (!value || typeof value !== "object" || depth > 3) return;
    if (Array.isArray(value)) {
        for (const item of value.slice(0, 50)) collectNames(item, into, depth + 1);
        return;
    }
    const record = value as Record<string, unknown>;
    if (isId(record.id) || isId(record.userId)) {
        for (const field of nameFields) {
            const name = record[field];
            if (typeof name === "string" && name.trim()) into.add(name.trim());
        }
        if (record.nicks && typeof record.nicks === "object") {
            for (const [id, nick] of Object.entries(record.nicks as Record<string, unknown>).slice(0, 50)) {
                if (snowflake.test(id) && typeof nick === "string" && nick.trim()) into.add(nick.trim());
            }
        }
    }
    for (const key of holders) {
        if (Object.hasOwn(record, key)) collectNames(record[key], into, depth + 1);
    }
}

function fiberOf(node: Node): any {
    for (const key in node) if (key.startsWith("__reactFiber$")) return (node as any)[key];
    return undefined;
}

function hostProps(node: Node): any {
    for (const key in node) if (key.startsWith("__reactProps$")) return (node as any)[key];
    return undefined;
}

// React keeps two versions of each component (the one on screen and the one being prepared) and leaves on a DOM
// node the version that created it: after a re-render, such as another conversation shown in the same nodes, that
// version and the components above it can hold the previous props. The version on screen is the one whose props
// React last gave the node (its text, for a text node). When this cannot be told, both are read.
function currentFibers(host: Node, fiber: any): any[] {
    const alternate = fiber?.alternate;
    if (!alternate) return [fiber];
    const shown = host.nodeType === Node.TEXT_NODE ? (host as Text).data : hostProps(host);
    if (shown !== undefined) {
        if (fiber.memoizedProps === shown && alternate.memoizedProps !== shown) return [fiber];
        if (alternate.memoizedProps === shown && fiber.memoizedProps !== shown) return [alternate];
    }
    return [fiber, alternate];
}

// The names the components that render this node know about; empty outside React (and in tests without it).
export function userNames(node: Node | null): Set<string> {
    const names = new Set<string>();
    let host: Node | null = node;
    while (host && !fiberOf(host)) host = host.parentNode;
    if (!host) return names;
    for (let fiber of currentFibers(host, fiberOf(host))) {
        for (let depth = 0; fiber && depth < 40; depth++, fiber = fiber.return) {
            const props = fiber.memoizedProps;
            if (props && typeof props === "object") collectNames(props, names, 0);
            for (const key of ["user", "member", "channel", "guild"]) {
                if (props && typeof props === "object" && Object.hasOwn(props, key)) collectNames(props[key], names, 0);
            }
        }
    }
    return names;
}

// Discord's typing indicator writes the names of the people typing in <strong>, from its own store: its props only
// hold the channel ({channel, isThreadCreation}). Only "Several people are typing…" puts interface text there.
function typingName(element: Element | null): boolean {
    const strong = element?.closest("strong");
    if (!strong) return false;
    let typing = Boolean(strong.closest('[class*="typing"]'));
    for (let fiber = fiberOf(strong), depth = 0; !typing && fiber && depth < 12; depth++, fiber = fiber.return) {
        const props = fiber.memoizedProps;
        typing = Boolean(props && typeof props === "object" && Object.hasOwn(props, "isThreadCreation"));
    }
    if (!typing) return false;
    const parent = strong.parentElement;
    const alone = parent ? Array.from(parent.children).filter(child => child.localName === "strong").length === 1 : true;
    const following = strong.nextSibling?.textContent ?? "";
    return !(alone && /^\s*(are|sont)\b/i.test(following));
}

// Names that must stay as written during the current lookup (set by translateLabel for one label at a time). Every
// way of reading a label checks it, so no part of a name is read as a word, a template, a count or a date.
let keep: Set<string> = new Set();
const kept = (text: string) => keep.size > 0 && keep.has(normalize(text.trim()).toLowerCase());

// Discord shows dates in its interface language; give the day and month their Corsican names.
const days: Record<string, string> = { lundi: "luni", mardi: "marti", mercredi: "mercuri", jeudi: "ghjovi",
    vendredi: "venneri", samedi: "sabbatu", dimanche: "dumenica" };
const months: Record<string, string> = { janvier: "ghjennaghju", février: "ferraghju", mars: "marzu", avril: "aprile",
    mai: "maghju", juin: "ghjugnu", juillet: "lugliu", août: "aostu", septembre: "sittembre", octobre: "ottobre",
    novembre: "nuvembre", décembre: "dicembre" };
const datePattern = new RegExp(`\\b(${Object.keys(days).join("|")}|${Object.keys(months).join("|")}|Aujourd’hui|Aujourd'hui|Hier|Demain)\\b`, "gi");
const relative: Record<string, string> = { "aujourd’hui": "Oghje", "aujourd'hui": "Oghje", hier: "Eri", demain: "Dumane" };

// Relative times written by Discord's date library: "il y a 5 minutes", "dans un jour".
const units: Record<string, string> = { seconde: "secondu", secondes: "secondi", minute: "minutu", minutes: "minuti",
    heure: "ora", heures: "ore", jour: "ghjornu", jours: "ghjorni", semaine: "simana", semaines: "simane",
    mois: "mesi", an: "annu", ans: "anni" };
const amounts: Record<string, string> = { un: "un", une: "una", "quelques": "uni pochi di" };

function relativeTime(text: string): string | undefined {
    const match = text.match(/^(il y a|dans) (\d+|une?|quelques) (\p{L}+)$/u);
    if (!match || !units[match[3]]) return undefined;
    let amount = amounts[match[2]] ?? match[2];
    const unit = match[3] === "mois" && amount === "un" ? "mese" : units[match[3]];
    if (amount === "una" && unit === "ora") amount = "un'";
    else if (amount === "una" && unit === "minutu") amount = "un";
    const quantity = amount.endsWith("'") ? amount + unit : amount + " " + unit;
    return match[1] === "dans" ? "trà " + quantity : quantity + " fà";
}

function translateDate(text: string): string | undefined {
    if (kept(text)) return undefined;
    const ago = relativeTime(text);
    if (ago) return ago;
    if (!/\d/.test(text) || !/^[\p{L}\d\s:,./’'-]+$/u.test(text)) return undefined;
    let changed = false;
    const result = text.replace(/ dernier à /g, () => { changed = true; return " scorsu à "; }).replace(datePattern, word => {
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
    if (kept(text)) return undefined;
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

// Discord ends some labels with "…" where the dictionary has "..." ("est en train d'écrire…"), or the reverse.
function ellipsis(key: string): string | undefined {
    const other = key.endsWith("…") ? key.slice(0, -1) + "..." : key.endsWith("...") ? key.slice(0, -3) + "…" : undefined;
    if (other === undefined) return undefined;
    const value = Object.hasOwn(corrections, other) ? corrections[other] : Object.hasOwn(words, other) ? words[other] : undefined;
    if (value === undefined) return undefined;
    const end = key.endsWith("…") ? "…" : "...";
    return value.endsWith("...") ? value.slice(0, -3) + end : value.endsWith("…") ? value.slice(0, -1) + end : value;
}

function direct(text: string): string | undefined {
    if (kept(text)) return undefined;
    const key = normalize(text);
    if (Object.hasOwn(corrections, key)) return corrections[key];
    if (Object.hasOwn(words, key)) return words[key];
    const dotted = ellipsis(key);
    if (dotted !== undefined) return dotted;
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
    if (kept(text)) return undefined;
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
    // A sentence Discord breaks over lines for layout ("Ce salon n'a pas encore de\nmessage épinglé"): look up the whole
    // sentence and break the translation at the same share of its length.
    if (text.includes("\n")) {
        const lines = text.split(/\s*\n\s*/);
        const joined = resolve(lines.join(" "), false);
        if (joined !== undefined) return rebreak(joined, lines);
    }
    if (!segments) return undefined;
    const parts = text.split(separators);
    if (parts.length < 3) return composite(text) ?? translateDate(text);
    const output: string[] = [];
    for (const [index, part] of parts.entries()) {
        // A name between separators ("Work — Online") stays as it is and the labels around it are translated.
        if (index % 2 || !/[^\W\d_]/.test(part) || nameToken.test(part.trim()) || kept(part)) { output.push(part); continue; }
        const piece = resolve(part.trim(), false);
        if (piece === undefined) return composite(text);
        output.push(part.replace(part.trim(), piece));
    }
    return output.join("");
}

function rebreak(translated: string, lines: string[]): string {
    const total = lines.reduce((sum, line) => sum + line.length + 1, -1);
    let result = translated, offset = 0, seen = 0;
    for (const line of lines.slice(0, -1)) {
        seen += line.length + 1;
        const target = Math.round(seen / total * translated.length);
        // The space nearest to the same share of the text becomes the line break; a line that ends a sentence
        // breaks after the nearest sentence end.
        const sentence = /[.!?:…]$/.test(line);
        let best = -1;
        for (const strict of sentence ? [true, false] : [false]) {
            for (let i = offset; i < result.length; i++) {
                if (result[i] !== " " || /[?!:;»]/.test(result[i + 1] ?? "") || strict && !/[.!?:…]/.test(result[i - 1] ?? "")) continue;
                if (best < 0 || Math.abs(i - target) < Math.abs(best - target)) best = i;
            }
            if (best >= 0) break;
        }
        if (best < 0) break;
        result = result.slice(0, best) + "\n" + result.slice(best + 1);
        offset = best + 1;
    }
    return result;
}

// Inside names only templates and dates apply, so a name that happens to be a dictionary word stays as it is.
function nameLabel(value: string): string {
    const match = value.match(/^(\s*)(.*?)(\s*)$/s);
    if (!match || !match[2]) return value;
    const result = fromTemplate(match[2]) ?? translateDate(match[2]);
    return result === undefined ? value : match[1] + result + match[3];
}

// A name holding ", " or a separator ("Smith, Ann", "Paul | Work") would be cut where labels are cut, and its pieces
// looked up: it stands in the label as one placeholder while the label is translated.
const nameToken = /^\{\$corsuName\d+\}$/;

function maskNames(core: string, names: Set<string>): [string, string[]] {
    const masked: string[] = [];
    const cut = Array.from(names).filter(name => name.includes(", ") || separators.test(name))
        .sort((a, b) => b.length - a.length);
    let text = core;
    for (const name of cut) {
        const pattern = new RegExp(`(?<![\\p{L}\\p{N}])${escape(name)}(?![\\p{L}\\p{N}])`, "gu");
        text = text.replace(pattern, () => {
            masked.push(name);
            return `{$corsuName${masked.length}}`;
        });
    }
    return [text, masked];
}

export function translateLabel(value: string, names: Set<string> = new Set()): string {
    const match = value.match(/^(\s*)(.*?)(\s*)$/s);
    if (!match || !match[2]) return value;
    const [, before, core, after] = match;
    const folded = new Set(Array.from(names, name => normalize(name).toLowerCase()));
    if (folded.has(normalize(core).toLowerCase())) return value;
    const [masked, cut] = maskNames(core, names);
    keep = folded;
    let result: string | undefined;
    try {
        result = resolve(masked);
    } finally {
        keep = new Set();
    }
    if (result !== undefined) result = result.replace(/\{\$corsuName(\d+)\}/g, (token, n) => cut[Number(n) - 1] ?? token);
    if (result === undefined || result === core) return value;
    // Never change a placeholder or markup contract.
    const signature = (text: string) => (text.match(placeholder) ?? []).sort().join("\u0001");
    if (signature(core) !== signature(result)) return value;
    return before + result + after;
}

// With showOriginal, hovering a translated label shows the text it replaced: a way to learn while using Discord.
export function createTranslator(doc: Document, options: { showOriginal?: () => boolean; } = {}) {
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
        const translated = parent.closest(nameArea) || typingName(parent) ? nameLabel(value)
            : translateLabel(value, userNames(node));
        if (translated === value) return;
        originalText.set(node, { original: value, translated });
        node.data = translated;
    }

    function attributes(element: Element) {
        if (element.closest(contentArea) && !element.matches("input,textarea")) return;
        const inName = Boolean(element.closest(nameArea));
        for (const name of ["aria-label", "title", "placeholder"]) {
            const value = element.getAttribute(name);
            if (!value) continue;
            let saved = originalAttrs.get(element);
            if (saved?.get(name)?.translated === value) continue;
            const translated = inName ? nameLabel(value) : translateLabel(value, userNames(element));
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

    // Learning option: hovering a translated text shows, in a small bubble, the text it replaced.
    let bubble: HTMLDivElement | undefined;
    function originalOf(element: Element | null): string | undefined {
        for (let depth = 0; element && depth < 4; depth++, element = element.parentElement) {
            for (const child of Array.from(element.childNodes)) {
                const saved = child.nodeType === Node.TEXT_NODE ? originalText.get(child as Text) : undefined;
                if (saved && (child as Text).data === saved.translated) return saved.original.trim();
            }
            const attribute = originalAttrs.get(element)?.get("aria-label");
            if (attribute && element.getAttribute("aria-label") === attribute.translated) return attribute.original;
        }
        return undefined;
    }
    function hover(event: MouseEvent) {
        const original = options.showOriginal?.() ? originalOf(event.target as Element) : undefined;
        if (!original) { if (bubble) bubble.style.display = "none"; return; }
        if (!bubble) {
            bubble = doc.createElement("div");
            bubble.setAttribute("data-corsu-ignore", "");
            bubble.style.cssText = "position:fixed;z-index:100000;pointer-events:none;max-width:320px;padding:4px 8px;" +
                "border-radius:4px;font:13px/1.35 var(--font-primary, sans-serif);background:#111214;color:#dbdee1;" +
                "box-shadow:0 2px 8px rgba(0,0,0,.35)";
            doc.body.append(bubble);
        }
        bubble.textContent = original;
        bubble.style.display = "block";
        const x = Math.min(event.clientX + 12, doc.documentElement.clientWidth - bubble.offsetWidth - 8);
        const y = event.clientY + 18 + bubble.offsetHeight > doc.documentElement.clientHeight ? event.clientY - bubble.offsetHeight - 10 : event.clientY + 18;
        bubble.style.left = x + "px";
        bubble.style.top = y + "px";
    }

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
            doc.addEventListener("mousemove", hover, { passive: true });
            observer.observe(doc.documentElement, {
                subtree: true, childList: true, characterData: true,
                attributes: true, attributeFilter: ["aria-label", "title", "placeholder"]
            });
        },
        stop() {
            if (!running) return;
            running = false;
            observer.disconnect();
            doc.removeEventListener("mousemove", hover);
            bubble?.remove();
            bubble = undefined;
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
