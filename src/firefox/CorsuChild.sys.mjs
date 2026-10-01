/*
 * Corsu: puts Corsican on the buttons, tabs and menus of Google's pages, where Google's own Corsican
 * interface falls back to French or English. Search results and page text are never changed.
 * Same matching rules as the Discord plugin and src/engine.py.
 */
import { words } from "resource://corsu/dictionary.mjs";

// Never touched: code, text being typed, and anything marked to ignore.
const protectedArea = ["script", "style", "pre", "code", "textarea", "[contenteditable]", "[data-corsu-ignore]"].join(",");
// The results area: only the interface labels listed below are translated there, never links or page text.
const resultsArea = "#search,#rso,#botstuff";
const resultLabels = new Set([
    "AI Overview", "Aperçu IA", "AI Mode", "Mode IA", "Show all", "Tout afficher", "Show more", "Afficher plus",
    "Show less", "Afficher moins", "People also ask", "Autres questions posées", "Related searches",
    "Recherches associées", "Short videos", "Vidéos courtes", "Videos", "Vidéos", "Images", "Feedback",
    "Commentaires", "Envoyer des commentaires", "Learn more", "En savoir plus", "Copy", "Copier", "Share",
    "Partager", "Listen", "Écouter", "More actions", "Plus d'actions", "Close", "Fermer",
    "AI can make mistakes, so double-check responses",
    "Vérifiez les réponses de l'IA, car elle peut faire des erreurs"
]);
// On Google's pages every short label outside the results is interface text.
const uiArea = "*";
const placeholder = /\{\s*[$-]?[\w.-]+(?:\([^{}]*\))?\s*\}|%(?:\d+\$)?[0-9]*\.?[0-9]*(?:ll|l|h)?[sdiufgexXop]|%[Ln]?\d+|\$\{[A-Za-z_]\w*\}|\{\d+\}/g;
const separators = /(\s*[   ]?[:—–/·|]\s+|\n|\s+-\s+)/;
const SHOW_ELEMENT = 1, SHOW_TEXT = 4, TEXT_NODE = 3, FILTER_ACCEPT = 1, FILTER_REJECT = 2;

function normalize(text) {
    return text.replace(/[’ʼ]/g, "'").replace(/[   ]/g, " ");
}

function direct(text) {
    const key = normalize(text);
    if (Object.hasOwn(words, key)) return words[key];
    const tokens = [];
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

function resolve(text, segments = true) {
    const found = direct(text);
    if (found !== undefined) return found;
    const trailing = text.match(/^(.*?)([\s ]*(?:\.\.\.|…|:|\?|!|;|\.))$/s);
    if (trailing && trailing[1].trim()) {
        const inner = resolve(trailing[1].trimEnd(), false);
        if (inner !== undefined) return inner + trailing[2];
    }
    const other = text[0] && text[0].toLowerCase() !== text[0]
        ? text[0].toLowerCase() + text.slice(1) : (text[0] || "").toUpperCase() + text.slice(1);
    if (other !== text) {
        const found2 = direct(other);
        if (found2 !== undefined) {
            return text[0] === text[0].toUpperCase()
                ? found2[0].toUpperCase() + found2.slice(1) : found2[0].toLowerCase() + found2.slice(1);
        }
    }
    if (!segments) return undefined;
    const parts = text.split(separators);
    if (parts.length < 3) return undefined;
    const output = [];
    for (const [index, part] of parts.entries()) {
        if (index % 2 || !/[^\W\d_]/u.test(part)) { output.push(part); continue; }
        const piece = resolve(part.trim(), false);
        if (piece === undefined) return undefined;
        output.push(part.replace(part.trim(), piece));
    }
    return output.join("");
}

function translateLabel(value) {
    const match = value.match(/^(\s*)(.*?)(\s*)$/s);
    if (!match || !match[2] || match[2].length > 100) return value;
    const [, before, core, after] = match;
    const result = resolve(core);
    if (result === undefined || result === core) return value;
    const signature = text => (text.match(placeholder) ?? []).sort().join("\u0001");
    if (signature(core) !== signature(result)) return value;
    return before + result + after;
}

export function translatePage(doc) {
        const win = doc.defaultView;
        if (!win || doc.documentElement.hasAttribute("data-corsu")) return;
        doc.documentElement.setAttribute("data-corsu", "on");
        const walk = root => {
            if (!root || !root.isConnected) return;
            const visit = node => {
                if (node.nodeType === TEXT_NODE) {
                    const parent = node.parentElement;
                    if (!parent || parent.closest(protectedArea) || !parent.closest(uiArea)) return;
                    if (parent.closest(resultsArea) &&
                        (parent.closest("a") || !resultLabels.has(normalize(node.data).trim()))) return;
                    const translated = translateLabel(node.data);
                    if (translated !== node.data) node.data = translated;
                } else if (node.matches && !node.closest(protectedArea) && node.matches(uiArea)) {
                    const inResults = node.closest(resultsArea);
                    for (const name of ["aria-label", "title", "placeholder"]) {
                        const value = node.getAttribute(name);
                        if (!value || (inResults && !resultLabels.has(normalize(value).trim()))) continue;
                        const translated = translateLabel(value);
                        if (translated !== value) node.setAttribute(name, translated);
                    }
                }
            };
            visit(root);
            const walker = doc.createTreeWalker(root, SHOW_ELEMENT | SHOW_TEXT, {
                acceptNode: node => node.matches && node.matches(protectedArea) ? FILTER_REJECT : FILTER_ACCEPT
            });
            let node;
            while ((node = walker.nextNode())) visit(node);
        };
        walk(doc.documentElement);
        const pending = new Set();
        let timer = null;
        const observer = new win.MutationObserver(records => {
            for (const record of records) {
                if (record.type === "childList") for (const node of record.addedNodes) pending.add(node);
                else pending.add(record.target);
            }
            if (pending.size && timer === null) {
                timer = win.setTimeout(() => {
                    timer = null;
                    const roots = Array.from(pending);
                    pending.clear();
                    for (const root of roots) walk(root);
                }, 50);
            }
        });
        observer.observe(doc.documentElement, {
            subtree: true, childList: true, characterData: true,
            attributes: true, attributeFilter: ["aria-label", "title", "placeholder"]
        });
    }
