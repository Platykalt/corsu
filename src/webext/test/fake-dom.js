/*
 * A tiny fake DOM for the engine tests (jsdom is not available offline). It implements only what
 * core/engine.js uses, and a CSS selector subset: tag, *, #id, .class, [attr], [attr="v"], [attr^="v"],
 * [attr*="v"], [attr$="v"], compound selectors, the descendant combinator (space) and comma lists.
 */
"use strict";

class Node {
    constructor(nodeType) { this.nodeType = nodeType; this.parentNode = null; this.childNodes = []; }
    get parentElement() { return this.parentNode && this.parentNode.nodeType === 1 ? this.parentNode : null; }
    get isConnected() {
        let node = this;
        while (node.parentNode) node = node.parentNode;
        return node.nodeType === 9;
    }
    append(...children) {
        for (const child of children) {
            const node = typeof child === "string" ? new Text(child) : child;
            node.parentNode = this;
            this.childNodes.push(node);
        }
        return this;
    }
    remove() {
        if (!this.parentNode) return;
        this.parentNode.childNodes = this.parentNode.childNodes.filter(node => node !== this);
        this.parentNode = null;
    }
    contains(other) {
        for (let node = other; node; node = node.parentNode) if (node === this) return true;
        return false;
    }
}

class Text extends Node {
    constructor(data) { super(3); this.data = data; }
}

class Element extends Node {
    constructor(tagName, attributes = {}) {
        super(1);
        this.tagName = tagName.toUpperCase();
        this.attributes = new Map(Object.entries(attributes));
    }
    getAttribute(name) { return this.attributes.has(name) ? this.attributes.get(name) : null; }
    setAttribute(name, value) { this.attributes.set(name, String(value)); }
    hasAttribute(name) { return this.attributes.has(name); }
    removeAttribute(name) { this.attributes.delete(name); }
    get textContent() {
        return this.childNodes.map(node => (node.nodeType === 3 ? node.data : node.textContent)).join("");
    }
    matches(selector) { return parseSelector(selector).some(complex => matchComplex(this, complex)); }
    closest(selector) {
        const parsed = parseSelector(selector);
        for (let node = this; node && node.nodeType === 1; node = node.parentNode) {
            if (parsed.some(complex => matchComplex(node, complex))) return node;
        }
        return null;
    }
    querySelectorAll(selector) {
        const parsed = parseSelector(selector), found = [];
        const walk = node => {
            for (const child of node.childNodes) {
                if (child.nodeType !== 1) continue;
                if (parsed.some(complex => matchComplex(child, complex))) found.push(child);
                walk(child);
            }
        };
        walk(this);
        return found;
    }
}

class Document extends Node {
    constructor() { super(9); }
    get documentElement() { return this.childNodes.find(node => node.nodeType === 1) || null; }
}

/** Split on `separator` outside brackets and quotes. */
function split(text, separator) {
    const parts = [];
    let depth = 0, quote = null, current = "";
    for (const char of text) {
        if (quote) { if (char === quote) quote = null; current += char; continue; }
        if (char === "\"" || char === "'") { quote = char; current += char; continue; }
        if (char === "[") depth++;
        if (char === "]") depth--;
        if (depth === 0 && separator.test(char)) { if (current.trim()) parts.push(current.trim()); current = ""; continue; }
        current += char;
    }
    if (current.trim()) parts.push(current.trim());
    return parts;
}

const cache = new Map();
function parseSelector(selector) {
    if (!cache.has(selector)) {
        cache.set(selector, split(selector, /,/).map(complex => split(complex, /\s/).map(parseCompound)));
    }
    return cache.get(selector);
}

function parseCompound(text) {
    const compound = { tag: null, ids: [], classes: [], attributes: [] };
    const pattern = /^(\*|[a-zA-Z][\w-]*)|#([\w-]+)|\.([\w-]+)|\[([\w-]+)(?:([*^$]?=)"([^"]*)")?\]/y;
    let index = 0;
    while (index < text.length) {
        pattern.lastIndex = index;
        const found = pattern.exec(text);
        if (!found || found[0] === "") throw new Error(`Unsupported selector: ${text}`);
        if (found[1] && index === 0) compound.tag = found[1] === "*" ? null : found[1].toUpperCase();
        else if (found[1]) throw new Error(`Unsupported selector: ${text}`);
        if (found[2]) compound.ids.push(found[2]);
        if (found[3]) compound.classes.push(found[3]);
        if (found[4]) compound.attributes.push({ name: found[4], operator: found[5], value: found[6] });
        index = pattern.lastIndex;
        pattern.lastIndex = 0;
        if (index === 0) break;
    }
    return compound;
}

function matchCompound(element, compound) {
    if (compound.tag && element.tagName !== compound.tag) return false;
    if (compound.ids.some(id => element.getAttribute("id") !== id)) return false;
    const classes = (element.getAttribute("class") || "").split(/\s+/);
    if (compound.classes.some(name => !classes.includes(name))) return false;
    return compound.attributes.every(({ name, operator, value }) => {
        const actual = element.getAttribute(name);
        if (actual === null) return false;
        if (!operator) return true;
        if (operator === "=") return actual === value;
        if (operator === "^=") return actual.startsWith(value);
        if (operator === "$=") return actual.endsWith(value);
        return actual.includes(value);
    });
}

function matchComplex(element, compounds) {
    if (!matchCompound(element, compounds[compounds.length - 1])) return false;
    let index = compounds.length - 2;
    for (let node = element.parentNode; node && node.nodeType === 1 && index >= 0; node = node.parentNode) {
        if (matchCompound(node, compounds[index])) index--;
    }
    return index < 0;
}

/** h("nav", {"aria-label": "Repository"}, h("a", {}, "Code"), "text") */
function h(tag, attributes = {}, ...children) {
    return new Element(tag, attributes).append(...children);
}

function page(...children) {
    const document = new Document();
    document.append(h("html", {}, h("body", {}, ...children)));
    return document;
}

module.exports = { Node, Text, Element, Document, h, page, parseSelector };
