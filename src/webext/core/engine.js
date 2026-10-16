/*
 * Corsu web extension: the translation engine shared by every site adapter.
 *
 * Nothing here talks to the network or to browser APIs. The engine receives a glossary (plain objects read from
 * glossary/*.json), an adapter (CSS selectors that say where the site's interface is and where user content is)
 * and a document, and changes only text that is both inside an interface zone and an exact glossary label.
 *
 * The DOM calls it makes are limited to closest(), matches(), querySelectorAll(), contains(), childNodes,
 * get/set/has/removeAttribute(), nodeType, data and isConnected, so the Node tests can run it on a tiny fake DOM.
 * Loaded as a classic content script (sets globalThis.CorsuWeb) or with require() under Node.
 */
(function (root, factory) {
    const api = factory();
    if (typeof module === "object" && module.exports) module.exports = api;
    else root.CorsuWeb = Object.assign(root.CorsuWeb || {}, api);
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";

    const TEXT_NODE = 3, ELEMENT_NODE = 1;
    // Never touched on any site: code, form values, editable text and anything the page marks as not to translate.
    const BUILTIN_NEVER = [
        "script", "style", "noscript", "template", "textarea", "input", "select", "option", "pre", "code", "kbd",
        "samp", "[contenteditable]", "[role=\"textbox\"]", "[translate=\"no\"]", "[data-corsu-ignore]"
    ].join(", ");
    // Longer texts are sentences or user content, not interface labels.
    const MAX_LENGTH = 120;
    const PLACEHOLDER = /\{([A-Za-z_][\w]*)\}/g;
    const TRAILING = /^(.*?)(\s*(?:\.\.\.|…|:))$/s;

    function normalize(text) {
        return text.replace(/[’ʼ]/g, "'").replace(/[   ]/g, " ").replace(/\s+/g, " ").trim();
    }

    /** Names of the {placeholders} of a glossary text, sorted, with repeats. */
    function placeholders(text) {
        return [...text.matchAll(PLACEHOLDER)].map(found => found[1]).sort();
    }

    function escapeRegExp(text) {
        return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    /** "{n} comments" -> /^(\d[\d.,\s]*[kKmM]?) comments$/; any other name matches any text. */
    function templatePattern(source) {
        // Same spacing rules as normalize(), without trimming the text between placeholders.
        const literal = text => escapeRegExp(text.replace(/[’ʼ]/g, "'").replace(/[   ]/g, " ")
            .replace(/\s+/g, " "));
        const names = [];
        let pattern = "", last = 0;
        for (const found of source.matchAll(PLACEHOLDER)) {
            pattern += literal(source.slice(last, found.index));
            pattern += found[1] === "n" ? "(\\d[\\d., ]*[kKmM]?)" : "(.+?)";
            names.push(found[1]);
            last = found.index + found[0].length;
        }
        pattern += literal(source.slice(last));
        return { regex: new RegExp("^" + pattern.trim() + "$", "s"), names };
    }

    /**
     * Merge glossaries into lookup tables. Earlier glossaries win: pass the site glossary before shared.json.
     * An entry with `within` only applies inside elements matching that selector; `exceptions` are checked first
     * and can give another translation (`co`) or keep the original (`skip: true`) in a given context.
     */
    function compileGlossary(...glossaries) {
        const exact = new Map(), templates = [], exceptions = [];
        for (const glossary of glossaries) {
            for (const entry of glossary.entries || []) {
                if (!entry.source || !entry.co) continue;
                const candidate = { co: entry.co, within: entry.within || null };
                if (PLACEHOLDER.test(entry.source)) {
                    PLACEHOLDER.lastIndex = 0;
                    templates.push(Object.assign(templatePattern(entry.source), candidate));
                    continue;
                }
                const key = normalize(entry.source);
                if (!exact.has(key)) exact.set(key, []);
                exact.get(key).push(candidate);
            }
            for (const exception of glossary.exceptions || []) {
                exceptions.push({ key: normalize(exception.source), within: exception.within,
                                  co: exception.co || null, skip: Boolean(exception.skip) });
            }
        }
        return { exact, templates, exceptions };
    }

    function applies(candidate, element) {
        return !candidate.within || Boolean(element && element.closest(candidate.within));
    }

    function lookupCore(table, key, element) {
        for (const exception of table.exceptions) {
            if (exception.key === key && element && element.closest(exception.within)) {
                return exception.skip ? null : exception.co;
            }
        }
        for (const candidate of table.exact.get(key) || []) {
            if (applies(candidate, element)) return candidate.co;
        }
        for (const template of table.templates) {
            const found = key.match(template.regex);
            if (!found || !applies(template, element)) continue;
            const values = {};
            template.names.forEach((name, index) => { values[name] = found[index + 1]; });
            return template.co.replace(PLACEHOLDER, (whole, name) => values[name] ?? whole);
        }
        return undefined;
    }

    /**
     * The Corsican for one label, or undefined. Leading and trailing spaces are kept; a final "…", "..." or ":"
     * is kept when only the label before it is known. Nothing else is guessed: no case folding, no word splitting.
     */
    function translateText(table, text, element) {
        const match = /^(\s*)([\s\S]*?)(\s*)$/.exec(text);
        const [, before, core, after] = match;
        if (!core || core.length > MAX_LENGTH || !/[^\W\d_]/u.test(core)) return undefined;
        const key = normalize(core);
        let found = lookupCore(table, key, element);
        if (found === undefined) {
            const trailing = TRAILING.exec(key);
            if (trailing && trailing[1]) {
                const inner = lookupCore(table, trailing[1], element);
                if (inner) found = inner + trailing[2];
            }
        }
        if (!found || found === key) return undefined;
        return before + found + after;
    }

    /** Selector strings of an adapter, joined once. */
    function zones(adapter, table) {
        const join = list => (list && list.length ? list.join(", ") : null);
        const selectors = [adapter.ui, adapter.never, adapter.uiInsideNever, adapter.searchFields].flat()
            .filter(Boolean);
        if (table) {
            for (const list of table.exact.values()) for (const entry of list) if (entry.within) selectors.push(entry.within);
            for (const entry of [...table.templates, ...table.exceptions]) if (entry.within) selectors.push(entry.within);
        }
        // Attribute values the selectors depend on, such as nav[aria-label="Repository"]: translating them would
        // move the zones (and could break the site's own CSS or scripts that select on them).
        const pinned = [];
        for (const selector of selectors) {
            for (const found of selector.matchAll(/\[([\w-]+)([*^$]?=)"([^"]*)"\]/g)) {
                pinned.push({ name: found[1], operator: found[2], value: found[3] });
            }
        }
        return {
            pinned,
            ui: join([...(adapter.ui || []), ...(adapter.uiInsideNever || [])]),
            never: join(adapter.never),
            uiInsideNever: join(adapter.uiInsideNever),
            searchFields: join(adapter.searchFields),
            attributes: (adapter.attributes || []).filter(name => name !== "placeholder"),
        };
    }

    /**
     * True when text inside `element` belongs to user content or to a protected element. The adapter's `never`
     * zones win over its `ui` zones, except for the few widgets listed in `uiInsideNever` (such as the copy button
     * GitHub puts inside a README), when that widget is nested inside the never zone.
     */
    /** True when changing this attribute value would change which selectors match. */
    function pinnedAttribute(z, name, value) {
        return z.pinned.some(pin => pin.name === name && (
            pin.operator === "=" ? value === pin.value : pin.operator === "^=" ? value.startsWith(pin.value)
                : pin.operator === "$=" ? value.endsWith(pin.value) : value.includes(pin.value)));
    }

    function blocked(element, z) {
        if (!element || element.closest(BUILTIN_NEVER)) return true;
        const never = z.never && element.closest(z.never);
        if (!never) return false;
        const widget = z.uiInsideNever && element.closest(z.uiInsideNever);
        return !(widget && widget !== never && never.contains(widget));
    }

    /** True when text inside `element` is site interface that the engine may translate. */
    function inInterface(element, z) {
        return Boolean(element && z.ui && element.closest(z.ui)) && !blocked(element, z);
    }

    /**
     * A translator for one document. `schedule(callback)` batches work (requestIdleCallback in the browser,
     * a manual queue in tests). `showOriginal` is "tooltip" (title attribute on the label's element when it has
     * none) or "off".
     */
    function createTranslator({ adapter, glossary, schedule, showOriginal = "off" }) {
        const z = zones(adapter, glossary);
        const done = new WeakSet();          // text nodes and elements already looked at
        const records = new WeakMap();       // node -> { text: record, attrs: { name: record } }
        const changed = new Set();           // every record, so the page can be put back
        const pending = new Set();
        let scheduled = false, active = true, tooltips = showOriginal === "tooltip";

        const recordOf = node => {
            if (!records.has(node)) records.set(node, { text: null, attrs: {} });
            return records.get(node);
        };

        function translateTextNode(node) {
            if (done.has(node)) return;
            done.add(node);
            const parent = node.parentElement;
            if (!inInterface(parent, z)) return;
            const translated = translateText(glossary, node.data, parent);
            if (translated === undefined || translated === node.data) return;
            const record = { node, attr: null, original: node.data, translated, tooltipOn: null };
            if (tooltips && !parent.hasAttribute("title")) {
                parent.setAttribute("title", node.data.trim());
                parent.setAttribute("data-corsu-title", "");
                record.tooltipOn = parent;
            }
            node.data = translated;
            recordOf(node).text = record;
            changed.add(record);
        }

        function translateAttributes(element) {
            if (done.has(element)) return;
            done.add(element);
            const search = Boolean(z.searchFields && element.matches(z.searchFields));
            const allowed = search ? !blocked(element.parentElement, z) && Boolean(element.parentElement)
                                   : inInterface(element, z);
            if (!allowed) return;
            const names = search ? [...z.attributes, "placeholder"] : z.attributes;
            for (const name of names) {
                const value = element.getAttribute(name);
                if (!value || (name === "title" && element.hasAttribute("data-corsu-title"))) continue;
                if (pinnedAttribute(z, name, value)) continue;
                const translated = translateText(glossary, value, element);
                if (translated === undefined || translated === value) continue;
                const record = { node: element, attr: name, original: value, translated };
                element.setAttribute(name, translated);
                recordOf(element).attrs[name] = record;
                changed.add(record);
            }
        }

        function visit(node) {
            if (node.nodeType === TEXT_NODE) { translateTextNode(node); return; }
            if (node.nodeType !== ELEMENT_NODE) {
                for (const child of node.childNodes || []) visit(child);
                return;
            }
            translateAttributes(node);
            if (node.matches(BUILTIN_NEVER) && !(z.searchFields && node.matches(z.searchFields))) return;
            if (z.never && node.matches(z.never)) {
                // User content: only look for the interface widgets that may sit inside it.
                if (z.uiInsideNever) for (const widget of node.querySelectorAll(z.uiInsideNever)) visit(widget);
                return;
            }
            for (const child of node.childNodes) visit(child);
        }

        function flush() {
            scheduled = false;
            if (!active) { pending.clear(); return; }
            const roots = [...pending];
            pending.clear();
            for (const root of roots) if (root.isConnected !== false) visit(root);
            for (const record of changed) if (!record.node.isConnected) changed.delete(record);
        }

        function queue(node) {
            pending.add(node);
            if (!scheduled) { scheduled = true; schedule(flush); }
        }

        /** Feed MutationObserver records. The engine's own changes are recognised and ignored. */
        function handleMutations(mutations) {
            for (const mutation of mutations) {
                if (mutation.type === "childList") {
                    for (const node of mutation.addedNodes) queue(node);
                } else if (mutation.type === "characterData") {
                    const record = records.get(mutation.target)?.text;
                    if (record && mutation.target.data === record.translated) continue;
                    if (record) changed.delete(record);
                    done.delete(mutation.target);
                    queue(mutation.target);
                } else if (mutation.type === "attributes") {
                    const element = mutation.target, name = mutation.attributeName;
                    const record = records.get(element)?.attrs[name];
                    if (record && element.getAttribute(name) === record.translated) continue;
                    if (name === "title" && element.hasAttribute("data-corsu-title")) continue;
                    if (record) { changed.delete(record); delete records.get(element).attrs[name]; }
                    done.delete(element);
                    queue(element);
                }
            }
        }

        /** Put every changed label back to the site's own text. */
        function revert() {
            for (const record of changed) {
                const { node, attr } = record;
                if (attr) {
                    if (node.getAttribute(attr) === record.translated) node.setAttribute(attr, record.original);
                    delete records.get(node)?.attrs[attr];
                } else {
                    if (node.data === record.translated) node.data = record.original;
                    if (record.tooltipOn) {
                        record.tooltipOn.removeAttribute("title");
                        record.tooltipOn.removeAttribute("data-corsu-title");
                    }
                    if (records.get(node)) records.get(node).text = null;
                }
                done.delete(node);
            }
            changed.clear();
        }

        return {
            start(root) { active = true; queue(root); },
            /** Translate now (tests, and the first pass so the page does not stay English until idle time). */
            run(root) { active = true; visit(root); },
            handleMutations,
            stop() { active = false; pending.clear(); revert(); },
            setShowOriginal(mode) { tooltips = mode === "tooltip"; },
            get active() { return active; },
            get changedCount() { return changed.size; },
        };
    }

    /** The adapter whose hosts include this hostname (exact host or a subdomain listed explicitly). */
    function adapterFor(adapters, hostname) {
        return Object.values(adapters).find(adapter => adapter.hosts.includes(hostname)) || null;
    }

    return { BUILTIN_NEVER, normalize, placeholders, compileGlossary, translateText, zones, blocked, inInterface,
             createTranslator, adapterFor };
});
