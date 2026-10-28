#!/usr/bin/env python3
"""Regressions reported on Discord desktop 1.0.166 (French UI) after Corsu 0.28.1, on the BUILT plugin with the REAL dictionary.

Usage: check_discord_regressions.py CHROME [VENCORD_DIR]
Same harness as check_discord_built.py (the translator taken out of VENCORD_DIR/dist/renderer.js, headless Chrome), but
each scenario models the markup and React records of Discord's public web client as read in its own code on 2026-10-27
(web.ad0b95d8568e0f6b.js and its lazy chunks; class names from the client's CSS module maps), and most of them insert
or change the page AFTER the translator started, the way Discord does:
- A. the message composer of a DM: the placeholder <div class="placeholder__1b31f slateTextArea_ec4baf" aria-hidden
  data-slate-placeholder> that Discord's SlateTextArea draws NEXT TO the editor (not inside it, unlike Slate's own
  placeholder), key 4c+CAx "Envoyer un message à {channel}" (8lzR/R "… dans {channel}" in a group), the editor's
  aria-label fqOxbV "Écrire un message, {channel}"; the placeholder is removed while a draft is typed and a new <div> is
  inserted when the draft is erased; a draft equal to a dictionary phrase is never touched, nor the caret;
- B. the message search bar over a DM (LDZtFO "Rechercher {name}", Slate's own placeholder span inside the combobox,
  whose aria-label is the same text): open, type, clear, navigate (remounted by key, or the text node reused);
- C. group DM notices MMN2Jq "{username} a ajouté {otherUsername} au groupe.", L2FyVq (retiré), 5v2xa8 (quitté) and
  the pin notices yIDvPL / R7vZGZ, with the names drawn by the username hook (an Anchor > span.container__703b9 >
  span.nameContainer__703b9 > span.name__703b9) and the fragments as bare text nodes of the content <div>, inserted
  after load; a nickname equal to a fragment ("a ajouté"); a real message with the same words;
- for every scenario: the page writing back what it shows, then a second translator over the translated page (no
  double translation).
Expected values: Discord's French translated with the Corsican already in the dictionary (Corsu usage), except the
cases tagged "proposal" (an AI wording proposal, not a speaker's validation; see docs/discord-review-0.28.2.md).
This is a simulated page, not an observation of the real Discord app.
"""
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
from check_chromium import DevTools  # noqa: E402
from check_discord_names import evaluate  # noqa: E402
from check_discord_built import extract  # noqa: E402

HELPERS = r'''
window.results = [];
const ID = n => String(n).repeat(18).slice(0, 18);
const user = (n, g) => ({ id: ID(n), username: "u" + n, globalName: g });
const raw = p => ({ id: p.id, username: p.username, global_name: p.globalName });
const ron = user(3, "Ron"), work = user(1, "Work"), error = user(2, "Error"), fragment = user(8, "a ajouté");
const dm = p => ({ id: "9" + p.id.slice(1), type: 1, name: "", recipients: [p.id], rawRecipients: [raw(p)], nicks: {} });
const group = (...people) => ({ id: ID(6), type: 3, name: "", recipients: people.map(p => p.id), rawRecipients: people.map(raw), nicks: {} });
const settle = () => new Promise(resolve => setTimeout(resolve, 40));
// React's records: the node (an element, or a text node like React's HostText) keeps the fiber that created it, the
// component fibers above it hold their props (nearest first).
function fiber(node, ...chain) {
  let parent = null;
  for (const props of [...chain].reverse()) parent = { memoizedProps: props, return: parent, alternate: null };
  const host = { memoizedProps: node.nodeType === Node.TEXT_NODE ? node.data : { children: node.textContent }, return: parent, alternate: null };
  node.__reactFiber$test = host;
  if (node.nodeType === Node.ELEMENT_NODE) node.__reactProps$test = host.memoizedProps;
  return host;
}
const element = markup => { const t = document.createElement("template"); t.innerHTML = markup.trim(); return t.content.firstElementChild; };
function check(name, models, got, expected, kind = "regression") {
  const ok = typeof expected === "function" ? expected(got) : got === expected;
  results.push({ name, models, got, expected: typeof expected === "function" ? expected.description : expected, ok, kind });
}
const translatedSearch = name => Object.assign(v => v !== "Rechercher " + name && v.startsWith("Circà") && v.endsWith(" " + name),
  { description: `translated ("Circà … ${name}"), name kept` });
// Every checked value is read again after the page writes back what it shows and after a second translator.
window.watched = [];
const watch = (name, read) => watched.push({ name, read });
'''

# Discord's SlateTextArea (web.ad0b95d8568e0f6b.js, the class with showPlaceholder; ChannelTextArea passes
# className "slateTextArea_ec4baf" and wraps it in div.slateContainer_ec4baf): the placeholder is a sibling <div> of the
# editor (class "markup__75297 editor__1b31f …", contenteditable, role textbox), rendered only while the editor is empty.
COMPOSER = r'''
const zero = '<span data-slate-zero-width="n" data-slate-length="0">﻿<br></span>';
function composer(channel, placeholder, label) {
  const root = element(`<form class="form__74017"><div class="channelTextArea__74017"><div class="scrollableContainer__74017"><div class="inner__74017"><div class="textArea__74017"><div class="slateContainer_ec4baf"><div>
    <div class="markup__75297 editor__1b31f slateTextArea_ec4baf" role="textbox" aria-multiline="true" spellcheck="true" aria-label="${label}" contenteditable="true" data-slate-editor="true" data-slate-node="value"><div data-slate-node="element"><span data-slate-node="text"><span data-slate-leaf="true">${zero}</span></span></div></div>
  </div></div></div></div></div></div></form>`);
  const editor = root.querySelector('[role="textbox"]');
  const records = [{ editor: {}, className: "slateTextArea_ec4baf", placeholder, channelId: channel.id }, { channel, type: { analyticsName: "normal" } }];
  fiber(editor, { className: "markup__75297 editor__1b31f slateTextArea_ec4baf", "aria-label": label }, ...records);
  return { root, editor, records };
}
function showPlaceholder(c, text) {
  const div = element(`<div class="placeholder__1b31f slateTextArea_ec4baf" aria-hidden="true" data-slate-placeholder="true">${text}</div>`);
  fiber(div, { className: "placeholder__1b31f slateTextArea_ec4baf", "aria-hidden": true, "data-slate-placeholder": "true", children: text }, ...c.records);
  c.editor.before(div);
  return div;
}
'''

# Discord's message search bar (lazy chunk c5b5c25ec8ff16aa.js): placeholder LDZtFO "Rechercher {name}" with the
# conversation's name, passed to Slate's Editable as placeholder (drawn by renderPlaceholder in the leaf, a span
# data-slate-placeholder contenteditable=false) and as the combobox's aria-label; the bar is keyed by search context.
SEARCH = r'''
function searchBar(channel, name) {
  const text = "Rechercher " + name;
  const root = element(`<div class="search_c322aa"><div class="searchBar_c322aa"><div class="searchBar__25bec">
    <div class="editor__25bec" role="combobox" aria-expanded="false" aria-label="${text}" aria-autocomplete="list" autocorrect="off" spellcheck="false" contenteditable="true" data-slate-editor="true" data-slate-node="value"><div data-slate-node="element"><span data-slate-node="text"><span data-slate-leaf="true"><span data-slate-placeholder="true" contenteditable="false" style="position:absolute;pointer-events:none;opacity:1">${text}</span><span data-slate-zero-width="n" data-slate-length="0">﻿<br></span></span></span></div></div>
  </div></div></div>`);
  const records = [{ placeholder: text, navId: "search-results" }, { searchContext: { type: "CHANNEL", channelId: channel.id }, placeholder: text }];
  fiber(root.querySelector('[role="combobox"]'), { "aria-label": text, role: "combobox" }, ...records);
  fiber(root.querySelector("[data-slate-placeholder]"), { contentEditable: false, children: text }, { leaf: { placeholder: text } }, ...records);
  return root;
}
'''

# A system message row (lazy chunk fe6d9251f9aa4e0a.js): the message list item, the layout component (module 888675:
# div.container__235ca > div.iconContainer__235ca + div.content__235ca > div > [children, timestamp]) and the parts
# intl.format gives: the hooks' elements and bare strings. The username hook (module 447215) draws the name through
# module 463930: an Anchor > span.container__703b9 > span.nameContainer__703b9 > span.name__703b9, inside a user
# popout holding the user record.
SYSTEM = r'''
let messageCounter = 0;
function systemRow(channel, author, parts, upper) {
  const message = { id: ID(7).slice(0, 15) + String(++messageCounter).padStart(3, "0"), channel_id: channel.id, author, mentions: [], content: "" };
  const li = element(`<li id="chat-messages-${channel.id}-${message.id}" class="messageListItem__5126c"><div class="message__5126c cozyMessage__5126c systemMessage__5126c" role="article"><div class="container__235ca cozy__235ca"><div class="iconContainer__235ca"><div class="icon__235ca iconSize__235ca"></div></div><div class="content__235ca"><div></div></div></div></div></li>`);
  const line = li.querySelector(".content__235ca > div");
  const chain = [{ children: parts }, { className: "content__235ca" }, { className: "container__235ca cozy__235ca" },
    { timestamp: "2026-10-27T12:00:00Z", compact: false, children: parts }, { message, ...upper }, { message, channel, compact: false }];
  const nodes = [];
  for (const part of parts) {
    if (typeof part === "string") {
      const node = document.createTextNode(part);
      fiber(node, ...chain);
      line.append(node);
      nodes.push(node);
    } else if (part.user) {
      const a = element(`<span class="anchor__14d82 anchorUnderlineOnHover__14d82" role="button" tabindex="0"><span class="container__703b9"><span class="nameContainer__703b9"><span class="name__703b9 username__703b9 desaturateUserColors__41f68">${part.name}</span></span></span></span>`);
      const name = a.querySelector(".name__703b9");
      fiber(name, { className: "name__703b9 username__703b9", children: part.name }, { roleStyle: "username", name: part.name },
        { name: part.name, colorString: null }, { user: part.user, channelId: channel.id, messageId: message.id }, ...chain);
      line.append(a);
      nodes.push(name);
    } else {
      const a = element(`<span class="anchor__14d82 anchorUnderlineOnHover__14d82" role="button" tabindex="0">${part.link}</span>`);
      fiber(a, { onClick() {}, children: part.link }, ...chain);
      line.append(a);
      nodes.push(a);
    }
  }
  const time = element(`<span class="timestamp_c19a55"><time aria-label="Aujourd'hui à 12:00" datetime="2026-10-27T12:00:00.000Z">12:00</time></span>`);
  line.append(time);
  return { li, nodes, message };
}
const read = node => node.nodeType === Node.TEXT_NODE ? node.data : node.textContent;
'''

# 0.28.3, report B. Discord's message list draws every system message inside the SAME wrapper as a person's message:
# SystemMessage (lazy chunk c9979a719b7a8406.js, module 64369, `ls`) renders the type's component (the pin notice `iP`:
# yIDvPL / lD5tup / R7vZGZ / vfkjqx) as the children of MessageContent (module 438729, `O`), a
# <div id="message-content-{id}" class="markup__75297 messageContent_c19a55"> whose component holds the message record
# (with its numeric `type`). Inside: SystemMessage's container (module 888675: div.container__235ca > div.iconContainer +
# div.content__235ca > div > [the formatted text, the timestamp span]). The username hook (module 447215) draws an
# Anchor > span.container__703b9 > span.nameContainer__703b9 > span.name__703b9; each $link an Anchor. The C1-C3 rows
# above leave that wrapper out, which is why 0.28.2 passed them and still showed the notice in French.
NOTICE = r'''
let noticeCounter = 0;
function listNotice(channel, author, type, parts, { compact = true, time = "01:31", messageId } = {}) {
  const message = { id: messageId || ID(5).slice(0, 15) + String(++noticeCounter).padStart(3, "0"), type, channel_id: channel.id, author, mentions: [], content: "" };
  const li = element(`<li id="chat-messages-${channel.id}-${message.id}" class="messageListItem__5126c"><div class="message__5126c ${compact ? "compact__5126c" : "cozyMessage__5126c"} systemMessage__5126c" role="article"><div id="message-content-${message.id}" class="markup__75297 messageContent_c19a55"><div class="container__235ca ${compact ? "compact__235ca" : "cozy__235ca"}"><div class="iconContainer__235ca"><svg class="icon__235ca"></svg></div><div class="content__235ca"><div></div></div></div></div></div></li>`);
  const wrapper = li.querySelector('[id^="message-content"]');
  const row = [{ message, channel, compact }];
  const content = { message, content: "", compact, children: null };
  fiber(wrapper, content, ...row);
  const line = li.querySelector(".content__235ca > div");
  const chain = [{ children: parts }, { className: "content__235ca" }, { className: "container__235ca" },
    { timestamp: "2026-10-28T00:31:00Z", compact, children: parts }, { message, usernameHook() {}, onClickPins() {} },
    { message, channel, compact }, { id: wrapper.id, className: wrapper.className }, content, ...row];
  const nodes = [];
  for (const part of parts) {
    if (typeof part === "string") {
      const node = document.createTextNode(part);
      fiber(node, ...chain);
      line.append(node);
      nodes.push(node);
    } else if (part.user) {
      const a = element(`<span class="anchor__14d82 anchorUnderlineOnHover__14d82" role="button" tabindex="0"><span class="container__703b9"><span class="nameContainer__703b9"><span class="name__703b9 username__703b9">${part.name}</span></span></span></span>`);
      const name = a.querySelector(".name__703b9");
      fiber(name, { className: "name__703b9 username__703b9", children: part.name }, { roleStyle: "username", name: part.name },
        { name: part.name, colorString: null }, { user: part.user, channelId: channel.id, messageId: message.id }, ...chain);
      line.append(a);
      nodes.push(name);
    } else {
      const a = element(`<a class="anchor__14d82 anchorUnderlineOnHover__14d82" role="button" tabindex="0" href="${part.href || ""}">${part.link}</a>`);
      fiber(a, { onClick() {}, children: part.link }, ...chain);
      line.append(a);
      nodes.push(a);
    }
  }
  const stamp = element(`<span class="timestamp_c19a55 timestampInline_c19a55"><time aria-label="mardi 28 octobre 2026 à ${time}" id="message-timestamp-${message.id}" datetime="2026-10-28T00:31:00.000Z">${time}</time></span>`);
  line.append(stamp);
  return { li, nodes, message, stamp: stamp.querySelector("time"), wrapper };
}
// A nickname of several words that a server member chose (fictional).
const lune = { id: ID(4), username: "lune", globalName: "Lune und Sol" };
const server = { id: ID(2), type: 0, name: "general", guild_id: ID(1) };
'''

# 0.28.3, report A ("Aller sur un serveur", a paraphrase): every "Go to server" label of the current web client
# (web.33a8a649a2fda558 and its lazy chunks). Each opens a server the person ALREADY belongs to (the action is
# 345942.u, routing to the guild's last channel, or 449054.Z2 with joinedAt set, or 976860.uh, or closing the modal
# and transitioning): RGgqm1 menu item "goto-server" of the now-playing-menu (activity feed), IRoQXr the guild
# profile's CTA when IS_MEMBER, DymAQt the Hub "add guild" confirmation, cqWE2Z the directory card's button when
# joined (else VJlc0S "Rejoindre"), KLOhbO the boost settings card, M35zFB / UdYYP3 ("Aller à {guildName}", the name
# when it has at most 30 characters) the app-authorization success modal, AEfs1D ("Aller à {guildName}") the
# aria-label of a game profile's community card when joined. 3IpLLa is in the catalogue but used by no chunk.
GOTO = r'''
const luneGuild = { id: ID(1), name: "Lune und Sol", joinedAt: "2026-01-01" };
function button(text, ...chain) {
  const b = element(`<button type="button" class="button__201d5 lookFilled__201d5 sizeSmall__201d5"><div class="contents__201d5"><span class="lineClamp1__4bd52">${text}</span></div></button>`);
  const span = b.querySelector("span");
  fiber(span.firstChild, ...chain);
  fiber(span, { children: text }, ...chain);
  return { root: b, node: span.firstChild };
}
function menuItem(navId, id, text, ...chain) {
  const m = element(`<div class="menu_c1e9c4" role="menu" aria-label="Options"><div class="scroller_c1e9c4"><div role="group"><div class="item_c1e9c4 labelContainer_c1e9c4 colorDefault_c1e9c4" role="menuitem" id="${navId}-${id}" tabindex="-1"><div class="label_c1e9c4">${text}</div></div></div></div></div>`);
  const label = m.querySelector(".label_c1e9c4");
  fiber(label.firstChild, { className: "label_c1e9c4", children: text }, { id, label: text, action() {} }, ...chain);
  return { root: m, node: label.firstChild };
}
const layer = () => { const l = element('<div class="layerContainer_da8173"><div class="layer_da8173"></div></div>'); document.body.append(l); return l.firstChild; };
'''

# name -> (JS run BEFORE the translator starts, JS run after; both may use the helpers above).
SCENARIOS = {}

SCENARIOS['A1 composer of a DM, at load'] = (r'''
const c = composer(dm(ron), "Envoyer un message à @Ron", "Écrire un message, @Ron");
document.body.append(c.root);
window.c = c; window.p = showPlaceholder(c, "Envoyer un message à @Ron");
''', r'''
check("A1 DM composer placeholder at load", "4c+CAx in SlateTextArea's placeholder div (sibling of the editor)", p.textContent, "Mandà un messaghju à @Ron");
check("A1 DM composer editor aria-label", "fqOxbV on the editor (role textbox, contenteditable)", c.editor.getAttribute("aria-label"), "Scrive un messaghju, @Ron");
watch("A1 placeholder", () => p.textContent); watch("A1 aria-label", () => c.editor.getAttribute("aria-label"));
''')

SCENARIOS['A2 composer: type a draft, erase it'] = (r'''
const c = composer(dm(ron), "Envoyer un message à @Ron", "Écrire un message, @Ron");
document.body.append(c.root);
window.c = c; showPlaceholder(c, "Envoyer un message à @Ron");
''', r'''
// Typing: SlateTextArea removes its placeholder div, Slate writes the draft in a data-slate-string span.
c.root.querySelector("[data-slate-placeholder]").remove();
const leaf = c.editor.querySelector("[data-slate-leaf]");
leaf.innerHTML = '<span data-slate-string="true">Envoyer un message</span>';
const typed = leaf.firstChild.firstChild;
c.editor.focus();
getSelection().collapse(typed, 7);
await settle();
check("A2 draft equal to a dictionary phrase is not touched", "Slate string in the editor", typed.data, "Envoyer un message");
check("A2 caret stays where it was while typing", "Selection in the draft",
  getSelection().anchorNode === typed && getSelection().anchorOffset === 7, true);
// Erasing: the editor is empty again and SlateTextArea inserts a NEW placeholder div.
leaf.innerHTML = zero;
getSelection().collapse(leaf.firstChild, 0);
const anchor = getSelection().anchorNode, offset = getSelection().anchorOffset;
const p = showPlaceholder(c, "Envoyer un message à @Ron");
await settle();
check("A2 placeholder translated again after the draft is erased", "4c+CAx, new placeholder div inserted after load", p.textContent, "Mandà un messaghju à @Ron");
check("A2 caret unchanged when the placeholder comes back", "Selection in the empty editor",
  getSelection().anchorNode === anchor && getSelection().anchorOffset === offset, true);
watch("A2 placeholder", () => p.textContent);
''')

SCENARIOS['A3 composer: another DM in the same nodes, a group'] = (r'''
const c = composer(dm(ron), "Envoyer un message à @Ron", "Écrire un message, @Ron");
document.body.append(c.root);
window.c = c; window.p = showPlaceholder(c, "Envoyer un message à @Ron");
''', r'''
// Navigation to the DM with Error: React keeps the component, gives the div's text node and the editor's label the
// new values and the components above them the new channel.
c.records[1].channel = dm(error);
p.firstChild.data = "Envoyer un message à @Error";
p.__reactProps$test = { children: "Envoyer un message à @Error" };
c.editor.setAttribute("aria-label", "Écrire un message, @Error");
await settle();
check("A3 DM composer placeholder after navigation (node reused)", "4c+CAx, text node reused", p.textContent, "Mandà un messaghju à @Error");
check("A3 DM composer aria-label after navigation", "fqOxbV, attribute changed", c.editor.getAttribute("aria-label"), "Scrive un messaghju, @Error");
// A group DM (type 3): 8lzR/R with the name Discord composes from the members.
const g = composer(group(work, error), "Envoyer un message dans Work, Error", "Écrire un message, salon textuel Work, Error");
document.body.append(g.root);
const q = showPlaceholder(g, "Envoyer un message dans Work, Error");
await settle();
check("A3 group DM composer placeholder inserted after load", "8lzR/R in SlateTextArea's placeholder div", q.textContent, "Mandà un messaghju in Work, Error");
watch("A3 placeholder", () => p.textContent); watch("A3 group placeholder", () => q.textContent);
''')

SCENARIOS['B1 DM search bar: wording'] = (r'''
window.bar = searchBar(dm(ron), "Ron");
document.body.append(bar);
''', r'''
const span = bar.querySelector("[data-slate-placeholder]");
check("B1 DM search placeholder wording", "LDZtFO 'Rechercher {name}' (Search {name}), name = the conversation", span.textContent, "Circà in Ron", "proposal");
check("B1 DM search aria-label wording", "LDZtFO on the combobox", bar.querySelector('[role="combobox"]').getAttribute("aria-label"), "Circà in Ron", "proposal");
check("B1 name Ron kept", "LDZtFO", span.textContent.endsWith("Ron"), true);
watch("B1 placeholder", () => span.textContent);
''')

SCENARIOS['B2 DM search bar: open, type, clear, reopen, navigate'] = ('', r'''
// Opened after load.
let bar = searchBar(dm(ron), "Ron");
document.body.append(bar);
await settle();
check("B2 search placeholder when the bar appears after load", "LDZtFO, Slate placeholder span", bar.querySelector("[data-slate-placeholder]").textContent, translatedSearch("Ron"));
// Typing "Work": Slate drops the placeholder from the leaf and writes the query.
const leaf = bar.querySelector("[data-slate-leaf]");
leaf.innerHTML = '<span data-slate-string="true">Rechercher Work</span>';
await settle();
check("B2 typed query left alone", "Slate string in the search editor", leaf.textContent, "Rechercher Work");
// Clearing: a new placeholder span.
leaf.innerHTML = '<span data-slate-placeholder="true" contenteditable="false">Rechercher Ron</span><span data-slate-zero-width="n" data-slate-length="0">﻿<br></span>';
fiber(leaf.firstChild, { contentEditable: false, children: "Rechercher Ron" }, { leaf: { placeholder: "Rechercher Ron" } });
await settle();
check("B2 placeholder after the query is cleared", "LDZtFO, new placeholder span", leaf.firstChild.textContent, translatedSearch("Ron"));
// Closed and reopened (unmounted, mounted again).
bar.remove();
await settle();
bar = searchBar(dm(ron), "Ron");
document.body.append(bar);
await settle();
check("B2 placeholder after the bar is closed and reopened", "LDZtFO", bar.querySelector("[data-slate-placeholder]").textContent, translatedSearch("Ron"));
// Navigation, text node reused (same editor, new placeholder text and label).
const span = bar.querySelector("[data-slate-placeholder]"), box = bar.querySelector('[role="combobox"]');
span.firstChild.data = "Rechercher Error";
box.setAttribute("aria-label", "Rechercher Error");
await settle();
check("B2 placeholder after navigation, node reused", "LDZtFO, text node reused", span.textContent, translatedSearch("Error"));
check("B2 aria-label after navigation", "LDZtFO, attribute changed", box.getAttribute("aria-label"), translatedSearch("Error"));
// Navigation, remounted (the bar is keyed by search context).
bar.remove();
const other = searchBar(dm(work), "Work");
document.body.append(other);
await settle();
check("B2 placeholder after navigation, remounted, name Work kept", "LDZtFO", other.querySelector("[data-slate-placeholder]").textContent, translatedSearch("Work"));
watch("B2 placeholder", () => span.textContent); watch("B2 Work", () => other.querySelector("[data-slate-placeholder]").textContent);
''')

SCENARIOS['C1 group add notice inserted after load'] = (r'''
window.list = element('<ol class="scrollerInner__36d07" data-list-id="chat-messages"></ol>');
document.body.append(list);
''', r'''
const g = group(work, error);
const row = systemRow(g, work, [{ user: work, name: "Work" }, " a ajouté ", { user: error, name: "Error" }, " au groupe."], { otherUsername: "Error", compact: false });
list.append(row.li);
await settle();
const [adder, verb, added, end] = row.nodes;
check("C1 group add: verb", "MMN2Jq ' a ajouté ' (bare text node)", read(verb), " hà aghjuntu ");
check("C1 group add: end", "MMN2Jq ' au groupe.'", read(end), " à u gruppu.");
check("C1 group add: adder Work kept", "username hook", read(adder), "Work");
check("C1 group add: added Error kept", "otherUsername hook", read(added), "Error");
// The same row re-rendered for a removal (React reuses the text nodes).
verb.data = " a retiré "; end.data = " du groupe.";
await settle();
check("C1 node reused: remove verb", "L2FyVq ' a retiré '", read(verb), " hà cacciatu ");
check("C1 node reused: remove end", "L2FyVq ' du groupe.'", read(end), " da u gruppu.");
watch("C1 verb", () => read(verb)); watch("C1 end", () => read(end)); watch("C1 Work", () => read(adder)); watch("C1 Error", () => read(added));
''')

SCENARIOS['C2 group remove, leave, system-looking nickname'] = (r'''
window.list = element('<ol class="scrollerInner__36d07" data-list-id="chat-messages"></ol>');
document.body.append(list);
''', r'''
const g = group(work, error, fragment);
const removed = systemRow(g, error, [{ user: error, name: "Error" }, " a retiré ", { user: work, name: "Work" }, " du groupe."], { otherUser: work, compact: false });
const left = systemRow(g, work, [{ user: work, name: "Work" }, " a quitté le groupe."], { compact: false });
const odd = systemRow(g, fragment, [{ user: fragment, name: "a ajouté" }, " a ajouté ", { user: error, name: "Error" }, " au groupe."], { otherUsername: "Error", compact: false });
list.append(removed.li, left.li, odd.li);
await settle();
check("C2 group remove: verb", "L2FyVq", read(removed.nodes[1]), " hà cacciatu ");
check("C2 group remove: end", "L2FyVq", read(removed.nodes[3]), " da u gruppu.");
check("C2 group leave", "5v2xa8 ' a quitté le groupe.'", read(left.nodes[1]), " hà lasciatu u gruppu.");
check("C2 nickname 'a ajouté' kept", "username hook, nickname equal to a fragment", read(odd.nodes[0]), "a ajouté");
check("C2 fragment translated next to a nickname 'a ajouté'", "MMN2Jq, author's records hold 'a ajouté'", read(odd.nodes[1]), " hà aghjuntu ");
check("C2 removed person Work kept", "otherUsername hook", read(removed.nodes[2]), "Work");
watch("C2 remove", () => read(removed.nodes[1])); watch("C2 leave", () => read(left.nodes[1])); watch("C2 nickname", () => read(odd.nodes[0]));
''')

SCENARIOS['C3 pin notices as the current client draws them'] = (r'''
window.list = element('<ol class="scrollerInner__36d07" data-list-id="chat-messages"></ol>');
document.body.append(list);
''', r'''
const channel = dm(ron);
const pin = systemRow(channel, ron, [{ user: ron, name: "Ron" }, " a épinglé ", { link: "un message" }, " dans ce salon. Voir tous les ", { link: "messages épinglés" }, "."], { compact: false });
const plain = systemRow(channel, work, [{ user: work, name: "Work" }, " a épinglé un message dans ce salon. Voir tous les ", { link: "messages épinglés" }, "."], { compact: false });
list.append(pin.li, plain.li);
await settle();
check("C3 pin (yIDvPL): verb", "yIDvPL ' a épinglé '", read(pin.nodes[1]), " hà spirlatu ");
check("C3 pin (yIDvPL): link 'un message'", "yIDvPL $link", read(pin.nodes[2]), "un messaghju");
check("C3 pin (yIDvPL): middle", "yIDvPL ' dans ce salon. Voir tous les '", read(pin.nodes[3]), " in stu canale. Vede tutti i ");
check("C3 pin (yIDvPL): link 'messages épinglés'", "yIDvPL $link", read(pin.nodes[4]), "messaghji spirlati");
check("C3 pin (R7vZGZ): sentence", "R7vZGZ ' a épinglé un message dans ce salon. Voir tous les '", read(plain.nodes[1]), " hà spirlatu un messaghju in stu canale. Vede tutti i ");
check("C3 pin (R7vZGZ): link", "R7vZGZ $link", read(plain.nodes[2]), "messaghji spirlati");
check("C3 pin author Ron kept", "username hook", read(pin.nodes[0]), "Ron");
watch("C3 verb", () => read(pin.nodes[1])); watch("C3 link", () => read(pin.nodes[4]));
''')

SCENARIOS['C4 a real message with the same words stays'] = (r'''
window.list = element('<ol class="scrollerInner__36d07" data-list-id="chat-messages"></ol>');
document.body.append(list);
''', r'''
const li = element(`<li id="chat-messages-${ID(6)}-${ID(9)}" class="messageListItem__5126c"><div class="message__5126c cozyMessage__5126c" role="article"><div class="contents_c19a55"><h3 class="header_c19a55"><span class="headerText_c19a55"><span class="username_c19a55" role="button">Work</span></span></h3><div id="message-content-${ID(9)}" class="markup__75297 messageContent_c19a55">a ajouté Error au groupe.</div></div></div></li>`);
fiber(li.querySelector(".username_c19a55"), { children: "Work" }, { author: work, message: { id: ID(9), author: work } });
list.append(li);
await settle();
const content = li.querySelector('[id^="message-content"]');
check("C4 real message with the group notice's words stays French", "message-content, inserted after load", content.textContent, "a ajouté Error au groupe.");
check("C4 author Work kept", "message header", li.querySelector(".username_c19a55").textContent, "Work");
watch("C4 message", () => content.textContent);
''')

# The message preview line (lazy chunk 4bb013d8238b3d6b.js, MessagePreviewManager, in the rows of the friends/DM
# widget): a system message is given as ONE plain string (formatToPlainString of MMN2Jq with identity hooks) inside
# span.messageContent__7c4a2, the same span that holds a real message's parsed content (component given {message}).
SCENARIOS['C5 message preview line of a group'] = ('', r'''
const g = group(work, error);
const message = { id: ID(7), channel_id: g.id, type: 1, author: work, mentions: [error.id], content: "" };
const row = element(`<div class="messagePreviewLine__7c4a2"><span class="messageContent__7c4a2">Work a ajouté Error au groupe.</span></div>`);
fiber(row.firstChild, { className: "messageContent__7c4a2", children: [null, "Work a ajouté Error au groupe."] }, { channel: g, message });
const real = element(`<div class="messagePreviewLine__7c4a2"><span class="messageContent__7c4a2"><span>a ajouté Error au groupe.</span></span></div>`);
const userMessage = { id: ID(9), channel_id: g.id, type: 0, author: work, mentions: [], content: "a ajouté Error au groupe." };
fiber(real.firstChild.firstChild, { children: "a ajouté Error au groupe." }, { message: userMessage }, { className: "messageContent__7c4a2" }, { channel: g, message: userMessage });
document.body.append(row, real);
await settle();
check("C5 group notice in a message preview line", "MMN2Jq as one plain string in span.messageContent__7c4a2", row.textContent, "Work hà aghjuntu Error à u gruppu.");
check("C5 real message in a preview line stays French", "a message's own content in the same span", real.textContent, "a ajouté Error au groupe.");
watch("C5 preview", () => row.textContent); watch("C5 real", () => real.textContent);
''')

# --- 0.28.3: report B, the pin notice inside the message-content wrapper (see NOTICE). ---
PIN = '[{ user: lune, name: "Lune und Sol" }, " a épinglé ", { link: "un message" }, " dans ce salon. Voir tous les ", { link: "messages épinglés" }, "."]'

SCENARIOS['D0 pin notice already on the page when the translator starts'] = (r'''
window.list = element('<ol class="scrollerInner__36d07" data-list-id="chat-messages"></ol>');
document.body.append(list);
window.early = listNotice(server, lune, 6, ''' + PIN + r''');
list.append(early.li);
''', r'''
const [nick, verb, link, middle, pins] = early.nodes;
check("D0 initial render: verb", "yIDvPL in message-content, present at start", read(verb), " hà spirlatu ");
check("D0 initial render: middle", "yIDvPL", read(middle), " in stu canale. Vede tutti i ");
check("D0 initial render: links", "$link x2", read(link) + "|" + read(pins), "un messaghju|messaghji spirlati");
check("D0 initial render: nickname and time kept", "username hook, timestamp", read(nick) + "|" + early.stamp.textContent, "Lune und Sol|01:31");
watch("D0 verb", () => read(verb));
''')

SCENARIOS['D1 pin notice in the message list, inside message-content, inserted after load'] = (r'''
window.list = element('<ol class="scrollerInner__36d07" data-list-id="chat-messages"></ol>');
document.body.append(list);
''', r'''
const pin = listNotice(server, lune, 6, ''' + PIN + r''');
const anchors = Array.from(pin.li.querySelectorAll("a"));
const handlers = anchors.map(a => a.__reactProps$test.onClick);
list.append(pin.li);
await settle();
const [nick, verb, link, middle, pins, end] = pin.nodes;
check("D1 pin: verb", "yIDvPL ' a épinglé ' in message-content", read(verb), " hà spirlatu ");
check("D1 pin: link 'un message'", "yIDvPL $link messageOnClick", read(link), "un messaghju");
check("D1 pin: middle", "yIDvPL ' dans ce salon. Voir tous les '", read(middle), " in stu canale. Vede tutti i ");
check("D1 pin: link 'messages épinglés'", "yIDvPL $link pinsActionOnClick", read(pins), "messaghji spirlati");
check("D1 pin: final full stop", "yIDvPL '.'", read(end), ".");
check("D1 pin: nickname of several words kept", "username hook, 'Lune und Sol'", read(nick), "Lune und Sol");
check("D1 pin: time kept", "timestamp LT", pin.stamp.textContent, "01:31");
check("D1 pin: same link elements, same targets", "Anchors untouched (node, href, onClick)", anchors.every(a => pin.li.contains(a))
  && anchors.map(a => a.getAttribute("href")).join() === "," && anchors.every((a, i) => a.__reactProps$test.onClick === handlers[i]), true);
check("D1 pin: whole line", "visible text", pin.li.querySelector(".content__235ca").textContent,
  "Lune und Sol hà spirlatu un messaghju in stu canale. Vede tutti i messaghji spirlati.01:31");
watch("D1 verb", () => read(verb)); watch("D1 middle", () => read(middle)); watch("D1 nickname", () => read(nick));
''')

SCENARIOS['D2 pin notice re-rendered after channel navigation'] = (r'''
window.list = element('<ol class="scrollerInner__36d07" data-list-id="chat-messages"></ol>');
document.body.append(list);
''', r'''
const first = listNotice(server, lune, 6, ''' + PIN + r''');
list.append(first.li);
await settle();
// Another channel: the list is emptied and new rows are inserted (as Discord does on navigation).
list.replaceChildren();
const other = { id: ID(3), type: 0, name: "annonces", guild_id: ID(1) };
const second = listNotice(other, lune, 6, ''' + PIN + r''', { time: "23:59" });
await settle();
list.append(second.li);
await settle();
check("D2 after navigation: verb", "new row", read(second.nodes[1]), " hà spirlatu ");
check("D2 after navigation: middle", "new row", read(second.nodes[3]), " in stu canale. Vede tutti i ");
check("D2 after navigation: time kept", "timestamp", second.stamp.textContent, "23:59");
// Back to the first channel: React reuses the row and writes its French again into the same text nodes.
list.replaceChildren(first.li);
first.nodes[1].data = " a épinglé "; first.nodes[3].data = " dans ce salon. Voir tous les ";
await settle();
check("D2 back, text nodes rewritten by React: verb", "reused node", read(first.nodes[1]), " hà spirlatu ");
check("D2 back, text nodes rewritten by React: middle", "reused node", read(first.nodes[3]), " in stu canale. Vede tutti i ");
check("D2 back: nickname kept", "username hook", read(first.nodes[0]), "Lune und Sol");
watch("D2 verb", () => read(first.nodes[1])); watch("D2 second", () => read(second.nodes[3]));
''')

SCENARIOS['D3 a person writing the pin sentence keeps it'] = (r'''
window.list = element('<ol class="scrollerInner__36d07" data-list-id="chat-messages"></ol>');
document.body.append(list);
''', r'''
// A person's message (type 0) in the same wrapper, with the notice's words, whole and split in nodes.
const said = listNotice(server, lune, 0, ["a épinglé un message dans ce salon. Voir tous les messages épinglés."]);
const split = listNotice(server, lune, 0, [" a épinglé ", { link: "un message" }, " dans ce salon. Voir tous les "]);
list.append(said.li, split.li);
await settle();
check("D3 person's sentence stays French", "type 0 in message-content", read(said.nodes[0]), "a épinglé un message dans ce salon. Voir tous les messages épinglés.");
check("D3 person's fragment stays French", "type 0, bare text node", read(split.nodes[0]), " a épinglé ");
check("D3 person's link text stays French", "type 0, link", read(split.nodes[1]), "un message");
watch("D3 said", () => read(said.nodes[0])); watch("D3 split", () => read(split.nodes[0]));
''')

SCENARIOS['D4 group notices inside message-content'] = (r'''
window.list = element('<ol class="scrollerInner__36d07" data-list-id="chat-messages"></ol>');
document.body.append(list);
''', r'''
const g = group(work, error);
const added = listNotice(g, work, 1, [{ user: work, name: "Work" }, " a ajouté ", { user: error, name: "Error" }, " au groupe."]);
const removed = listNotice(g, error, 2, [{ user: error, name: "Error" }, " a retiré ", { user: work, name: "Work" }, " du groupe."]);
list.append(added.li, removed.li);
await settle();
check("D4 group add: verb", "MMN2Jq in message-content", read(added.nodes[1]), " hà aghjuntu ");
check("D4 group add: end", "MMN2Jq", read(added.nodes[3]), " à u gruppu.");
check("D4 group remove: verb", "L2FyVq in message-content", read(removed.nodes[1]), " hà cacciatu ");
check("D4 names Work and Error kept", "username hooks", [added.nodes[0], added.nodes[2], removed.nodes[0]].map(read).join(), "Work,Error,Error");
watch("D4 add", () => read(added.nodes[1]));
''')

SCENARIOS['D5 pin notice in a message preview line'] = ('', r'''
const message = { id: ID(7), channel_id: server.id, type: 6, author: lune, mentions: [], content: "" };
const row = element(`<div class="messagePreviewLine__7c4a2"><span class="messageContent__7c4a2">Lune und Sol a épinglé un message dans ce salon. Voir tous les messages épinglés.</span></div>`);
fiber(row.firstChild, { className: "messageContent__7c4a2", children: [null, row.firstChild.textContent] }, { channel: server, message });
document.body.append(row);
await settle();
check("D5 pin notice in a preview line", "yIDvPL as one plain string, author 'Lune und Sol'", row.textContent, "Lune und Sol hà spirlatu un messaghju in stu canale. Vede tutti i messaghji spirlati.");
watch("D5 preview", () => row.textContent);
''')

# --- 0.28.3: report A, the "Go to server" labels (see GOTO). ---
SCENARIOS['E1 Go to server labels inserted after load'] = ('', r'''
const go = "Andà nant'à u servore";
const L = layer();
const party = { currentActivities: [{ activity: { name: "Ghjocu", type: 0 }, application: { name: "Ghjocu" } }], voiceChannels: [] };
const menu = menuItem("now-playing-menu", "goto-server", "Aller sur le serveur", { navId: "now-playing-menu" }, { party, close() {}, onSelect() {} });
const profile = button("Aller sur le serveur", { text: "Aller sur le serveur", variant: "active", size: "sm" }, { guildId: luneGuild.id, ctaType: 0 }, { guild: luneGuild });
const hub = button("Aller sur le serveur", { text: "Aller sur le serveur", variant: "primary" }, { actions: [] }, { directoryGuildName: "Lune und Sol", guildToAdd: luneGuild, isExistingGuildFlow: false });
const card = element('<div class="card__0c0bf"><div class="guildInfo__0c0bf"><div class="title__0c0bf"><span class="guildName__0c0bf">Lune und Sol</span></div><div class="joinButton__0c0bf"></div></div></div>');
const directory = button("Aller sur le serveur", { text: "Aller sur le serveur", variant: "secondary", fullWidth: true }, { entry: { guildId: luneGuild.id, name: "Lune und Sol", description: "" } });
card.querySelector(".joinButton__0c0bf").append(directory.root);
const boost = element('<div class="card__1bfce"><div class="cardHeader__1bfce"><div class="guildInfo__1bfce">Lune und Sol</div></div></div>');
const boostButton = button("Aller sur le serveur", { text: "Aller sur le serveur", variant: "secondary", size: "sm" }, { guildId: luneGuild.id, slots: [] });
boost.firstChild.append(boostButton.root);
const oauthLong = button("Aller sur le serveur", { text: "Aller sur le serveur", variant: "primary" }, { actions: [] }, { guild: { id: ID(2), name: "Un nome di servore assai longu per esse cortu" } });
const oauth = button("Aller à Lune und Sol", { text: "Aller à Lune und Sol", variant: "primary" }, { actions: [] }, { guild: luneGuild, application: { id: ID(3), name: "Bot" } });
const community = element('<div class="clickable_f9f2ca card_b1bfc6" role="button" tabindex="0" aria-label="Aller à Lune und Sol"><div class="guildName_b1bfc6">Lune und Sol</div></div>');
fiber(community, { className: "card_b1bfc6", "aria-label": "Aller à Lune und Sol", onClick() {} }, { guild: luneGuild, presenceCount: 3, memberCount: 9, ariaLabel: "Aller à Lune und Sol" }, { guild: luneGuild, layout: 0 });
L.append(menu.root, profile.root, hub.root, card, boost, oauthLong.root, oauth.root, community);
await settle();
check("E1 RGgqm1 now-playing menu item", "menu item label, activity feed menu", read(menu.node), go);
check("E1 IRoQXr guild profile button (member)", "Button text", read(profile.node), go);
check("E1 DymAQt Hub confirmation button", "Button text", read(hub.node), go);
check("E1 cqWE2Z directory card button (joined)", "Button text in card__0c0bf", read(directory.node), go);
check("E1 KLOhbO boost settings card button", "Button text", read(boostButton.node), go);
check("E1 M35zFB app authorization (long name)", "Button text", read(oauthLong.node), go);
check("E1 UdYYP3 app authorization 'Aller à {guildName}'", "Button text, guild name kept", read(oauth.node), "Andà à Lune und Sol");
check("E1 AEfs1D community card aria-label", "aria-label, guild name kept", community.getAttribute("aria-label"), "Andà à Lune und Sol");
check("E1 guild names kept", "names", card.querySelector(".guildName__0c0bf").textContent + "|" + community.textContent, "Lune und Sol|Lune und Sol");
watch("E1 menu", () => read(menu.node)); watch("E1 UdYYP3", () => read(oauth.node)); watch("E1 AEfs1D", () => community.getAttribute("aria-label"));
// The modal shown again for another server (React rewrites the same nodes).
oauth.node.data = "Aller à Lune und Sol"; community.setAttribute("aria-label", "Aller à Lune und Sol");
await settle();
check("E1 UdYYP3 rewritten by React", "same text node", read(oauth.node), "Andà à Lune und Sol");
check("E1 AEfs1D rewritten by React", "attribute set again", community.getAttribute("aria-label"), "Andà à Lune und Sol");
''')

SCENARIOS['E2 Go to server labels present when the translator starts'] = (r'''
window.early = button("Aller à Lune und Sol", { text: "Aller à Lune und Sol" }, { guild: luneGuild });
window.earlyPlain = button("Aller sur le serveur", { text: "Aller sur le serveur" }, { guild: luneGuild });
document.body.append(early.root, earlyPlain.root);
''', r'''
check("E2 UdYYP3 at load", "Button text", read(early.node), "Andà à Lune und Sol");
check("E2 IRoQXr/M35zFB at load", "Button text", read(earlyPlain.node), "Andà nant'à u servore");
watch("E2 template", () => read(early.node));
''')

SCENARIOS['E3 a person writing "Aller à Lune und Sol" keeps it'] = (r'''
window.list = element('<ol class="scrollerInner__36d07" data-list-id="chat-messages"></ol>');
document.body.append(list);
''', r'''
const said = listNotice(server, lune, 0, ["Aller à Lune und Sol"]);
list.append(said.li);
await settle();
check("E3 person's message stays French", "type 0 in message-content", read(said.nodes[0]), "Aller à Lune und Sol");
''')

RUN = r'''
(async () => {
const translator = CorsuBuilt.createTranslator(document);
translator.start();
await settle();
await (async () => { %s })();
await settle();
const before = watched.map(w => w.read());
for (let pass = 0; pass < 2; pass++) {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) if (!node.parentElement.closest('[contenteditable="true"]')) node.data = node.data;
  for (const el of document.querySelectorAll("[aria-label]")) el.setAttribute("aria-label", el.getAttribute("aria-label"));
  await settle();
}
const second = CorsuBuilt.createTranslator(document);
second.start();
await settle();
second.stop();
watched.forEach((w, index) => check(w.name + " unchanged by write-back and a second translator", "no double translation", w.read(), before[index]));
translator.stop();
return JSON.stringify(results);
})()
'''


def main(chrome, vencord):
    failures = []
    with tempfile.TemporaryDirectory(prefix='corsu-regressions-', ignore_cleanup_errors=True) as folder:
        _, url = extract(vencord, folder)
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1', 0))
            port = reserve.getsockname()[1]
        command = [chrome, '--headless=new', '--disable-gpu', f'--user-data-dir={folder}/profile',
                   f'--remote-debugging-port={port}', '--no-first-run', 'about:blank']
        if sys.platform.startswith('linux'):
            command.insert(1, '--no-sandbox')
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(120):
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/version', timeout=2) as response:
                        endpoint = json.load(response)['webSocketDebuggerUrl']
                    break
                except OSError:
                    time.sleep(0.5)
            devtools = DevTools(endpoint)
            for scenario, (before, after) in SCENARIOS.items():
                target = devtools.call('Target.createTarget', {'url': url})['targetId']
                session = devtools.call('Target.attachToTarget', {'targetId': target, 'flatten': True})['sessionId']
                for _ in range(200):
                    if evaluate(devtools, session, 'Boolean(window.CorsuBuilt)'):
                        break
                    time.sleep(0.2)
                else:
                    raise SystemExit('FAIL: the built translator did not load')
                helpers = HELPERS + COMPOSER + SEARCH + SYSTEM + NOTICE + GOTO
                evaluate(devtools, session, helpers + before)
                for case in json.loads(evaluate(devtools, session, RUN.replace('%s', after))):
                    tag = 'PASS' if case['ok'] else 'FAIL'
                    note = '' if case['kind'] == 'regression' else f' [{case["kind"]}]'
                    print(f'{tag}: {case["name"]} = {case["got"]!r}'
                          + ('' if case['ok'] else f' (expected {case["expected"]!r})') + f'{note} — models {case["models"]}')
                    if not case['ok']:
                        failures.append(case['name'])
                devtools.call('Target.closeTarget', {'targetId': target})
        finally:
            process.terminate()
            process.wait(timeout=15)
    if failures:
        raise SystemExit(f'FAIL: {len(failures)} case(s): {failures}')
    print('PASS: the reported Discord regressions are fixed in this build (simulated page)')


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding='utf-8', errors='replace')
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else str(ROOT / 'Vencord'))
