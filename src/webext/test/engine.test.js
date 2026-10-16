// Tests of the Corsu web extension engine and GitHub adapter. Run: node --test src/webext/test/engine.test.js
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const engine = require("../core/engine.js");
const github = require("../adapters/github.js");
const { h, page, parseSelector } = require("./fake-dom.js");

const WEBEXT = path.join(__dirname, "..");
const readJSON = name => JSON.parse(fs.readFileSync(path.join(WEBEXT, name), "utf8"));
const siteGlossary = readJSON("glossary/github.json");
const sharedGlossary = readJSON("glossary/shared.json");
const table = engine.compileGlossary(siteGlossary, sharedGlossary);

/** A translator whose idle callbacks run only when the test calls flush(). */
function translatorFor(options = {}) {
    const queue = [];
    const translator = engine.createTranslator({
        adapter: github, glossary: table, schedule: callback => queue.push(callback), ...options,
    });
    return { translator, queue, flush: () => { while (queue.length) queue.shift()(); } };
}

const text = element => element.textContent;

test("exact labels, placeholders and trailing punctuation", () => {
    const nav = h("nav", { "aria-label": "Repository" });
    assert.equal(engine.translateText(table, "Pull requests", nav), "Dumande di fusione");
    assert.equal(engine.translateText(table, "\n   Issues  \n", nav), "\n   Prublemi  \n");
    assert.equal(engine.translateText(table, "12 comments", nav), "12 cummenti");
    assert.equal(engine.translateText(table, "1,204 comments", nav), "1,204 cummenti");
    assert.equal(engine.translateText(table, "Filter by label type-bug", nav), "Filtrà per etichetta type-bug");
    assert.equal(engine.translateText(table, "Page 7", nav), "Pagina 7");
    assert.equal(engine.translateText(table, "src, (Directory)", nav), "src, (Cartulare)");
    assert.equal(engine.translateText(table, "Name:", nav), "Nome:");
    assert.equal(engine.translateText(table, "Search or jump to...", nav), "Ricercà o andà à…");
    // Site glossary wins over shared.json; the shared one fills the gaps.
    assert.equal(engine.translateText(table, "Settings", nav), "Parametri");
});

test("nothing is guessed: no case folding, no partial matches, no long texts", () => {
    const nav = h("nav", { "aria-label": "Global" });
    assert.equal(engine.translateText(table, "issues", nav), undefined);
    assert.equal(engine.translateText(table, "Issues and pull requests", nav), undefined);
    assert.equal(engine.translateText(table, "Page seven", nav), undefined);
    assert.equal(engine.translateText(table, "Settings ".repeat(20), nav), undefined);
    assert.equal(engine.translateText(table, "2026", nav), undefined);
    assert.equal(engine.translateText(table, "", nav), undefined);
});

test("entries limited with `within` only apply in their context", () => {
    const repoNav = h("nav", { "aria-label": "Repository" }, h("span", {}, "Code"));
    const footer = h("footer", { role: "contentinfo" }, h("span", {}, "Code"));
    assert.equal(engine.translateText(table, "Code", repoNav.childNodes[0]), "Codice");
    assert.equal(engine.translateText(table, "Code", footer.childNodes[0]), undefined);
});

test("interface zones are translated, user content is never touched", () => {
    const doc = page(
        h("header", { role: "banner" }, h("a", {}, "Sign in"), h("button", {}, "Platform")),
        h("nav", { "aria-label": "Repository" }, h("a", {}, h("span", {}, "Code")), h("a", {}, "Issues")),
        h("main", {},
            h("p", {}, "Settings"),                                          // not an interface zone
            h("button", { class: "prc-IssueLabel-IssueLabel-x1" }, "Documentation"),  // label name
            h("a", { "data-hovercard-type": "user" }, h("button", {}, "Open")),        // user name
            h("article", {}, h("div", { class: "markdown-body" },
                h("h2", { "data-component": "Heading" }, "Documentation"),
                h("button", {}, "Copy"),
                h("pre", {}, h("code", {}, "Settings")))),
            h("div", { contenteditable: "true" }, h("button", {}, "Save")),
            h("table", { "data-testid": "directory-content" },
                h("thead", {}, h("tr", {}, h("th", {}, "Name"), h("th", {}, "Last commit message"))),
                h("tbody", {}, h("tr", {}, h("td", { title: "Documentation" }, "Documentation"))))),
        h("footer", { role: "contentinfo" }, h("nav", { "aria-label": "Footer" }, h("a", {}, "Docs"), h("a", {}, "Privacy"))));
    const { translator } = translatorFor();
    translator.run(doc);
    const html = doc.documentElement;
    const [header, nav, main, footer] = html.childNodes[0].childNodes;
    assert.equal(text(header), "CunnettesiPiattaforma");
    assert.equal(text(nav), "CodicePrublemi");
    assert.equal(text(footer), "DocumentazioneVita privata");
    assert.equal(text(main.childNodes[0]), "Settings");
    assert.equal(text(main.childNodes[1]), "Documentation");
    assert.equal(text(main.childNodes[2]), "Open");
    assert.equal(text(main.childNodes[3]), "DocumentationCopySettings");
    assert.equal(text(main.childNodes[4]), "Save");
    const table = main.childNodes[5];
    assert.equal(text(table.childNodes[0]), "NomeMessaghju di l’ultimu commit");
    assert.equal(text(table.childNodes[1]), "Documentation");
    assert.equal(table.childNodes[1].childNodes[0].childNodes[0].getAttribute("title"), "Documentation");
});

test("attributes: aria-label and title in interface zones, placeholder of search fields only", () => {
    const search = h("input", { role: "combobox", placeholder: "Search issues", value: "Settings" });
    const comment = h("textarea", { placeholder: "Leave a comment", "aria-label": "Close" });
    const doc = page(
        h("nav", { "aria-label": "Breadcrumbs" }),
        h("button", { "aria-label": "Close dialog", title: "Close" }),
        h("div", {}, search, comment, h("input", { type: "text", placeholder: "Search issues" })),
        h("p", { "aria-label": "Close" }, "x"));
    const { translator } = translatorFor();
    translator.run(doc);
    const [nav, button, , paragraph] = doc.documentElement.childNodes[0].childNodes;
    assert.equal(nav.getAttribute("aria-label"), "Chjassu di navigazione");
    assert.equal(button.getAttribute("aria-label"), "Chjode a finestra di dialogu");
    assert.equal(button.getAttribute("title"), "Chjode");
    assert.equal(search.getAttribute("placeholder"), "Ricercà i prublemi");
    assert.equal(search.getAttribute("value"), "Settings");
    assert.equal(comment.getAttribute("placeholder"), "Leave a comment");
    assert.equal(comment.getAttribute("aria-label"), "Close");
    assert.equal(doc.documentElement.childNodes[0].childNodes[2].childNodes[2].getAttribute("placeholder"),
                 "Search issues");
    assert.equal(paragraph.getAttribute("aria-label"), "Close");
});

test("attribute values that selectors rely on are never translated, so zones do not move", () => {
    const nav = h("nav", { "aria-label": "Repository" }, h("a", {}, h("span", {}, "Code")));
    const header = h("header", { "aria-label": "Global navigation menu" }, h("a", {}, "Explore"));
    const doc = page(nav, header);
    const { translator } = translatorFor();
    translator.run(doc);
    assert.equal(nav.getAttribute("aria-label"), "Repository");
    assert.equal(header.getAttribute("aria-label"), "Global navigation menu");
    assert.equal(text(nav), "Codice");
    assert.equal(text(header), "Scopre");
    // Run twice: the result is stable.
    translator.run(doc);
    assert.equal(text(nav), "Codice");
});

test("contextual exceptions: the state icon is singular, the state filter plural", () => {
    const icon = h("svg", { role: "img", "aria-label": "Open" });
    const doc = page(h("nav", { "aria-label": "Issues" }, h("a", {}, "Open"), h("a", {}, "Closed")), icon,
                     h("h2", { "data-component": "Heading" }, "Code"));
    const { translator } = translatorFor();
    translator.run(doc);
    const [nav, , heading] = doc.documentElement.childNodes[0].childNodes;
    assert.equal(text(nav), "ApertiChjusi");
    assert.equal(icon.getAttribute("aria-label"), "Apertu");
    assert.equal(text(heading), "Code");
});

test("interface widgets inside user content (uiInsideNever)", () => {
    const copy = h("clipboard-copy", { "aria-label": "Copy code to clipboard" });
    const doc = page(h("div", { class: "markdown-body" }, h("p", {}, "Copy"), h("div", {}, copy)),
                     h("table", { "data-testid": "directory-content" }, h("tbody", {},
                         h("tr", { "data-testid": "view-all-files-row" }, h("td", {}, h("button", {}, "View all files"))),
                         h("tr", {}, h("td", {}, h("button", {}, "Files"))))));
    const { translator } = translatorFor();
    translator.run(doc);
    const [markdown, files] = doc.documentElement.childNodes[0].childNodes;
    assert.equal(copy.getAttribute("aria-label"), "Cupià u codice in u preme’papei");
    assert.equal(text(markdown.childNodes[0]), "Copy");
    assert.equal(text(files), "Affissà tutti i schedariiFiles");
});

test("mutations are batched, re-translated when the site changes them, and own edits are ignored", () => {
    const doc = page(h("nav", { "aria-label": "Global" }));
    const nav = doc.documentElement.childNodes[0].childNodes[0];
    const { translator, queue, flush } = translatorFor();
    translator.run(doc);
    const first = h("a", {}, "Explore"), second = h("a", {}, "Trending");
    nav.append(first, second);
    translator.handleMutations([{ type: "childList", addedNodes: [first] }, { type: "childList", addedNodes: [second] }]);
    assert.equal(queue.length, 1, "one idle callback for a burst of mutations");
    assert.equal(text(nav), "ExploreTrending", "nothing changes before the idle callback");
    flush();
    assert.equal(text(nav), "ScopreIn voga");
    // The engine's own write comes back as a characterData record: no new work.
    translator.handleMutations([{ type: "characterData", target: first.childNodes[0] }]);
    assert.equal(queue.length, 0);
    // GitHub changes the label (React re-render): it is looked at again.
    first.childNodes[0].data = "Topics";
    translator.handleMutations([{ type: "characterData", target: first.childNodes[0] }]);
    flush();
    assert.equal(text(first), "Temi");
    // An attribute set by the site again is translated again; the engine's own value is not re-queued.
    const button = h("button", { "aria-label": "Close" });
    nav.append(button);
    translator.handleMutations([{ type: "childList", addedNodes: [button] }]);
    flush();
    assert.equal(button.getAttribute("aria-label"), "Chjode");
    translator.handleMutations([{ type: "attributes", target: button, attributeName: "aria-label" }]);
    assert.equal(queue.length, 0);
    button.setAttribute("aria-label", "Dismiss");
    translator.handleMutations([{ type: "attributes", target: button, attributeName: "aria-label" }]);
    flush();
    assert.equal(button.getAttribute("aria-label"), "Ricusà");
});

test("original text: tooltip on hover, and stop() puts the site's text back", () => {
    const withTitle = h("button", { title: "Already there" }, "Cancel");
    const doc = page(h("nav", { "aria-label": "Global" }, h("a", {}, "Pricing"), withTitle),
                     h("button", { "aria-label": "Close" }));
    const { translator } = translatorFor({ showOriginal: "tooltip" });
    translator.run(doc);
    const [nav, close] = doc.documentElement.childNodes[0].childNodes;
    const link = nav.childNodes[0];
    assert.equal(text(link), "Tariffi");
    assert.equal(link.getAttribute("title"), "Pricing");
    assert.equal(withTitle.getAttribute("title"), "Already there");
    assert.equal(text(withTitle), "Abbandunà");
    assert.equal(close.getAttribute("aria-label"), "Chjode");
    translator.stop();
    assert.equal(text(link), "Pricing");
    assert.equal(link.hasAttribute("title"), false);
    assert.equal(text(withTitle), "Cancel");
    assert.equal(close.getAttribute("aria-label"), "Close");
    assert.equal(translator.changedCount, 0);
    translator.run(doc);
    assert.equal(text(link), "Tariffi");
});

test("adapter selection by exact host", () => {
    const adapters = { github };
    assert.equal(engine.adapterFor(adapters, "github.com"), github);
    assert.equal(engine.adapterFor(adapters, "gist.github.com"), null);
    assert.equal(engine.adapterFor(adapters, "evilgithub.com"), null);
});

test("adapter selectors stay within the subset the fake DOM understands", () => {
    for (const key of ["ui", "never", "uiInsideNever", "searchFields"]) {
        for (const selector of github[key]) assert.doesNotThrow(() => parseSelector(selector), selector);
    }
    assert.ok(github.never.length > 5, "the adapter declares user-content zones");
});

test("manifest content script runs only on the adapter's hosts", () => {
    const manifest = readJSON("manifest.json");
    const matches = manifest.content_scripts.flatMap(script => script.matches);
    assert.deepEqual(matches, github.matches);
    assert.deepEqual(manifest.host_permissions, github.matches);
});
