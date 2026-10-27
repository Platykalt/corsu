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

// Which translator and which dictionary a running Discord has loaded, for the diagnostic: Discord keeps a plugin built
// earlier until it restarts, so a report can come from an older build than the one installed. The revision changes
// with this file's way of reading the page; the fingerprint is computed from the dictionary itself (its entry count
// and two sums of FNV-1a hashes over each key and value's UTF-16 code units, which do not depend on the order of the
// entries), so it can be compared with the dictionary.json of any build.
export const translatorRevision = "2026-10-composer-1";
let fingerprint: string | undefined;

export function dictionaryFingerprint(): string {
    if (fingerprint) return fingerprint;
    let sum = 0, mixed = 0, count = 0;
    for (const [key, value] of Object.entries(words)) {
        let hash = 0x811c9dc5;
        const entry = key + "\u0000" + value;
        for (let i = 0; i < entry.length; i++) hash = Math.imul(hash ^ entry.charCodeAt(i), 0x01000193) >>> 0;
        sum = (sum + hash) >>> 0;
        mixed = (mixed ^ Math.imul(hash, 0x9e3779b1)) >>> 0;
        count++;
    }
    const hex = (n: number) => n.toString(16).padStart(8, "0");
    return fingerprint = `${count}-${hex(sum)}${hex(mixed)}`;
}
// What people write is never touched: messages, bios, statuses, embeds and the text being typed.
const contentArea = [
    // Code blocks sit inside messages (markup); a bare <pre> elsewhere is an interface tooltip.
    "script", "style", "textarea", "input", "[contenteditable]", "[data-corsu-ignore]",
    '[id^="message-content"]', '[id^="message-accessories"]', '[class*="messageContent"]', '[class*="markup"]',
    '[class*="embed"]', '[class*="attachment"]', '[class*="topic"]', '[class*="customStatus"]', '[class*="bio"]',
    '[class*="aboutMe"]', '[class*="forumPost"]', '[class*="searchResult"]',
    // The status people write on a voice channel ("On joue ce soir").
    '[class*="voiceChannelStatus"]'
].join(",");
// A text field is where people type, but its own placeholder and label are Discord's ("Rechercher" on the Friends
// page, "Rechercher {name}" over a conversation): those attributes of the field itself are translated, never what is
// typed in it. A field inside what people write (a message, a bio) is left alone.
const fieldSelector = 'input,textarea,[contenteditable]:not([contenteditable="false"])';
const isField = (element: Element) => element.matches(fieldSelector) && !element.parentElement?.closest(contentArea);
// Slate, the editor of Discord's text fields, draws the placeholder of an empty field inside the field, in a span it
// marks data-slate-placeholder (not editable): Discord's text, not what is typed. Discord's message composer
// (SlateTextArea) draws its own placeholder ("Envoyer un message à @Ron") in a <div data-slate-placeholder> BESIDE
// the editor, outside any content area: Discord's text too (0.28.0 and 0.28.1 took it for typed content).
const slatePlaceholder = "[data-slate-placeholder]";

function inContent(element: Element): boolean {
    const placeholder = element.closest(slatePlaceholder);
    if (!placeholder) return Boolean(element.closest(contentArea));
    const editor = placeholder.parentElement?.closest(contentArea);
    return Boolean(editor) && !isField(editor!);
}

// A placeholder (an attribute, a Slate placeholder, an element named so) or a text field's label is written whole by
// Discord, around the name it inserts: there a template applies whatever it captures ("Rechercher {name}" with
// "EnzoParisi, Moz_One", a name Discord composes from a group's members and that no record holds as such).
const placeholderArea = `${slatePlaceholder},[class*="placeholder"],[class*="Placeholder"]`;
// Names of people, servers, channels and roles: only labels around them change (templates like "Send a message in
// {channel}" and dates); a name itself is never looked up in the dictionary. Kept as a list so that the diagnostic
// can tell which of these rules kept a text as it was.
const nameRules = [
    '[id^="chat-messages"]', '[id^="message-reply-context"]',
    '[class*="username"]', '[class*="displayName"]', '[class*="nickname"]', '[class*="globalName"]',
    '[class*="channelName"]', '[class*="guildName"]', '[class*="roleName"]', '[class*="activity"]',
    '[class*="member"] [class*="name"]', 'a[href^="/channels/"]:not([href="/channels/@me"])', '[class*="threadName"]'
];
const nameArea = nameRules.join(",");

// What people chose themselves (user names, display names, server nicknames, server, channel and role names) is
// recognised by where it comes from, not by its look: Discord renders it from its own records, which the React
// components above the text hold in their props (a user, member, guild, channel or role object, with a numeric id).
// A text equal to one of those names is never looked up, even when it is also a dictionary word ("Work", "Error"),
// and inside a label or sentence only the interface text around it changes.
const snowflake = /^\d{15,21}$/;
const nameFields = ["username", "globalName", "global_name", "nick", "nickname", "displayName", "display_name", "name"];
// Discord's records: a channel keeps its DM recipients' ids in `recipients` and the people themselves in
// `rawRecipients`, with group DM nicknames in `nicks` (by user id); a server member is identified by `userId`.
// The channel someone is in a call in comes as `voiceChannel` (`voiceStatusChannel` in the member list).
const holders = ["user", "author", "member", "guildMember", "guild", "channel", "role", "recipient", "recipients",
    "rawRecipients", "users", "members", "message", "currentUser", "otherUser", "friend", "relationship", "entry", "item",
    "voiceChannel", "voiceStatusChannel"];
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

// What people and applications show as their activity is theirs too: a game, a song or a stream title, the
// details and state a game or an application writes (rich presence), the text of the images it shows, the buttons it
// adds, and a custom status. Discord's activity status (ActivityStatus) receives these records as `activities`, and
// its parts as `activity` (one game or song), `customStatusActivity` (the custom status) or `game` (the game being
// streamed). Discord only adds its own labels around them ("Playing {game}", "In a call").
const activityKeys = ["activities", "activity", "customStatusActivity", "game"];
const activityFields = ["name", "details", "state"];

function collectActivity(value: unknown, into: Set<string>, depth: number) {
    if (!value || typeof value !== "object" || depth > 2) return;
    if (Array.isArray(value)) {
        for (const item of value.slice(0, 20)) collectActivity(item, into, depth + 1);
        return;
    }
    const record = value as Record<string, any>;
    if (typeof record.type !== "number" && typeof record.name !== "string") return;
    const add = (text: unknown) => { if (typeof text === "string" && text.trim()) into.add(text.trim()); };
    for (const field of activityFields) add(record[field]);
    // Discord shows a song's artists, separated by "; " in the record, with ", " instead.
    if (typeof record.state === "string" && record.state.includes("; ")) add(record.state.split("; ").join(", "));
    add(record.assets?.large_text); add(record.assets?.small_text);
    add(record.emoji?.name);
    if (Array.isArray(record.buttons)) for (const button of record.buttons.slice(0, 4)) add(button?.label ?? button);
}

// Components that hold someone's activity records sit a few levels above the activity status text; the records of a
// whole list (or of the page) are further up and say nothing about this node.
const activityDepth = 20;
const hasActivity = (props: any) => activityKeys.some(key => Object.hasOwn(props, key))
    || Object.hasOwn(props, "voiceChannel") || Object.hasOwn(props, "voiceStatusChannel");
// A component given one activity (`activity`, `customStatusActivity`, `game`) draws that activity: a card in a
// profile, the status line itself. What it draws a few levels below is that activity, whatever class it has.
const presenceDepth = 8;
const hasOneActivity = (props: any) => ["activity", "customStatusActivity", "game"].some(key => Object.hasOwn(props, key));

// What the components that render this node know: the names in their records and the texts of the activities they
// show (`names`), whether one of them is close enough to be the activity status itself (`activity`), and whether the
// node is drawn by a component given one activity (`presence`).
export function origin(node: Node | null): { names: Set<string>; activity: boolean; presence: boolean; } {
    const names = new Set<string>();
    let activity = false, presence = false;
    let host: Node | null = node;
    while (host && !fiberOf(host)) host = host.parentNode;
    if (!host) return { names, activity, presence };
    for (let fiber of currentFibers(host, fiberOf(host))) {
        for (let depth = 0; fiber && depth < 40; depth++, fiber = fiber.return) {
            const props = fiber.memoizedProps;
            if (!props || typeof props !== "object") continue;
            collectNames(props, names, 0);
            for (const key of ["user", "member", "channel", "guild"]) {
                if (Object.hasOwn(props, key)) collectNames(props[key], names, 0);
            }
            for (const key of activityKeys) {
                if (Object.hasOwn(props, key)) collectActivity(props[key], names, 0);
            }
            if (depth < activityDepth && hasActivity(props)) activity = true;
            if (depth < presenceDepth && hasOneActivity(props)) presence = true;
        }
    }
    return { names, activity, presence };
}

// In an activity or presence area, a text is translated only when it is one of the labels Discord itself writes
// there. Anything else may come from the activity even when it differs from the records: Discord can show a game
// under another name than its record's (a detectable application's name, a renamed game), so "Control" there is kept
// even when the record says "control.exe". The labels are those of Discord's activity components (its public web
// client, October 2026: the status line, the call and stage labels, the activity cards and their buttons), in French
// and English; the templates take any value, since the value itself is copied as it is.
const activityLabels = new Set([
    "Dans un appel", "In a call", "Dans un salon vocal", "In voice", "In a Voice Channel", "Dans une conférence",
    "In a stage", "Dans un salon de conférence", "In a Stage Channel", "Écoute une conférence", "Listening to a Stage",
    "En pleine activité", "In Activity", "En partage d'écran", "Sharing their screen", "En direct", "Streaming", "Live",
    "Live Now", "En stream depuis la console", "Streaming from console", "Joue à", "Playing", "Écoute", "Listening to",
    "Regarde", "Watching", "Joue en partie classée à", "Competing in", "A récemment joué à", "Recently Played",
    "En cours", "Active Now", "Rejoindre", "Join", "Demander à rejoindre", "Ask to Join", "Regarder", "Watch", "Écouter",
    "Listen In", "Jouer", "Play", "Quitter l'activité", "Leave Activity", "Invitation à rejoindre", "Invite to Join",
    "Rejoindre le salon vocal", "Join Voice", "Rejoint", "Joined", "Voir le profil du jeu", "View Game Profile",
    "Lancer le jeu", "Launch Game", "Essayer le jeu", "Try Game", "Le plus joué", "Most played", "Nouveau joueur",
    "New Player", "Nouvelle sortie", "New Release"
].map(label => normalize(label).toLowerCase()));
const activityTemplates = new Set([
    "Joue à {}", "Playing {}", "Écoute {}", "Listening to {}", "Regarde {}", "Watching {}", "Participant à : {}",
    "Competing in {}", "Streame {}", "Streaming {}", "En direct sur {}", "Live on {}", "Joue sur {}", "Playing on {}",
    "Écoute quelque chose sur {}", "Listening on {}", "Regarde sur {}", "Watching on {}", "Joue en compétition sur {}",
    "Competing on {}", "Stream de {}", "Stream {}", "Dans un salon vocal, {}", "In Voice, {}", "Dans un appel ({})",
    "In a call ({})", "({} sur {})", "({} of {})", "Joue depuis {} minutes", "Playing for {} minutes",
    "Joue depuis {} heures", "Playing for {} hours"
].map(template => normalize(template).toLowerCase()));
const templateShape = (key: string) => normalize(key).replace(/\u0000\d+\u0000/g, "{}").toLowerCase();

// Set by translateLabel for one label of an activity or presence area: only the labels above apply.
let strict = false;
// Set by label() for one placeholder or text field label (see placeholderArea): templates take any value.
let loose = false;
const activityLabel = (text: string) => activityLabels.has(normalize(text).trim().toLowerCase());

// The names the components that render this node know about, with the activities they show; empty outside React
// (and in tests without it).
export function userNames(node: Node | null): Set<string> {
    return origin(node).names;
}

// Discord's activity status in a list (direct messages, friends, members, the account panel): the line under a
// person's name. The activity texts are inside a name rule ([class*="activity"], or the link of a direct message), but
// besides the values from the records it holds Discord's own labels: "In a call", "In a voice channel", "Playing
// {game}" in its tooltip. When the React records show where the line comes from, those labels (and only those, see
// activityLabels) are translated, every value from the records and every name staying as written; without them (or in
// the person's name above) only templates and dates apply, as before.
const statusArea = '[class*="activity"],[class*="subText"],[class*="subtext"],[class*="statusText"]';
const nameHolder = '[class*="username"],[class*="displayName"],[class*="nickname"],[class*="globalName"],' +
    '[class*="channelName"],[class*="guildName"],[class*="roleName"],[class*="threadName"],[class*="nameTag"],[class*="name_"]';

// Where a text sits, from the React records above it and the page around it: in an activity or presence area
// (`presence`: the activity status line with its records, or what a component given one activity draws), in a name
// (`name`: a name rule, or a name holder inside the activity line), with the names and activity values to keep.
type Place = { presence: boolean; name: boolean; names: Set<string>; };

function place(element: Element, node: Node): Place {
    const found = origin(node);
    const scope = element.closest(statusArea);
    // A name inside the line (the link of a direct message around it is named "channelNameFade", so only what is
    // between the text and the line counts).
    const holder = element.closest(nameHolder);
    const presence = found.presence || Boolean(scope && found.activity);
    const name = presence ? Boolean(holder && (!scope || scope.contains(holder))) : Boolean(element.closest(nameArea));
    return { presence, name, names: found.names };
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
    // A game can be called "Mars 2": in an activity area only Discord's relative times are read as dates.
    if (strict) return undefined;
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
type Template = { pattern: RegExp; value: string; fixed: number; parts: string[]; key: string; };
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
        const entry = { pattern, fixed, parts, key, value: value.replace(/\u0000(\d+)\u0000/g, (_, n) => `\u0000${order.indexOf(Number(n)) + 1}\u0000`) };
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
    for (const { pattern, value, fixed, key: source } of candidates) {
        const match = key.match(pattern);
        // Too little fixed text ("Send {x}") would match labels that only start the same way; such short templates
        // apply only when what they capture is a number ("{count} mentions").
        // A value Discord's records give for this node (a name, a game) also counts: "Playing {game}" with the game.
        // In an activity area a template applies only when it is one of Discord's activity labels or when what it
        // captures is known: "{a} de {b}" must not take a game called "Bobby de Paris".
        const known = () => match!.slice(1).every(group => /^[\d\s.,\u00a0\u202f+]+$/.test(group) || kept(group) || nameToken.test(group.trim()));
        // Discord's own activity templates there take any value: "Joue à {game}" with a game shown under another name.
        const discord = match && strict && activityTemplates.has(templateShape(source));
        if (match && strict && !discord && !known()) continue;
        // A placeholder is Discord's text around the value it inserts, so there the value can be anything.
        if (match && fixed < 12 && !discord && !loose && !known()) continue;
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
    if (strict && !activityLabel(text)) return undefined;
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

// Discord's system messages sit in the message list, inside [id^="chat-messages"] (a name rule), so only templates
// and dates applied to them and a pin notice with its "see all pinned" link stayed in French. These exact interface
// phrases are the whole text of their node, so they are translated as written: this is the primary path, used when
// the author is a separate element (a username rule, kept as written) and the text node holds no name. The link and
// the sentence may be one node or two, so all three forms are listed. A real message with the same words is in a
// content area and never reaches here.
const systemLabels = new Set([
    "a épinglé un message dans ce salon.",
    "a épinglé un message dans ce salon. Voir tous les messages épinglés.",
    "Voir tous les messages épinglés.",
    // Group DM notices: "{username} a ajouté {otherUsername} au groupe.", "… a retiré … du groupe.", "… a quitté le
    // groupe.", each name its own element, so these fragments are whole text nodes between them.
    "a ajouté", "au groupe.", "a retiré", "du groupe.", "a quitté le groupe.",
    // The pin notice as Discord's web client draws it (October 2026): yIDvPL "{username} a épinglé [un message] dans
    // ce salon. Voir tous les [messages épinglés].", lD5tup without the second link, R7vZGZ without the first; each
    // [link] is its own element.
    "a épinglé", "un message", "dans ce salon. Voir tous les", "messages épinglés", "dans ce salon.",
    "a épinglé un message dans ce salon. Voir tous les",
    // A group renamed or its icon changed: geP3rU "{username} a changé le nom du groupe : {name}. [Modifier le
    // groupe]", AI1ZZr "… a supprimé le nom de groupe personnalisé. [Modifier le groupe]", OEdU6X "… a changé l'icône
    // du groupe."; oItgEw and SOQ4hJ for a channel or a forum post renamed.
    "a changé le nom du groupe :", "a supprimé le nom de groupe personnalisé.", "Modifier le groupe",
    "a changé l'icône du groupe.", "a changé le nom du salon :", "a changé le titre du post :"
].map(label => normalize(label).toLowerCase()));
// System messages are rows of the message list; elsewhere in a name area these phrases are never looked up.
const messageRow = '[id^="chat-messages"]';

// Inside names only templates and dates apply, so a name that happens to be a dictionary word stays as it is. A
// system message (a pin notice and its link, see systemLabels) is interface text, not a name, so it is looked up.
// If Discord instead draws the author's name inside the sentence's own text node, the exact phrase above no longer
// matches; the fallback below then applies a template ("{name} a épinglé un message dans ce salon…" in the
// dictionary), which keeps the name as a protected value and translates only the fixed parts.
function nameLabel(value: string, presence = false, names: Set<string> = new Set(), system = false): string {
    const match = value.match(/^(\s*)(.*?)(\s*)$/s);
    if (!match || !match[2]) return value;
    let result: string | undefined;
    // A name its records hold is never a system label, even one written "a ajouté".
    const label = normalize(match[2]).toLowerCase();
    if (system && !presence && systemLabels.has(label) && ![...names].some(name => normalize(name.trim()).toLowerCase() === label)) {
        result = resolve(match[2], false);
    }
    if (result === undefined) {
        strict = presence;
        try {
            result = fromTemplate(match[2]) ?? translateDate(match[2]);
        } finally {
            strict = false;
        }
    }
    return result === undefined ? value : match[1] + result + match[3];
}

// A name holding ", " or a separator ("Smith, Ann", "Paul | Work") would be cut where labels are cut, and its pieces
// looked up: it stands in the label as one placeholder while the label is translated.
const nameToken = /^\{\$corsuName\d+\}$/;

function maskNames(core: string, names: Set<string>): [string, string[]] {
    const masked: string[] = [];
    // Names and activity values of several words are masked too, so that a value inside a longer text ("Dans un
    // appel (1 sur 4)" where "Dans un appel" is the activity's state) is never read as the start of a template.
    const cut = Array.from(names).filter(name => name.includes(", ") || separators.test(name) || /\S\s+\S/.test(name.trim()))
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

// `presence`: the label is in an activity or presence area, where only Discord's activity labels apply.
export function translateLabel(value: string, names: Set<string> = new Set(), presence = false): string {
    const match = value.match(/^(\s*)(.*?)(\s*)$/s);
    if (!match || !match[2]) return value;
    const [, before, core, after] = match;
    const folded = new Set(Array.from(names, name => normalize(name).toLowerCase()));
    if (folded.has(normalize(core).toLowerCase())) return value;
    const [masked, cut] = maskNames(core, names);
    keep = folded;
    strict = presence;
    let result: string | undefined;
    try {
        result = resolve(masked);
    } finally {
        keep = new Set();
        strict = false;
    }
    if (result !== undefined) result = result.replace(/\{\$corsuName(\d+)\}/g, (token, n) => cut[Number(n) - 1] ?? token);
    if (result === undefined || result === core) return value;
    // Never change a placeholder or markup contract.
    const signature = (text: string) => (text.match(placeholder) ?? []).sort().join("\u0001");
    if (signature(core) !== signature(result)) return value;
    return before + result + after;
}

// A text or attribute of `element`: inside a name rule only templates and dates apply; in an activity or presence
// area only Discord's activity labels; elsewhere the label is translated around the names and activities it holds.
// `placeholder`: the text is a placeholder or a text field's label, where templates take any value (not in a name
// rule nor in an activity or presence area, whose own rules stay).
function label(value: string, element: Element, node: Node, placeholder = false): string {
    const where = place(element, node);
    if (where.name) return nameLabel(value, where.presence, where.names, Boolean(element.closest(messageRow)));
    if (!where.presence) {
        const verb = dialogVerb(value, element, where.names);
        if (verb !== undefined) return verb;
    }
    loose = placeholder && !where.presence;
    try {
        return translateLabel(value, where.names, where.presence);
    } finally {
        loose = false;
    }
}

// One French label for several actions. Discord's French says "Supprimer" both for Delete (a message, a channel, a
// server: Corsican "Squassà", erase) and for Remove (an attachment, a role or a person from a list: "Caccià", take
// out); its English keeps them apart ("Delete", "Remove"). The dictionary gives the general "Caccià". In a dialog, the
// button repeats the action its title names ("Supprimer le message" over a "Supprimer" button), so the button takes
// the verb the title's translation starts with when it is one of these. Elsewhere, or with a title that starts with
// another word, the dictionary applies; a correction made in the Corsu app always wins. A name or activity value
// equal to the label stays as written, and a title inside what people write or in a name never decides.
export const dialogVerbs: Record<string, string[]> = { "Supprimer": ["Squassà", "Caccià"] };
const dialogArea = '[role="dialog"],[role="alertdialog"]';
const dialogTitle = 'h1,h2,h3,[class*="title"],[class*="Title"]';

function dialogVerb(value: string, element: Element, names: Set<string>): string | undefined {
    const match = value.match(/^(\s*)(.*?)(\s*)$/s);
    const key = normalize(match?.[2] ?? "");
    const verbs = dialogVerbs[key];
    if (!verbs || Object.hasOwn(corrections, key)) return undefined;
    if (Array.from(names).some(name => normalize(name).trim().toLowerCase() === key.toLowerCase())) return undefined;
    const dialog = element.closest(dialogArea);
    if (!dialog) return undefined;
    for (const title of Array.from(dialog.querySelectorAll(dialogTitle))) {
        if (title.contains(element) || element.contains(title) || title.closest(contentArea) || title.closest(nameArea)) continue;
        const shown = normalize(title.textContent ?? "").trim();
        if (!shown) continue;
        // The title may already be translated (it comes first in the page) or not yet.
        for (const text of [shown, resolve(shown)]) {
            const verb = text && verbs.find(candidate => text.toLowerCase().startsWith(candidate.toLowerCase() + " "));
            if (verb) return match![1] + verb + match![3];
        }
        return undefined;
    }
    return undefined;
}

type Finding = { kind: string; rule?: string; text?: string; };

// With showOriginal, hovering a translated label shows the text it replaced: a way to learn while using Discord.
export function createTranslator(doc: Document, options: { showOriginal?: () => boolean; } = {}) {
    const originalText = new WeakMap<Text, { original: string; translated: string; }>();
    const originalAttrs = new WeakMap<Element, Map<string, { original: string; translated: string; }>>();
    const pending = new Set<Node>();
    let scheduled = false;
    let running = false;

    function text(node: Text) {
        const parent = node.parentElement;
        if (!parent || inContent(parent)) return;
        const value = node.data;
        const previous = originalText.get(node);
        if (previous && previous.translated === value) return;
        const translated = typingName(parent) ? nameLabel(value)
            : label(value, parent, node, Boolean(parent.closest(placeholderArea)));
        if (translated === value) return;
        originalText.set(node, { original: value, translated });
        node.data = translated;
    }

    function attributes(element: Element) {
        const field = isField(element);
        if (!field && element.closest(contentArea)) return;
        for (const name of ["aria-label", "title", "placeholder"]) {
            const value = element.getAttribute(name);
            if (!value) continue;
            let saved = originalAttrs.get(element);
            if (saved?.get(name)?.translated === value) continue;
            const translated = label(value, element, element, field || name === "placeholder");
            if (translated === value) continue;
            if (!saved) originalAttrs.set(element, saved = new Map());
            saved.set(name, { original: value, translated });
            element.setAttribute(name, translated);
        }
    }

    // A part of the page left out as what people write: only a text field's own attributes and the placeholder Slate
    // draws in an empty field are read there.
    function shielded(element: Element) {
        if (isField(element)) attributes(element);
        const spans = element.matches(slatePlaceholder) ? [element] : Array.from(element.querySelectorAll(slatePlaceholder));
        for (const span of spans) {
            if (inContent(span)) continue;
            const walker = doc.createTreeWalker(span, NodeFilter.SHOW_TEXT);
            let node: Node | null;
            while ((node = walker.nextNode())) text(node as Text);
        }
    }

    function walk(root: Node) {
        if (!root.isConnected) return;
        if (root.nodeType === Node.TEXT_NODE) { text(root as Text); return; }
        if (root instanceof Element) {
            if (root.closest(contentArea)) { shielded(root); return; }
            attributes(root);
        }
        const left: Element[] = [];
        const walker = doc.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
            acceptNode(node) {
                if (!(node instanceof Element && node.matches(contentArea))) return NodeFilter.FILTER_ACCEPT;
                left.push(node);
                return NodeFilter.FILTER_REJECT;
            }
        });
        let node: Node | null;
        while ((node = walker.nextNode())) {
            if (node.nodeType === Node.TEXT_NODE) text(node as Text);
            else attributes(node as Element);
        }
        for (const element of left) shielded(element);
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

    // Diagnostic (off unless the hidden reportMissing option is on): the visible texts and interface attributes that
    // were left as they are, each with the reason. What people write or choose never shows in it, and this is decided
    // by where a text comes from, not by its words: a name can be a dictionary word ("Work", "Error", "Message").
    // - text inside what people write (messages, bios, statuses, embeds, the text being typed) is only counted;
    // - a text equal to a name or an activity value from the React records around it is only counted;
    // - a text from a personal area is never given, even when the dictionary knows it: names (the name rules, the
    //   names in the typing indicator), the activity and presence areas (a game can be shown under another name than
    //   its record's), any element whose class speaks of a name, a tag, a status, an activity, an account or pronouns,
    //   and a heading above records of people, servers or channels (a conversation's title). Only the kind of finding
    //   and the rule are given, except for Discord's own activity labels (activityLabels), which are given as they are;
    // - any other text is given with every name and activity value from the records around it replaced by {name},
    //   whole or word by word (so that part of a name does not show either), then word by word: a word that no
    //   dictionary entry uses becomes {?} and digits become #, and a text where such words are the majority is only
    //   counted. The report is only written to the local console, and only when asked for.
    // Each finding has a kind:
    //   missing      not in the dictionary;
    //   unapplied    in the dictionary, nothing protects it, yet it is shown untranslated (never seen by the translator);
    //   excluded     in the dictionary, kept as it is by a protection rule (named in `rule`), possibly wrongly;
    //   template     looks like one of the dictionary's templates whose pattern did not match (the template is given);
    //   stale        the page changed a text after it was translated and the change was not translated again.
    // The report also says which translator and dictionary are loaded, and counts what was rightly left alone.
    const reported = new Set<string>();
    const looksLikeText = /[éèêàçùûôîâ]|\b(le|la|les|des|un|une|de|du|et|à|en|pour|the|and|to|of|your|in|on)\b|^[A-Z][a-zé]+$/i;
    const personalArea = [...nameRules, statusArea, nameHolder, '[class*="Name"]', '[class*="nick"]', '[class*="Nick"]',
        '[class*="tag"]', '[class*="Tag"]', '[class*="status"]', '[class*="Status"]', '[class*="Activity"]',
        '[class*="presence"]', '[class*="Presence"]', '[class*="account"]', '[class*="Account"]', '[class*="pronoun"]',
        '[class*="Pronoun"]'].join(",");
    const heading = 'h1,h2,h3,h4,[class*="title"],[class*="Title"],[class*="header"],[class*="Header"]';

    function redact(text: string, names: Set<string>): string | undefined {
        let result = text;
        const values = Array.from(names).sort((a, b) => b.length - a.length);
        for (const name of values) {
            if (name.length < 2) continue;
            result = result.replace(new RegExp(`(?<![\\p{L}\\p{N}])${escape(name)}(?![\\p{L}\\p{N}])`, "giu"), "{name}");
        }
        // Then each word of a name or value on its own: a label can show part of a name ("Work" of "Work Error").
        const parts = new Set(values.flatMap(name => normalize(name).toLowerCase().match(/[\p{L}\p{N}]{2,}/gu) ?? []));
        if (parts.size) {
            result = result.replace(/\{name\}|[\p{L}\p{N}]+/gu, word => parts.has(normalize(word).toLowerCase()) ? "{name}" : word);
        }
        return scrub(result);
    }

    // The words of the dictionary's own entries (French and English, lower case), read once.
    let vocabulary: Set<string> | undefined;
    function known(word: string) {
        if (!vocabulary) {
            vocabulary = new Set();
            for (const key of [...Object.keys(words), ...Object.keys(corrections)]) {
                for (const found of normalize(key).toLowerCase().match(/\p{L}+/gu) ?? []) vocabulary.add(found);
            }
        }
        return vocabulary.has(word.toLowerCase());
    }

    // A text as the report may give it: words no entry uses become {?}, digits #; undefined when most words are unknown.
    function scrub(text: string): string | undefined {
        let total = 0, unknown = 0;
        const result = text.replace(/\{name\}|\{\d+\}/g, found => `\u0001${found}\u0001`).split("\u0001").map(part =>
            /^\{(name|\d+)\}$/.test(part) ? part : normalize(part).replace(/\p{L}+/gu, word => {
                total++;
                if (known(word)) return word;
                unknown++;
                return "{?}";
            }).replace(/\p{N}/gu, "#")).join("");
        return total && unknown * 2 >= total ? undefined : result;
    }

    // The template a text nearly matches: one indexed under its first or last word whose fixed parts all appear in it,
    // in order. Given as the template, with {1}, {2}… where the values go.
    function nearTemplate(text: string): string | undefined {
        const key = normalize(text).toLowerCase();
        const list = key.trim().split(/\s+/);
        const candidates = [...(templateIndex().get("^" + list[0]) ?? []), ...(templateIndex().get("$" + list[list.length - 1]) ?? [])];
        for (const template of candidates) {
            let at = 0;
            const inOrder = template.parts.every(part => {
                const found = key.indexOf(part.toLowerCase().trim(), at);
                if (found < 0) return false;
                at = found + part.trim().length;
                return true;
            });
            if (inOrder) return template.key.replace(/\u0000(\d+)\u0000/g, "{$1}");
        }
        return undefined;
    }

    // How a text the dictionary knows can be given: as it is when it is an entry (give or take case, final
    // punctuation, a count), as its template when values are inserted; undefined when it is only found piece by piece,
    // since the other pieces may be names.
    function inCatalogue(text: string): string | undefined {
        if (fromTemplate(text) !== undefined) return nearTemplate(text);
        return resolve(text, false) !== undefined ? text : undefined;
    }

    // In a personal area, only Discord's own activity labels and templates (without their values) may be given.
    function discordLabel(text: string): string | undefined {
        if (activityLabel(text)) return text;
        const template = nearTemplate(text);
        return template && activityTemplates.has(normalize(template).replace(/\{\d+\}/g, "{}").toLowerCase()) ? template : undefined;
    }

    function rule(element: Element, where: Place, typing: boolean): string {
        return (where.presence ? "activity origin" : undefined) ?? nameRules.find(selector => element.closest(selector))
            ?? (typing ? "typing indicator" : "personal area");
    }

    // `saved`: what the translator last wrote there, if it ever did.
    function classify(shown: string, element: Element, node: Node, saved: string | undefined, findings: Finding[],
        counts: Record<string, number>) {
        const text = shown.trim();
        if (text.length < 2 || text.length > 160 || !/\p{L}{2}/u.test(text)) return;
        const count = (kind: string) => { counts[kind] = (counts[kind] ?? 0) + 1; };
        if (element.closest(contentArea)) return count("userContent");
        if (saved === shown) return count("translated");
        const where = place(element, node);
        const { names } = where;
        const folded = new Set(Array.from(names, name => normalize(name).toLowerCase()));
        if (folded.has(normalize(text).toLowerCase())) return count("userValue");
        const typing = typingName(element);
        const personal = where.name || where.presence || typing || Boolean(element.closest(personalArea))
            || (names.size > 0 && Boolean(element.closest(heading)));
        const lookedUp = translateLabel(text, names);
        const applied = typing ? nameLabel(text) : label(text, element, node);
        const add = (finding: Finding) => {
            const id = finding.kind + "\u0001" + (finding.rule ?? "") + "\u0001" + (finding.text ?? "");
            count(finding.kind);
            if (reported.has(id)) return;
            reported.add(id);
            findings.push(finding);
        };
        if (lookedUp !== text) {
            if (applied !== text) {
                const kind = saved === undefined ? "unapplied" : "stale";
                if (personal) return add({ kind, rule: rule(element, where, typing), text: discordLabel(text) });
                const shape = inCatalogue(text);
                return add({ kind, text: shape !== undefined && shape !== text ? redact(shape, names) : redact(text, names) });
            }
            // A protection kept it: a nickname, a server name or a game can be a dictionary word, so only the rule is given.
            return add({ kind: "excluded", rule: rule(element, where, typing) });
        }
        if (personal) return count("unknownInName");
        const template = nearTemplate(text);
        if (template) return add({ kind: "template", text: template });
        if (!looksLikeText.test(text)) return;
        const given = redact(text, names);
        if (given === undefined) return count("missingUnreadable");
        add({ kind: "missing", text: given });
    }

    function report() {
        const findings: Finding[] = [];
        const counts: Record<string, number> = {};
        const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
        let node: Node | null;
        while ((node = walker.nextNode())) {
            if (node.nodeType === Node.TEXT_NODE) {
                const parent = (node as Text).parentElement;
                if (!parent || parent.closest("script,style,[data-corsu-ignore]") || !(parent as HTMLElement).offsetParent) continue;
                classify((node as Text).data, parent, node, originalText.get(node as Text)?.translated, findings, counts);
            } else {
                const element = node as HTMLElement;
                if (element.closest("script,style,[data-corsu-ignore]") || !element.offsetParent) continue;
                for (const name of ["aria-label", "title"]) {
                    const value = element.getAttribute(name);
                    if (!value) continue;
                    classify(value, element, element, originalAttrs.get(element)?.get(name)?.translated, findings, counts);
                }
            }
        }
        return { revision: translatorRevision, dictionary: dictionaryFingerprint(), corrections: Object.keys(corrections).length,
            counts, findings };
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

// Texts Discord's page hands to the desktop app, which draws them itself, outside the page: the menu of the icon in
// the notification area (system tray: "Ouvrir Discord", "Rendre muet", "Quitter Discord"...) and, on Windows, the
// tooltips of the buttons under the taskbar preview during a call. The page translator never sees them, so the plugin
// translates them on their way out (patches in index.ts, on Discord's NativeUtils module). Only Discord's own labels
// are looked up; the product name (appName: "Discord", "Discord PTB", "Discord Canary") stays as it is.
export function translateNative(text: unknown, appName?: string): unknown {
    if (typeof text !== "string" || !text.trim()) return text;
    try {
        // "Ouvrir Discord PTB" is looked up as "Ouvrir Discord", then given its own name back.
        const other = appName && appName !== "Discord" && text.includes(appName);
        const source = other ? text.split(appName!).join("Discord") : text;
        const translated = translateLabel(source);
        if (translated === source) return text;
        if (!other) return translated;
        return translated.includes("Discord") ? translated.split("Discord").join(appName!) : text;
    } catch {
        return text;
    }
}

// The object Discord gives setSystemTrayStrings: {appName, openApp, mute, deafen, suppressed, serverMuted,
// serverDeafened, voiceSettings, checkForUpdates, acknowledgements, quitApp, closeHint}. A copy is returned.
export function translateTrayStrings<T>(strings: T): T {
    if (!strings || typeof strings !== "object") return strings;
    const source = strings as Record<string, unknown>;
    const appName = typeof source.appName === "string" ? source.appName : undefined;
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(source)) {
        result[key] = key === "appName" ? value : translateNative(value, appName);
    }
    return result as T;
}

// The list Discord gives setThumbarButtons: [{name, active, tooltip, flags}]. Only the tooltips change.
export function translateThumbarButtons<T>(buttons: T): T {
    if (!Array.isArray(buttons)) return buttons;
    return buttons.map(button => button && typeof button === "object" && typeof button.tooltip === "string"
        ? { ...button, tooltip: translateNative(button.tooltip) } : button) as T;
}

// Where these texts leave the page: Discord's NativeUtils module (found by the same text as Vencord's NoSystemBadge
// plugin). `\i` is Vencord's shorthand for an identifier. Checked against Discord's web client of October 2026
// (tests/e2e/check_discord_native.py).
export const nativePatch = {
    find: ",setSystemTrayApplications",
    trayStrings: /setSystemTrayStrings\((\i)\)\{/,
    thumbarButtons: /setThumbarButtons\((\i)\)\{/
};
