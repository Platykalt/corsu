#!/usr/bin/env python3
"""The BUILT Discord plugin (Vencord's dist/renderer.js) with the REAL generated dictionary, in headless Chrome.

Usage: check_discord_built.py CHROME [VENCORD_DIR] [--strict]
The other Discord checks bundle src/discord-plugin/translate.ts with a small test dictionary. This one takes the
translator out of the bundle Discord actually loads (VENCORD_DIR/dist/renderer.js, built by installer.prepare_build
after corsu.generate()), with the dictionary embedded in it, and checks:
- the bundle: the translator revision, the dictionary fingerprint the diagnostic reports (it must equal the one computed
  from VENCORD_DIR/src/userplugins/corsu/dictionary.json), "Bio" written out as "Biugrafia" (no "Organicu" anywhere);
- simulated pages (the markup and React props of Discord's web client, as in check_discord_activity.py): the activity
  line in the direct message list and the Friends tab, games, rich presence and custom statuses equal to dictionary
  words, games shown under another name than their record's (renamed games, application names), voice channel
  statuses, names and nicknames ("Work", "Error", "Message"), server, channel and role names, names inserted in
  sentences (text, aria-label, title), long, emoji, right-to-left and separator names, the profile's "Bio" titles
  (Biugrafia) and the bio itself (kept), repeated passes, a second translator over a translated page, and nodes reused
  by React for other texts and records (navigation, activity changes);
- search fields: an <input> placeholder and label, the placeholder Slate draws in an empty editor, a bar that searches
  friends or users, with the names Discord inserts kept and what is typed left alone;
- the pin system message in the message list ([id^="chat-messages"], a name area): its sentence and its "see all
  pinned messages" link are translated as written, the author's name stays even when it is "Work", a real message with
  the same words is left alone, and a reused node is translated again after navigation;
- group DM notices in the message list ("a ajouté … au groupe.", "a retiré … du groupe.", "a quitté le groupe."): the
  fragments between the names are translated, the names stay (also "Work", "Error", and a name that reads like a
  fragment), names inside one text node take a template, a real message stays, and reused nodes are read again;
- the hidden diagnostic: it prints none of the synthetic personal data, even dictionary words ("Work", "Error",
  "Message", "Control"), whole or in part.
Cases marked strict=false are known limits, printed as KNOWN, failing only with --strict (there are none now).
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
from check_discord_content import HELPERS  # noqa: E402
from check_discord_names import evaluate  # noqa: E402
from check_discord_activity import fingerprint  # noqa: E402

# Takes the Corsu module out of the minified bundle: from the dictionary literal (found by one of its entries) to the
# plugin's settings, and finds the minified names of its functions from the plugin's start() and their own code.
EXTRACT = r"""
const fs = require("fs");
const s = fs.readFileSync(process.argv[1], "utf8");
const start = s.lastIndexOf("var ", s.indexOf('"Dans un appel":'));
const end = s.search(/var \w+=\w+\(\{showOriginal:/);
if (start < 0 || end < start) throw new Error("Corsu module not found in the bundle");
const body = s.slice(start, end), plugin = s.slice(end, s.indexOf("permanent:", end));
const pick = (text, pattern) => (text.match(pattern) || [])[1];
const names = {
  createTranslator: pick(plugin, /=(\w+)\(document,\{showOriginal/),
  setCorrections: pick(plugin, /try\{(\w+)\(JSON\.parse/),
  dictionaryFingerprint: pick(plugin, /dictionary:(\w+)\(\)/),
  revision: pick(plugin, /revision:(\w+),dictionary/),
  translateLabel: pick(body, /function (\w+)\(e,i=new Set(?:,\w+=!1)?\)\{let \w+=e\.match/),
};
for (const [key, value] of Object.entries(names)) if (!value) throw new Error("not found in the bundle: " + key);
const exported = Object.entries(names).map(([key, value]) => `${key}:${value}`).join(",");
fs.writeFileSync(process.argv[2], `(function(){${body}\nwindow.CorsuBuilt={${exported}};})();\n`);
"""

CASES = HELPERS + r'''
window.cases = [];
const ID = n => String(n).repeat(18).slice(0, 18);
const user = (n, g) => ({ id: ID(n), username: "u" + n, globalName: g });
const work = user(1, "Work"), error = user(2, "Error"), paris = user(3, "Paris"), sep = user(4, "Paul | Work"),
      longName = user(5, "Work ".repeat(70).trim()), emoji = user(6, "🔥🔥"), rtl = user(7, "محمد Work");
const dm = p => ({ id: "9" + p.id.slice(1), type: 1, name: "", recipients: [p.id],
  rawRecipients: [{ id: p.id, username: p.username, global_name: p.globalName }], nicks: {} });
const status = (p, activities, voiceChannel = null) => ({ user: p, activities, voiceChannel, applicationStream: null });
const row = (p, activities) => ({ user: p, activities, applicationStream: null, status: "online" });
const game = name => ({ type: 0, name, application_id: "999999999999999999" });
const custom = state => ({ type: 4, name: "Custom Status", state, emoji: null });
// strict: false marks a known limit of this branch (expected = what should happen).
function add(name, html, chain, expected, attr, strict = true) { cases.push({ name, html, chain, expected, attr, strict }); }
// After the first passes, React reuses the case's node for something else (navigation, an activity that changes).
function then(name, text, chain, expected) { cases.find(c => c.name === name).next = { text, chain, expected }; }
const subtext = inner => `<div class="userInfo__0a06e"><div class="subtext__0a06e"><div class="container_c9d15c">${inner}</div></div></div>`;
const dmLine = inner => `<a class="link__972a0 channelNameFade__972a0" href="/channels/@me/1"><div class="subText__20a53">${inner}</div></a>`;
const card = inner => `<div class="userProfile_x"><div class="activityCard_x">${inner}</div></div>`;

add("DM list call label", dmLine(`<div id="t" class="activityStatusText__972a0">Dans un appel</div>`),
  [{ variant: "x" }, { text: "Dans un appel" }, { channel: dm(work) }, status(work, [], dm(work)),
   { channel: dm(work), user: work, activities: [], voiceChannel: dm(work) }], "In una chjama");
add("DM list call aria-label", dmLine(`<div id="t" class="textWithIconContainer_c9d15c" aria-label="Dans un appel (Work)"></div>`),
  [{ text: "Dans un appel", "aria-label": "Dans un appel (Work)" }, { channel: dm(work) }, status(work, [], dm(work))],
  "In una chjama (Work)", "aria-label");
add("DM list call aria-label, name with separator", dmLine(`<div id="t" class="textWithIconContainer_c9d15c" aria-label="Dans un appel (Paul | Work)"></div>`),
  [{ text: "Dans un appel" }, { channel: dm(sep) }, status(sep, [], dm(sep))], "In una chjama (Paul | Work)", "aria-label");
add("Friends tab call label", subtext(`<div id="t" class="statusText__19b6d">Dans un appel</div>`),
  [{ variant: "x" }, { text: "Dans un appel" }, { channel: dm(work) }, status(error, [], dm(work)), row(error, [])], "In una chjama");
for (const name of ["Work", "Control", "Terminal", "Paris", "Dans un appel", "Bio"]) {
  const playing = [game(name)];
  add("game " + name, subtext(`<div id="t" class="statusText__19b6d">${name}</div>`),
    [{ variant: "x" }, { text: name }, { activity: playing[0] }, status(work, playing), row(work, playing)], name);
  add("game aria-label " + name, subtext(`<div id="t" class="textWithIconContainer_c9d15c" aria-label="Joue à ${name}"></div>`),
    [{ text: name, "aria-label": "Joue à " + name }, { activity: playing[0] }, status(work, playing), row(work, playing)],
    "Ghjoca à " + name, "aria-label");
}
for (const text of ["Dans un appel", "Work", "Bio", "En ligne", "Ne pas déranger", "Envoyer", "Créer un salon", "Joue à Work"]) {
  const typed = [custom(text)];
  add("custom status (Friends) " + text, subtext(`<div id="t" class="statusText__19b6d">${text}</div>`),
    [{ variant: "x" }, { customStatusActivity: typed[0] }, status(error, typed), row(error, typed)], text);
  add("custom status (DM list) " + text, dmLine(`<div id="t" class="activityStatusText__972a0">${text}</div>`),
    [{ variant: "x" }, { customStatusActivity: typed[0] }, status(error, typed), { channel: dm(error), user: error, activities: typed }], text);
}
{
  const typed = [{ ...custom("Dans un appel"), emoji: { name: "🔥" } }];
  add("custom status after its emoji", subtext(`<div class="statusText__19b6d"><img alt="🔥"><span id="t"> Dans un appel</span></div>`),
    [{ children: " Dans un appel" }, { customStatusActivity: typed[0] }, status(error, typed), row(error, typed)], " Dans un appel");
}
{
  const presence = { type: 0, name: "Control", details: "Work", state: "Dans un appel", party: { size: [1, 4] },
    assets: { large_text: "Paris", small_text: "Bio" }, buttons: ["Envoyer"] };
  const props = [{ activity: presence, user: work }];
  add("rich presence name", card(`<div id="t" class="activityName_x">Control</div>`), props, "Control");
  add("rich presence details", card(`<div id="t" class="details_x">Work</div>`), props, "Work");
  add("rich presence state", card(`<div id="t" class="state_x">Dans un appel</div>`), props, "Dans un appel");
  add("rich presence image text", card(`<div id="t" class="assets_x" aria-label="Paris"></div>`), props, "Paris", "aria-label");
  add("rich presence button", card(`<button id="t">Envoyer</button>`), props, "Envoyer");
  add("rich presence details in an activity-classed header", card(`<h3 id="t" class="activityHeader_x">Work</h3>`), props, "Work");
  add("activity card label around the game", card(`<h3 id="t" class="activityHeader_x">Joue à Control</h3>`), props, "Ghjoca à Control");
  // A value from the records with text added by Discord (the party size): the template "Dans un appel ({1})" must not
  // take it (it did in Corsu 0.23.0).
  add("rich presence state with party size", card(`<div id="t" class="state_x">Dans un appel (1 sur 4)</div>`), props,
    "Dans un appel (1 sur 4)");
}
// Games shown under another name than their record's (a detectable application's name, a renamed game): in an activity
// area only Discord's own labels are translated, so these stay as written (in 0.23.0 and 0.24 "Control" became
// "Cuntrollu"); Discord's template around them is still translated.
const renamed = game("control.exe");
add("game shown under another name than its record", subtext(`<div id="t" class="statusText__19b6d">Control</div>`),
  [{ variant: "x" }, { activity: renamed }, status(work, [renamed]), row(work, [renamed])], "Control");
add("renamed game aria-label", subtext(`<div id="t" class="textWithIconContainer_c9d15c" aria-label="Joue à Control"></div>`),
  [{ text: "Control", "aria-label": "Joue à Control" }, { activity: renamed }, status(work, [renamed]), row(work, [renamed])],
  "Ghjoca à Control", "aria-label");
add("renamed game in the DM list", dmLine(`<div id="t" class="activityStatusText__972a0">Message</div>`),
  [{ variant: "x" }, { activity: game("msgr") }, status(error, [game("msgr")]), { channel: dm(error), user: error, activities: [game("msgr")] }], "Message");
add("renamed game read as a date", subtext(`<div id="t" class="statusText__19b6d">Mars 2</div>`),
  [{ variant: "x" }, { activity: game("MARS2") }, status(work, [game("MARS2")]), row(work, [game("MARS2")])], "Mars 2");
add("renamed game in a profile card", card(`<div id="t" class="name_x">Control</div>`), [{ activity: renamed, user: work }], "Control");
add("renamed game in a profile card, no class", `<div class="userProfile_x"><div><div id="t">Error</div></div></div>`,
  [{ children: "Error" }, { activity: game("err.exe"), user: work }], "Error");
add("profile card header", card(`<h3 id="t" class="header_x">Joue à</h3>`), [{ activity: renamed, user: work }], "Ghjoca à");
add("call label in a profile card", `<div class="card_x"><div id="t" class="headerText_x">Dans un appel</div></div>`,
  [{ text: "Dans un appel" }, { user: work, voiceChannel: dm(work) }], "In una chjama");
add("custom status Control", subtext(`<div id="t" class="statusText__19b6d">Control</div>`),
  [{ variant: "x" }, { customStatusActivity: custom("Control") }, status(error, [custom("Control")]), row(error, [custom("Control")])], "Control");
add("voice channel status Work", `<div class="voiceChannelStatus_x"><span id="t">Work</span></div>`, [], "Work");
add("voice channel status Dans un appel", `<div class="voiceChannelStatus_x"><span id="t">Dans un appel</span></div>`, [], "Dans un appel");
add("nickname Work", `<div class="member_x"><span id="t" class="name_x">Work</span></div>`,
  [{ member: { userId: ID(8), guildId: ID(4), nick: "Work" } }], "Work");
add("nickname Error from Discord's store", `<div class="member_x"><span id="t" class="name_x">Error</span></div>`, [], "Error");
add("person named Message", `<div class="discordTag__0a06e"><span id="t" class="username__0a06e">Message</span></div>`,
  [{ user: user(9, "Message") }], "Message");
add("name in a sentence (aria-label)", `<div id="t" aria-label="Envoyer un message à @Work"></div>`, [{ user: work }],
  "Mandà un messaghju à @Work", "aria-label");
add("name Message in a sentence (aria-label)", `<div id="t" aria-label="Envoyer un message à @Message"></div>`,
  [{ user: user(9, "Message") }], "Mandà un messaghju à @Message", "aria-label");
add("name in a sentence (title)", `<div id="t" title="Profil de Error"></div>`, [{ user: error }], "Prufilu di Error", "title");
add("name in a sentence (text)", `<div id="t">Profil de Work</div>`, [{ user: work }], "Prufilu di Work");
add("friend named Work", `<div class="discordTag__0a06e"><span id="t" class="username__0a06e">Work</span></div>`, [{ user: work }, row(work, [])], "Work");
add("friend named Error", `<div class="discordTag__0a06e"><span id="t" class="username__0a06e">Error</span></div>`, [{ user: error }, row(error, [])], "Error");
add("channel named General", `<a id="t" href="/channels/4/5">General</a>`, [{ channel: { id: ID(5), name: "General", guild_id: ID(4) } }], "General");
add("role named Moderator", `<span id="t" class="roleName_x">Moderator</span>`, [{ role: { id: ID(6), name: "Moderator" } }], "Moderator");
add("server named Paris in a tooltip", `<div id="t" class="tooltip_x">Paris</div>`, [{ guild: { id: ID(4), name: "Paris" } }], "Paris");
add("label and name", `<div id="t" class="title_x">Dans un appel, Work</div>`, [{ user: work, voiceChannel: dm(work) }], "In una chjama, Work");
add("aria-label holding a name", `<div id="t" aria-label="Work"></div>`, [{ user: work }], "Work", "aria-label");
add("title holding a name", `<div id="t" title="Error"></div>`, [{ user: error }], "Error", "title");
add("very long name in a label", `<div id="t" aria-label="Dans un appel (${longName.globalName})"></div>`,
  [{ user: longName, voiceChannel: dm(longName) }], `In una chjama (${longName.globalName})`, "aria-label");
add("very long name", `<div id="t" class="username_x">${longName.globalName}</div>`, [{ user: longName }], longName.globalName);
add("emoji name in a label", `<div id="t" aria-label="Dans un appel (🔥🔥)"></div>`, [{ user: emoji, voiceChannel: dm(emoji) }], "In una chjama (🔥🔥)", "aria-label");
add("right-to-left name in a label", `<div id="t" aria-label="Dans un appel (محمد Work)"></div>`, [{ user: rtl, voiceChannel: dm(rtl) }], "In una chjama (محمد Work)", "aria-label");
add("game named like a template", subtext(`<div id="t" class="statusText__19b6d">Bobby de Paris</div>`),
  [{ variant: "x" }, { activity: game("Bobby de Paris") }, status(paris, [game("Bobby de Paris")])], "Bobby de Paris");
add("profile Bio heading", `<div class="userProfile_x"><h2 id="t" class="defaultColor_x">Bio</h2></div>`, [{ user: work }], "Biugrafia");
add("settings Bio section title", `<div class="sectionTitle_x"><h3 id="t" class="title_x">Bio</h3></div>`, [], "Biugrafia");
add("server Bio title", `<div class="sectionTitle_x"><h3 id="t" class="title_x">Bio du serveur</h3></div>`, [], "Biugrafia di u servore");
add("bio editor content Bio", `<div class="bioEditor_x"><div id="t" contenteditable="true">Bio</div></div>`, [{ user: work }], "Bio");
add("bio text Bio", `<div class="userBio_x"><div id="t" class="markup_x">Bio</div></div>`, [{ user: work }], "Bio");
add("bio text Dans un appel", `<div class="bio_x"><span id="t">Dans un appel</span></div>`, [{ user: work }], "Dans un appel");
add("Créer un salon", `<button id="t">Créer un salon</button>`, [], "Creà un canale");
// "Supprimer" is Discord's Delete and Remove: in a dialog it takes the verb of the title, elsewhere the dictionary's.
add("Supprimer in a delete dialog", `<div role="dialog"><h1 class="title_x">Supprimer le message</h1><button id="t">Supprimer</button></div>`,
  [], "Squassà");
add("Supprimer in a menu", `<div role="menu"><div id="t" role="menuitem">Supprimer</div></div>`, [], "Caccià");
add("person named Supprimer in a delete dialog", `<div role="dialog"><h1 class="title_x">Supprimer le message</h1><span id="t" class="username_x">Supprimer</span></div>`,
  [{ user: user(9, "Supprimer") }], "Supprimer");
add("message", `<div id="message-content-1" class="markup_x"><span id="t">Dans un appel</span></div>`, [], "Dans un appel");
// Search fields (seen in French on the maintainer's Discord, 2026-10-23): the Friends page's <input>, the placeholder
// over a group DM (drawn by Slate inside the empty editor; Discord composes the name from the members) and over a
// server; the names stay as written, what is typed and a field inside a message stay as they are.
const group = { id: ID(5), type: 3, name: "", recipients: [ID(1), ID(2)] };
const slate = text => `<div class="search_x"><div class="editor_x" role="combobox" contenteditable="true"><div data-slate-node="element"><span data-slate-node="text"><span data-slate-leaf="true"><span id="t" data-slate-placeholder="true" contenteditable="false">${text}</span></span></span></div></div></div>`;
add("Friends search placeholder", `<div class="peopleColumn_x"><input id="t" class="input_x" placeholder="Rechercher" aria-label="Rechercher"></div>`, [], "Circà", "placeholder");
add("Friends search label", `<div class="peopleColumn_x"><input id="t" class="input_x" placeholder="Rechercher" aria-label="Rechercher"></div>`, [], "Circà", "aria-label");
add("group DM search placeholder (Slate)", slate("Rechercher EnzoParisi, Moz_One"), [{ channel: group }], "Circà in EnzoParisi, Moz_One");
add("DM search placeholder with a dictionary word as name", slate("Rechercher Work"), [{ channel: dm(work) }], "Circà in Work");
add("server search placeholder", `<input id="t" placeholder="Rechercher Work, Error">`, [{ guild: { id: ID(4), name: "Work, Error" } }],
  "Circà in Work, Error", "placeholder");
add("search text being typed", `<div contenteditable="true"><span id="t" data-slate-string="true">Rechercher Work</span></div>`, [], "Rechercher Work");
add("field inside a message", `<div id="message-content-2" class="markup_x"><input id="t" placeholder="Rechercher"></div>`, [], "Rechercher", "placeholder");
// A bar that searches friends or users (the friends list, the "new DM"/"add member" pickers): a whole phrase of the
// Discord section, reached as a field's placeholder (the Ctrl+F box over a group DM is the Slate case above).
add("friend/user search bar", `<input id="t" placeholder="Rechercher des amis ou des membres de serveur">`, [],
  "Circà amichi o membri di servore", "placeholder");
// Pin system message (seen in French on the maintainer's Discord): "{author} a épinglé un message dans ce salon. Voir
// tous les messages épinglés." sits in the message list ([id^="chat-messages"], a name area), with the author in a
// separate username element and the last clause a link. The sentence and the link are translated as written, the
// author's name stays even as "Work", and a real message with the same words (in a content area) is left alone.
const pinRow = inner => `<li id="chat-messages-${ID(4)}-${ID(5)}" class="messageListItem_x"><div class="systemMessage_x">${inner}</div></li>`;
add("pin notice sentence", pinRow(`<span class="username_x" role="button">Work</span><span id="t"> a épinglé un message dans ce salon. </span>`),
  [{ user: work }], " hà spirlatu un messaghju in stu canale. ");
add("pin notice link", pinRow(`<span id="t" role="button" class="anchor_x">Voir tous les messages épinglés.</span>`), [],
  "Vede tutti i messaghji spirlati.");
add("pin notice in one node", pinRow(`<span id="t">a épinglé un message dans ce salon. Voir tous les messages épinglés.</span>`), [],
  "hà spirlatu un messaghju in stu canale. Vede tutti i messaghji spirlati.");
add("pin author named Work stays", pinRow(`<span id="t" class="username_x" role="button">Work</span><span> a épinglé un message dans ce salon.</span>`),
  [{ user: work }], "Work");
add("real message equal to the pin phrase", `<div id="message-content-3" class="markup_x"><span id="t">a épinglé un message dans ce salon. Voir tous les messages épinglés.</span></div>`,
  [], "a épinglé un message dans ce salon. Voir tous les messages épinglés.");
// If Discord instead draws the author's name inside the sentence's own text node, the exact-phrase path no longer
// matches and a template keeps the name (a protected value, even when it is the dictionary word "Error") and
// translates the fixed parts: one node for the whole notice, and the sentence alone when the link is drawn apart.
add("pin notice inline author Error (one node)", pinRow(`<span id="t">Error a épinglé un message dans ce salon. Voir tous les messages épinglés.</span>`),
  [{ user: error }], "Error hà spirlatu un messaghju in stu canale. Vede tutti i messaghji spirlati.");
add("pin notice inline author Work, link apart", pinRow(`<span id="t">Work a épinglé un message dans ce salon. </span><span role="button" class="anchor_x">Voir tous les messages épinglés.</span>`),
  [{ user: work }], "Work hà spirlatu un messaghju in stu canale. ");

// Group DM notices (seen in French on the maintainer's Discord, "a ajouté au groupe"): "{username} a ajouté
// {otherUsername} au groupe." (keys 7/Xl0S, MMN2Jq), "… a retiré … du groupe.", "… a quitté le groupe.", in the message
// list with each name its own element: the fragments between the names are translated, both names stay, even "Work"
// and "Error"; a real message with the same words is left alone; a name that reads like a fragment stays.
const groupDm = { id: ID(6), type: 3, name: "", recipients: [ID(1), ID(2)] };
const groupRow = inner => `<li id="chat-messages-${ID(6)}-${ID(7)}" class="messageListItem_x"><div class="systemMessage_x">${inner}</div></li>`;
const link = name => `<span class="username_x" role="button">${name}</span>`;
add("group add: verb between two names", groupRow(`${link("Work")}<span id="t"> a ajouté </span>${link("Error")}<span> au groupe.</span>`),
  [{ channel: groupDm }], " hà aghjuntu ");
add("group add: end of sentence", groupRow(`${link("Work")}<span> a ajouté </span>${link("Error")}<span id="t"> au groupe.</span>`),
  [{ channel: groupDm }], " à u gruppu.");
add("group add: adder named Work stays", groupRow(`<span id="t" class="username_x" role="button">Work</span><span> a ajouté </span>${link("Error")}<span> au groupe.</span>`),
  [{ user: work }], "Work");
add("group add: added person named Error stays", groupRow(`${link("Work")}<span> a ajouté </span><span id="t" class="username_x" role="button">Error</span><span> au groupe.</span>`),
  [{ user: error }], "Error");
add("group remove: verb", groupRow(`${link("Error")}<span id="t"> a retiré </span>${link("Work")}<span> du groupe.</span>`),
  [{ channel: groupDm }], " hà cacciatu ");
add("group remove: end of sentence", groupRow(`${link("Error")}<span> a retiré </span>${link("Work")}<span id="t"> du groupe.</span>`),
  [{ channel: groupDm }], " da u gruppu.");
add("group leave", groupRow(`${link("Work")}<span id="t"> a quitté le groupe.</span>`), [{ channel: groupDm }], " hà lasciatu u gruppu.");
add("group add: names inside one text node", groupRow(`<span id="t">Work a ajouté Error au groupe.</span>`),
  [{ channel: groupDm }, { users: [work, error] }], "Work hà aghjuntu Error à u gruppu.");
add("group leave: name inside the text node", groupRow(`<span id="t">Error a quitté le groupe.</span>`),
  [{ user: error }], "Error hà lasciatu u gruppu.");
// The last message of a conversation shown under its name in a conversation list (chunk 4bb013d8238b3d6b: MMN2Jq
// written with formatToPlainString and identity hooks, so both names are inside one text node, in a <span>).
add("group add in a conversation list preview", `<div class="secondaryText_x"><div class="text_x"><span id="t" class="preview_x">Work a ajouté Error au groupe.</span></div></div>`,
  [{ channel: groupDm, message: { id: ID(7), author: work, mentions: [error.id] } }], "Work hà aghjuntu Error à u gruppu.");
add("group add preview inside a conversation link", `<a href="/channels/@me/${ID(6)}"><span id="t" class="preview_x">Error a ajouté Work au groupe.</span></a>`,
  [{ channel: groupDm, message: { id: ID(7), author: error, mentions: [work.id] } }], "Error hà aghjuntu Work à u gruppu.");
add("real message equal to the group phrase", `<div id="message-content-4" class="markup_x"><span id="t">a ajouté au groupe.</span></div>`,
  [], "a ajouté au groupe.");
add("person named like a fragment stays", groupRow(`<span id="t" class="username_x" role="button">a ajouté</span><span> a quitté le groupe.</span>`),
  [{ user: user(8, "a ajouté") }], "a ajouté");

then("game Control", "Dans un appel", [{ variant: "x" }, { text: "Dans un appel" }, { channel: dm(work) },
  status(work, [], dm(work)), row(work, [])], "In una chjama");
then("DM list call label", "Control", [{ variant: "x" }, { activity: game("ctrl.exe") }, status(work, [game("ctrl.exe")]),
  { channel: dm(work), user: work, activities: [game("ctrl.exe")], voiceChannel: null }], "Control");
then("renamed game in a profile card", "Work", [{ activity: game("Work"), user: error }], "Work");
then("friend named Work", "Error", [{ user: error }, row(error, [])], "Error");
then("name in a sentence (aria-label)", "Envoyer un message à @Error", [{ user: error }], "Mandà un messaghju à @Error");
then("custom status (Friends) Dans un appel", "Joue à Control", [{ variant: "x" }, { customStatusActivity: custom("Joue à Control") },
  status(error, [custom("Joue à Control")]), row(error, [custom("Joue à Control")])], "Joue à Control");
then("Créer un salon", "Envoyer", [], "Mandà");
// Navigating to another channel reuses the node for its own pin notice: translated again from French.
then("pin notice in one node", "a épinglé un message dans ce salon. Voir tous les messages épinglés.", [],
  "hà spirlatu un messaghju in stu canale. Vede tutti i messaghji spirlati.");
// Another group conversation shown in the same nodes: its notices are translated again, its names kept.
then("group add: verb between two names", " a retiré ", [{ channel: groupDm }], " hà cacciatu ");
then("group add: end of sentence", " du groupe.", [{ channel: groupDm }], " da u gruppu.");
then("group add: added person named Error stays", "Work", [{ user: work }], "Work");
// The same node, reused for another author, keeps the name (never read as a system label).
then("pin author named Work stays", "Error", [{ user: error }], "Error");

for (const c of cases) {
  const host = document.createElement("div");
  host.innerHTML = c.html;
  document.body.append(host);
  c.element = host.querySelector("#t");
  c.element.removeAttribute("id");
  if (c.chain.length) mount(c.element, ...c.chain);
}
'''

RUN = r'''
(async () => {
const settle = () => new Promise(resolve => setTimeout(resolve, 30));
const read = c => c.attr ? c.element.getAttribute(c.attr) : c.element.textContent;
window.translator = CorsuBuilt.createTranslator(document);
translator.start();
await settle();
const first = cases.map(read);
// The page writes back what it shows, three times; then a second translator (fresh memory) reads the translated page.
for (let pass = 0; pass < 3; pass++) {
  for (const c of cases) {
    if (c.attr) c.element.setAttribute(c.attr, c.element.getAttribute(c.attr));
    else for (const node of c.element.childNodes) if (node.nodeType === Node.TEXT_NODE) node.data = node.data;
  }
  await settle();
}
const second = CorsuBuilt.createTranslator(document);
second.start();
await settle();
second.stop();
const last = cases.map(read);
// Navigation: the nodes are reused for other texts and records, then written back twice.
for (const c of cases.filter(c => c.next)) {
  const chain = c.next.chain.length ? c.next.chain : [{}];
  if (!c.element.__reactFiber$test) c.element.firstChild.data = c.next.text;  // no React records: only the text changes
  else if (c.attr) { rerender(c.element, null, ...chain); c.element.setAttribute(c.attr, c.next.text); }
  else rerender(c.element, c.next.text, ...chain);
}
await settle();
const moved = cases.map(read);
for (let pass = 0; pass < 2; pass++) {
  for (const c of cases.filter(c => c.next)) {
    if (c.attr) c.element.setAttribute(c.attr, c.element.getAttribute(c.attr));
    else for (const node of c.element.childNodes) if (node.nodeType === Node.TEXT_NODE) node.data = node.data;
  }
  await settle();
}
return JSON.stringify(cases.map((c, index) => ({ name: c.name, expected: c.expected, strict: c.strict, first: first[index],
  last: last[index], next: c.next?.expected, moved: moved[index], movedLast: read(c) })));
})()
'''

# The diagnostic with synthetic personal data: in places Discord shows what people chose without a name class or React
# records nearby, and names, nicknames, games and statuses that are dictionary words ("Work", "Error", "Message",
# "Control"), whole or in part. Nothing of it should be printed.
PRIVACY = HELPERS + r'''
(async () => {
const bob = { id: "111111111111111111", username: "bob.prive", globalName: "Bobette Secretnom" };
document.body.innerHTML = `
  <div class="connectedAccountNameText_x">Jérôme Martindale</div>
  <div class="pronouns_x">elle/la sienne</div>
  <div class="voiceChannelStatus_x">On joue à des jeux de la nuit</div>
  <div class="channel_x"><span class="username_x">Paris</span></div>
  <div class="subText_x"><div class="activityStatusText_x">En route pour Ajaccio avec Léa</div></div>
  <div id="emoji" aria-label=":chat_de_Mélanie:"></div>
  <div class="userBio_x"><div class="markup_x">Ma bio très privée</div></div>
  <div id="message-content-9" class="markup_x">Message ultra secret de Bobette</div>
  <div id="withRecords">Appel avec Bobette Secretnom en cours</div>
  <div class="discordTag_x"><span class="username_x">Work</span></div>
  <div class="member_x"><span class="name_x">Error</span></div>
  <div class="nickname_x">Message</div>
  <div class="customStatus_x">Travail du soir</div>
  <div class="voiceChannelStatus_x">Soirée Control</div>
  <h1 id="dmTitle" class="title_x">Error Work</h1>
  <div id="callLabel" aria-label="Dans un appel (Error Work)"></div>
  <div id="partial">Appel avec Work en cours</div>
  <div id="subtext" class="subtext_x"><div id="renamed" class="statusText_x">Control</div></div>`;
mount(document.getElementById("withRecords"), { user: bob });
const ew = { id: "222222222222222222", username: "ew", globalName: "Error Work" };
mount(document.getElementById("dmTitle"), { channel: { id: "333333333333333333", type: 1, name: "", recipients: [ew.id],
  rawRecipients: [{ id: ew.id, username: "ew", global_name: "Error Work" }] } });
mount(document.getElementById("callLabel"), { user: ew, voiceChannel: { id: "333333333333333333", type: 1, name: "" } });
mount(document.getElementById("partial"), { user: ew });
mount(document.getElementById("renamed"), { activity: { type: 0, name: "control.exe" } }, { user: ew, activities: [{ type: 0, name: "control.exe" }] });
const translator = CorsuBuilt.createTranslator(document);
translator.start();
await new Promise(resolve => setTimeout(resolve, 30));
const fresh = document.createElement("div");
fresh.textContent = "Jérôme Martindale, Envoyer";
document.body.append(fresh);
// Shown before the translator sees them (the report runs first): a renamed game and a nickname.
const line = document.createElement("div");
line.className = "subtext_y";
line.innerHTML = '<div class="statusText_y">Message</div><span class="username_y">Error</span>';
document.body.append(line);
mount(line.firstChild, { activity: { type: 0, name: "msgr" } }, { user: ew, activities: [{ type: 0, name: "msgr" }] });
const output = JSON.stringify(translator.report());
return JSON.stringify(["Jérôme", "Martindale", "elle/la sienne", "nuit", "Paris", "Ajaccio", "Léa", "Mélanie", "bio très",
  "secret", "Bobette", "Secretnom", "bob.prive", "Work", "Error", "Message", "Control", "Travail", "Soirée"]
  .filter(word => output.includes(word)));
})()
'''

# Pages that change after the translator started, built from the structures of Discord's public web client (build
# web.ad0b95d8568e0f6b, read 2026-10-27; French keys from its fr chunk). Each step is checked in order; this is a
# simulated page, not the real app.
# - DM composer: SlateTextArea (module 655098) draws `placeholder` in a <div class="placeholder__1b31f …"
#   aria-hidden data-slate-placeholder="true"> BESIDE the editor (<div class="markup__75297 editor__1b31f …"
#   role="textbox" contenteditable aria-label={placeholder}>), only while the draft is empty (state.showPlaceholder);
#   the text is 4c+CAx "Envoyer un message à {channel}" with channel "@{name}" (module 480870).
# - Message search: the Slate search bar (chunk c5b5c25ec8ff16aa) is an Editable role="combobox" with
#   aria-label={placeholder} and Slate's own placeholder span inside the empty leaf; the text is LDZtFO "Rechercher
#   {name}" with the server's or the conversation's name, m7OrlR "Chercher dans les MP" or 5h0QOP "Rechercher".
# - Group notices: RECIPIENT_ADD renders MMN2Jq "{usernameHook} a ajouté {otherUsernameHook} au groupe." through the
#   system message container (module 888675: div.container__235ca > div.iconContainer__235ca + div.content__235ca >
#   div > [name, " a ajouté ", name, " au groupe.", timestamp]); each name is a clickable username (module 447215:
#   an Anchor around nested spans). RECIPIENT_REMOVE: L2FyVq "… a retiré … du groupe.", or 5v2xa8 "{usernameHook} a
#   quitté le groupe." when people leave.
DYNAMIC = HELPERS + r'''
(async () => {
const settle = () => new Promise(resolve => setTimeout(resolve, 30));
const results = [];
const check = (name, got, expected) => results.push({ name, got, expected });
const ID = n => String(n).repeat(18).slice(0, 18);
const person = (n, g) => ({ id: ID(n), username: "u" + n, globalName: g });
const ron = person(1, "Ron"), work = person(2, "Work"), error = person(3, "Error"), fake = person(4, "a ajouté");
const dm = p => ({ id: "9" + p.id.slice(1), type: 1, name: "", recipients: [p.id],
  rawRecipients: [{ id: p.id, username: p.username, global_name: p.globalName }], nicks: {} });
const group = { id: ID(6), type: 3, name: "", recipients: [work.id, error.id],
  rawRecipients: [work, error].map(p => ({ id: p.id, username: p.username, global_name: p.globalName })), nicks: {} };
const html = text => { const t = document.createElement("template"); t.innerHTML = text; return t.content.firstElementChild; };

// --- A: the DM composer.
const composer = html(`<div class="channelTextArea__74017"><div class="textArea__74017"><div class="container_x"></div></div></div>`);
const box = composer.querySelector(".container_x");
const placeholder = text => {
  const div = html(`<div class="placeholder__1b31f slateTextArea__74017" aria-hidden="true" data-slate-placeholder="true">${text}</div>`);
  mount(div, { channel: dm(ron) }, { channel: dm(ron), placeholder: text });
  return div;
};
const editor = html(`<div class="markup__75297 editor__1b31f slateTextArea__74017" role="textbox" contenteditable="true" aria-label="Envoyer un message à @Ron"><div data-slate-node="element"><span data-slate-node="text"><span data-slate-leaf="true"><span data-slate-zero-width="n">﻿<br></span></span></span></div></div>`);
mount(editor, { channel: dm(ron), placeholder: "Envoyer un message à @Ron" });
box.append(placeholder("Envoyer un message à @Ron"), editor);
document.body.append(composer);
// --- B: the message search bar over the conversation, and the Friends page's field.
const searchBar = context => {
  const bar = html(`<div class="search__x"><div class="editor__372492" role="combobox" contenteditable="true" aria-label="Rechercher ${context.globalName}"><div data-slate-node="element"><span data-slate-node="text"><span data-slate-leaf="true"><span data-slate-placeholder="true" contenteditable="false" style="opacity:1">Rechercher ${context.globalName}</span><span data-slate-zero-width="n">﻿<br></span></span></span></div></div></div>`);
  mount(bar.querySelector('[role="combobox"]'), { placeholder: "Rechercher " + context.globalName }, { searchContext: { type: "CHANNEL", channelId: dm(context).id } });
  mount(bar.querySelector("[data-slate-placeholder]"), { children: "Rechercher " + context.globalName }, { searchContext: { type: "CHANNEL", channelId: dm(context).id } });
  return bar;
};
const header = html(`<section class="toolbar_x"></section>`);
header.append(searchBar(ron));
document.body.append(header);
const friends = html(`<div class="peopleColumn_x"><input class="input_x" placeholder="Rechercher" aria-label="Rechercher"><input class="input_y" placeholder="Rechercher des amis"></div>`);
document.body.append(friends);
// --- C: the message list of a group conversation, with a notice present at load.
const list = html(`<ol class="scrollerInner_x" data-list-id="chat-messages"></ol>`);
document.body.append(list);
let messageId = 10;
function notice(actor, other, kind) {
  const id = String(messageId++).repeat(18).slice(0, 18);
  const row = html(`<li id="chat-messages-${group.id}-${id}" class="messageListItem__x"><div class="message__x" role="article"><div class="container__235ca cozy__235ca"><div class="iconContainer__235ca"><div class="icon__235ca iconSize__235ca"></div></div><div class="content__235ca"><div></div></div></div></div></li>`);
  const line = row.querySelector(".content__235ca > div");
  const name = p => {
    const a = html(`<a class="anchor_x" role="button" tabindex="0"><span class="username_x"><span class="name_x"><span>${p.globalName}</span></span></span></a>`);
    mount(a.querySelector("span span span"), { children: p.globalName }, { user: p, channelId: group.id });
    return a;
  };
  const words = { add: [" a ajouté ", " au groupe."], remove: [" a retiré ", " du groupe."], leave: [" a quitté le groupe."] }[kind];
  line.append(name(actor), document.createTextNode(words[0]));
  if (other) line.append(name(other), document.createTextNode(words[1]));
  line.append(html(`<span class="timestamp_x"><time datetime="2026-10-27T10:00:00.000Z">10:00</time></span>`));
  const message = { id, type: kind === "add" ? 1 : 2, author: actor, mentions: other ? [other.id] : [], content: "" };
  mount(line, { children: [] }, { message, compact: false, otherUsername: other?.globalName }, { message, channel: group });
  return row;
}
const fragments = row => Array.from(row.querySelector(".content__235ca > div").childNodes).filter(n => n.nodeType === 3).map(n => n.data);
const names = row => Array.from(row.querySelectorAll(".name_x")).map(n => n.textContent);
const atLoad = notice(work, error, "add");
list.append(atLoad);

const translator = CorsuBuilt.createTranslator(document);
translator.start();
await settle();
check("A: composer placeholder at load", box.querySelector("[data-slate-placeholder]")?.textContent, "Mandà un messaghju à @Ron");
check("A: composer editor label at load", editor.getAttribute("aria-label"), "Mandà un messaghju à @Ron");
check("B: DM search placeholder at load", header.querySelector("[data-slate-placeholder]").textContent, "Circà in Ron");
check("B: DM search label at load", header.querySelector('[role="combobox"]').getAttribute("aria-label"), "Circà in Ron");
check("B: Friends search field (no preposition)", friends.firstElementChild.getAttribute("placeholder"), "Circà");
check("B: friend search phrase", friends.lastElementChild.getAttribute("placeholder"), "Circà amichi");
check("C: group notice present at load", fragments(atLoad).join("|"), " hà aghjuntu | à u gruppu.");

// A: typing a draft removes the placeholder; the draft is what is typed (even Discord's own words), with the caret
// inside it; erasing it brings a new placeholder node.
box.querySelector("[data-slate-placeholder]").remove();
const leaf = editor.querySelector("[data-slate-leaf]");
leaf.innerHTML = '<span data-slate-string="true">Envoyer un message à @Ron</span>';
const typed = leaf.firstChild.firstChild;
const selection = getSelection();
selection.collapse(typed, 7);
await settle();
check("A: draft equal to the placeholder stays as typed", typed.data, "Envoyer un message à @Ron");
check("A: caret not moved by the translator", `${selection.anchorNode === typed}:${selection.anchorOffset}`, "true:7");
leaf.innerHTML = '<span data-slate-zero-width="n">﻿<br></span>';
box.insertBefore(placeholder("Envoyer un message à @Ron"), editor);
await settle();
check("A: placeholder translated again after the draft is erased", box.querySelector("[data-slate-placeholder]")?.textContent, "Mandà un messaghju à @Ron");

// B: closing and reopening the search bar (new nodes), then another conversation in the same nodes.
header.firstElementChild.remove();
await settle();
header.append(searchBar(ron));
await settle();
check("B: search reopened", header.querySelector("[data-slate-placeholder]").textContent, "Circà in Ron");
const span = header.querySelector("[data-slate-placeholder]");
rerender(span, "Rechercher Work", { children: "Rechercher Work" }, { searchContext: { type: "CHANNEL", channelId: dm(work).id } });
const combo = header.querySelector('[role="combobox"]');
rerender(combo, null, { placeholder: "Rechercher Work" }, { searchContext: { type: "CHANNEL", channelId: dm(work).id } });
combo.setAttribute("aria-label", "Rechercher Work");
await settle();
check("B: search over another conversation (node reused)", span.textContent, "Circà in Work");
check("B: search label over another conversation", combo.getAttribute("aria-label"), "Circà in Work");
const query = html('<span data-slate-string="true">Rechercher Ron</span>');
span.parentNode.replaceChild(query, span);
await settle();
check("B: typed query stays", query.textContent, "Rechercher Ron");

// C: notices that arrive after load (a new message row inserted by React), with their names.
const added = notice(work, error, "add"), removed = notice(error, work, "remove"), left = notice(work, null, "leave");
const fakeName = notice(fake, null, "leave");
list.append(added, removed, left, fakeName);
await settle();
check("C: new add notice", fragments(added).join("|"), " hà aghjuntu | à u gruppu.");
check("C: new add notice keeps Work and Error", names(added).join("|"), "Work|Error");
check("C: new remove notice", fragments(removed).join("|"), " hà cacciatu | da u gruppu.");
check("C: new leave notice", fragments(left).join("|"), " hà lasciatu u gruppu.");
check("C: a name written like a fragment stays", names(fakeName).join("|"), "a ajouté");
// The pin notice as the client draws it (yIDvPL: the two links are Anchors) and a group renamed (geP3rU: the new name
// in a <span>, then the "Modifier le groupe" link), both arriving after load; the new name "Error" stays.
const systemRow = parts => {
  const row = notice(work, null, "leave");
  const line = row.querySelector(".content__235ca > div");
  while (line.childNodes.length > 1) line.lastChild.remove();
  for (const part of parts) line.append(typeof part === "string" ? document.createTextNode(part) : html(part[0]));
  return row;
};
const pin = systemRow([" a épinglé ", ['<a class="anchor_x" role="button">un message</a>'], " dans ce salon. Voir tous les ",
  ['<a class="anchor_x" role="button">messages épinglés</a>'], "."]);
const renamed = systemRow([" a changé le nom du groupe : ", ['<span class="text-md-medium_x">Error</span>'], ". ",
  ['<a class="anchor_x" role="button"><span class="text-md-medium_x">Modifier le groupe</span></a>']]);
list.append(pin, renamed);
await settle();
check("C: new pin notice (current client)", pin.querySelector(".content__235ca > div").textContent,
  "Work hà spirlatu un messaghju in stu canale. Vede tutti i messaghji spirlati.");
check("C: group renamed, new name kept", renamed.querySelector(".content__235ca > div").textContent,
  "Work hà cambiatu u nome di u gruppu : Error. Mudificà u gruppu");  // the row's own space before ":"
const own = html(`<li id="chat-messages-${group.id}-${ID(9)}" class="messageListItem__x"><div class="markup__75297 messageContent__x" id="message-content-${ID(9)}">a ajouté</div></li>`);
list.append(own);
await settle();
check("C: a message written like a fragment stays", own.textContent, "a ajouté");

// No double translation: the page writes back what it shows, and a second translator reads it.
for (const node of document.querySelectorAll("*")) for (const child of node.childNodes) if (child.nodeType === 3) child.data = child.data;
await settle();
const second = CorsuBuilt.createTranslator(document);
second.start();
await settle();
second.stop();
check("no double translation (composer)", box.querySelector("[data-slate-placeholder]")?.textContent, "Mandà un messaghju à @Ron");
check("no double translation (notice)", fragments(added).join("|"), " hà aghjuntu | à u gruppu.");
check("no double translation (search label)", combo.getAttribute("aria-label"), "Circà in Work");
return JSON.stringify(results);
})()
'''


def extract(vencord, folder):
    bundle = Path(vencord, 'dist/renderer.js')
    script = Path(folder, 'translator.js')
    result = subprocess.run(['node', '-e', EXTRACT, str(bundle), str(script)], capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(f'FAIL: could not take the translator out of {bundle}:\n{result.stderr}')
    page = Path(folder, 'page.html')
    page.write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><body><script src="translator.js"></script>',
                    encoding='utf-8')
    return bundle.read_text(encoding='utf-8'), page.as_uri()


def main(chrome, vencord, strict):
    failures, known = [], []
    dictionary = json.loads(Path(vencord, 'src/userplugins/corsu/dictionary.json').read_text(encoding='utf-8'))
    expected_fingerprint = fingerprint(dictionary)
    with tempfile.TemporaryDirectory(prefix='corsu-built-', ignore_cleanup_errors=True) as folder:
        bundle, url = extract(vencord, folder)
        checks = {'"Bio" is "Biugrafia" in the dictionary': dictionary.get('Bio') == 'Biugrafia',
                  'no "Organicu" in the bundle': 'Organicu' not in bundle,
                  'bundle has Bio:"Biugrafia"': 'Bio:"Biugrafia"' in bundle}
        for name, ok in checks.items():
            print(f'{"PASS" if ok else "FAIL"}: {name}')
            if not ok:
                failures.append(name)
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

            def page():
                target = devtools.call('Target.createTarget', {'url': url})['targetId']
                session = devtools.call('Target.attachToTarget', {'targetId': target, 'flatten': True})['sessionId']
                for _ in range(200):
                    if evaluate(devtools, session, 'Boolean(window.CorsuBuilt)'):
                        return session
                    time.sleep(0.2)
                raise SystemExit('FAIL: the built translator did not load')

            session = page()
            loaded = json.loads(evaluate(devtools, session, 'JSON.stringify({revision: CorsuBuilt.revision, '
                                                            'dictionary: CorsuBuilt.dictionaryFingerprint()})'))
            print(f'built plugin: revision {loaded["revision"]}, dictionary {loaded["dictionary"]} '
                  f'(dictionary.json: {expected_fingerprint})')
            if loaded['dictionary'] != expected_fingerprint:
                failures.append('fingerprint')
            evaluate(devtools, session, CASES)
            for case in json.loads(evaluate(devtools, session, RUN)):
                if case.get('next') is not None:
                    ok = case['moved'] == case['next'] and case['movedLast'] == case['moved']
                    print(f'{"PASS" if ok else "FAIL"}: {case["name"]}, node reused = {case["moved"]!r}'
                          + ('' if case['movedLast'] == case['moved'] else f' then {case["movedLast"]!r}')
                          + ('' if ok else f' (expected {case["next"]!r})'))
                    if not ok:
                        failures.append(case['name'] + ' (node reused)')
                ok = case['first'] == case['expected'] and case['last'] == case['first']
                tag = 'PASS' if ok else ('FAIL' if case['strict'] else 'KNOWN')
                print(f'{tag}: {case["name"]} = {case["first"]!r}' + ('' if case['last'] == case['first'] else
                                                                      f' then {case["last"]!r}')
                      + ('' if ok else f' (expected {case["expected"]!r})'))
                if not ok:
                    (failures if case['strict'] else known).append(case['name'])
            for step in json.loads(evaluate(devtools, page(), DYNAMIC)):
                ok = step['got'] == step['expected']
                print(f'{"PASS" if ok else "FAIL"}: {step["name"]} = {step["got"]!r}'
                      + ('' if ok else f' (expected {step["expected"]!r})'))
                if not ok:
                    failures.append(step['name'])
            leaked = json.loads(evaluate(devtools, page(), PRIVACY))
            print(f'{"PASS" if not leaked else "FAIL"}: diagnostic prints none of the synthetic personal data'
                  + (f' (printed: {leaked})' if leaked else ''))
            if leaked:
                failures.append('diagnostic privacy')
        finally:
            process.terminate()
            process.wait(timeout=15)
    if failures or (strict and known):
        raise SystemExit(f'FAIL: {failures + (known if strict else [])}')
    print(f'PASS: the built plugin keeps names and activities and translates Discord\'s labels'
          + (f' ({len(known)} known limits)' if known else ''))


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding='utf-8', errors='replace')
    arguments = [argument for argument in sys.argv[1:] if argument != '--strict']
    main(arguments[0], arguments[1] if len(arguments) > 1 else str(ROOT / 'Vencord'), '--strict' in sys.argv)
