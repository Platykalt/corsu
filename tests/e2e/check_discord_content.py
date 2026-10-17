#!/usr/bin/env python3
"""The Discord plugin's translator against pages built like Discord's own: what people chose stays as written.

Usage: check_discord_content.py CHROME [VENCORD_DIR]
Like check_discord_names.py (same bundle, same headless Chrome), with fixtures that follow the shapes of Discord's
records as Vencord's discord-types describe them and of Discord's markup as Vencord's patches show it: a server
member is identified by `userId` (not `id`); a DM channel keeps its recipients' ids in `recipients` and the people in
`rawRecipients`, with group DM nicknames in `nicks`; the typing indicator writes names in <strong> with only
{channel, isThreadCreation} in its props; React leaves on a node the fiber that created it, whose props can be the
previous render's (the current ones are on its `alternate` and in `__reactProps$`).
This is a simulated page, not an observation of the real Discord app.
"""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
from check_discord_names import run  # noqa: E402

DICTIONARY = {
    'Work': 'Travagliu', 'Error': 'Sbagliu', 'Online': 'In linea', 'General': 'Generale', 'Moderator': 'Moderatore',
    'is typing…': 'scrive…', 'are typing…': 'scrivenu…', 'Several people': 'Parechje persone', 'and': 'è',
    'Members': 'Membri',
}

# React as the checks simulate it, shared by the pages below.
HELPERS = r'''
// React: a host fiber with its component fibers above it; the node keeps the fiber that created it.
function mount(element, ...chain) {
  let parent = null;
  for (const props of chain.reverse()) parent = { memoizedProps: props, return: parent, alternate: null };
  const host = { memoizedProps: { children: element.textContent }, return: parent, alternate: null };
  element.__reactFiber$test = host;
  element.__reactProps$test = host.memoizedProps;
  return host;
}
// A re-render that reuses the node: the other version of each fiber gets the new props, the node still points at
// the old one, React gives the node its new props and text.
window.rerender = (element, text, ...chain) => {
  let old = element.__reactFiber$test, olds = [];
  for (let fiber = old.return; fiber; fiber = fiber.return) olds.push(fiber);
  let parent = null;
  chain.reverse().forEach((props, index) => {
    const previous = olds[chain.length - 1 - index];
    parent = { memoizedProps: props, return: parent, alternate: previous ?? null };
    if (previous) previous.alternate = parent;
  });
  const host = { memoizedProps: { children: text }, return: parent, alternate: old };
  old.alternate = host;
  element.__reactProps$test = host.memoizedProps;
  if (text !== null) element.firstChild.data = text;  // null: an element without text, only attributes
};
// React reconciling a parent's children: a node of the same kind at the same place is reused (a text node gets its
// new text, a <strong> its new text and props), extra ones are added or removed. `parts` lists strings for text
// nodes and [string] for <strong> elements, the way Discord writes names in its typing indicator.
window.setChildren = (element, parts, ...chain) => {
  parts.forEach((part, index) => {
    const strong = Array.isArray(part), text = strong ? part[0] : part;
    const node = element.childNodes[index];
    const same = node && (strong ? node.localName === "strong" : node.nodeType === Node.TEXT_NODE);
    if (!same) {
      const created = strong ? document.createElement("strong") : document.createTextNode(text);
      if (strong) { created.textContent = text; mount(created, { children: text }, ...chain); }
      if (node) element.replaceChild(created, node); else element.append(created);
    } else if (strong) rerender(node, text, { children: text }, ...chain);
    else node.data = text;
  });
  while (element.childNodes.length > parts.length) element.lastChild.remove();
};
'''

PAGE = HELPERS + r'''
const ID1 = "111111111111111111", ID2 = "222222222222222222", ID3 = "333333333333333333", GUILD = "444444444444444444";
const work = { id: ID1, username: "work.home", globalName: "Work" }, error = { id: ID2, username: "err", globalName: null };
const online = { id: "555555555555555555", username: "on", globalName: "Online" };
const raw = user => ({ id: user.id, username: user.username, global_name: user.globalName, display_name: null });
const general = { id: "666666666666666666", guild_id: GUILD, type: 0, name: "General", recipients: [], rawRecipients: [] };
document.body.innerHTML = `
  <h2 id="memberNick" class="title_x">Error</h2>
  <h1 id="dmTitle" class="title_x">Work</h1>
  <h1 id="groupTitle" class="title_x">Work, Error</h1>
  <div class="typing_a"><div class="text_a" role="status"><span id="typing1" class="text_b"><strong>Work</strong> is typing…</span></div></div>
  <div class="chatFooter_z"><span id="typing2"><strong>Work</strong> and <strong>Error</strong> are typing…</span></div>
  <div class="typing_a"><span id="typing3"><strong>Several people</strong> are typing…</span></div>
  <span id="reused" class="title_x">Online</span><button id="reusedLabel">Work</button>
  <div id="commaName" aria-label="Work, Error, Online"></div>
  <div id="barName" title="Work | Error — Online"></div>
  <div id="guildIcon" aria-label="Work"></div>
  <a href="/channels/${GUILD}/666666666666666666"><div id="channelLink" class="name_x">General</div></a>
  <h1 id="channelHeader" class="title_y">General</h1>
  <div id="rolePill" class="role_x" aria-label="Moderator"><span id="roleName" class="roleName_x">Moderator</span></div>
  <h3 id="memberGroup" class="membersGroup_x">Online — 3</h3>
  <div id="message-content-9" class="markup_x messageContent_x">Error</div>
  <div id="bio" class="bio_x markup_x">Work</div>
  <div id="status" class="customStatus_x">Online</div>
  <div id="embed" class="embedDescription_x">Error</div>
  <div id="message-reply-context-5"><span id="replyName" class="username_x">Work</span><div id="replyText" class="repliedTextContent_x markup_x">Online</div></div>`;
mount(document.getElementById("memberNick"), { member: { userId: ID2, guildId: GUILD, nick: "Error", roles: [] } });
const dm = { id: ID3, type: 1, name: "", recipients: [ID1], rawRecipients: [raw(work)], nicks: {} };
mount(document.getElementById("dmTitle"), { channel: dm });
const group = { id: "777777777777777777", type: 3, name: "", recipients: [ID1, ID2], rawRecipients: [raw(work), raw(error)],
  nicks: { [ID2]: "Error" } };
mount(document.getElementById("groupTitle"), { channel: group });
for (const id of ["typing1", "typing2", "typing3"]) {
  const span = document.getElementById(id);
  const component = { channel: general, isThreadCreation: false };
  mount(span, component);
  for (const strong of span.querySelectorAll("strong")) mount(strong, { children: strong.textContent }, component);
}
mount(document.getElementById("reused"), { user: online });
mount(document.getElementById("reusedLabel"), { onClick: () => 0, look: "filled" });
mount(document.getElementById("commaName"), { user: { id: "888888888888888888", username: "we", globalName: "Work, Error" } });
mount(document.getElementById("barName"), { user: { id: "999999999999999999", username: "wb", globalName: "Work | Error" } });
mount(document.getElementById("guildIcon"), { guild: { id: GUILD, name: "Work" } });
mount(document.getElementById("channelHeader"), { channel: general });
mount(document.getElementById("rolePill"), { role: { id: "123456789012345678", name: "Moderator" } });
window.translator = Corsu.createTranslator(document);
window.translator.start();
'''

CHANGE = r'''
// Another conversation in the same nodes: React gives them new text and new props.
rerender(document.getElementById("reused"), "Error", { user: { id: "222222222222222222", username: "err", globalName: "Error" } });
rerender(document.getElementById("reusedLabel"), "Error", { onClick: () => 0, look: "filled" });
document.querySelector("#typing1 strong").firstChild.data = "Online";
document.getElementById("message-content-9").firstChild.data = "Online";
'''

READ = r'''
(() => {
  const text = id => document.getElementById(id).textContent;
  const attribute = (id, name) => document.getElementById(id).getAttribute(name);
  return JSON.stringify({
    memberNick: text("memberNick"), dmTitle: text("dmTitle"), groupTitle: text("groupTitle"),
    typing1: text("typing1"), typing2: text("typing2"), typing3: text("typing3"),
    reused: text("reused"), reusedLabel: text("reusedLabel"),
    commaName: attribute("commaName", "aria-label"), barName: attribute("barName", "title"),
    guildIcon: attribute("guildIcon", "aria-label"), channelLink: text("channelLink"), channelHeader: text("channelHeader"),
    rolePill: attribute("rolePill", "aria-label"), roleName: text("roleName"), memberGroup: text("memberGroup"),
    message: text("message-content-9"), bio: text("bio"), status: text("status"), embed: text("embed"),
    replyName: text("replyName"), replyText: text("replyText"),
  });
})()
'''

EXPECTED = {
    # Defects found in the audit: names whose record Discord shapes differently from what the plugin read.
    'memberNick': 'Error',                       # GuildMember: userId and nick, no id
    'dmTitle': 'Work',                           # DM channel: the person is in rawRecipients
    'groupTitle': 'Work, Error',                 # group DM: rawRecipients and nicks
    'typing1': 'Work scrive…',                   # names in the typing indicator's <strong>
    'typing2': 'Work è Error scrivenu…',
    'typing3': 'Parechje persone scrivenu…',     # the one interface label Discord puts in that <strong>
    'reused': 'Online', 'reusedLabel': 'Travagliu',
    'commaName': 'Work, Error, In linea',        # a name with ", " inside a composed label
    'barName': 'Work | Error — In linea',        # a name with a separator inside a label cut at separators
    # Checked and already fine.
    'guildIcon': 'Work', 'channelLink': 'General', 'channelHeader': 'General',
    'rolePill': 'Moderator', 'roleName': 'Moderator', 'memberGroup': 'In linea — 3',
    'message': 'Error', 'bio': 'Work', 'status': 'Online', 'embed': 'Error',
    'replyName': 'Work', 'replyText': 'Online',
}
AFTER_CHANGE = {
    **EXPECTED,
    'reused': 'Error',                           # the node's own fiber still holds the previous props
    'reusedLabel': 'Sbagliu',                    # an interface label in a reused node is translated again
    'typing1': 'Online scrive…',
    'message': 'Online',
}


# Every element with data-check is read: its text, or the attribute data-check names.
READ_CHECKED = r"""
JSON.stringify(Object.fromEntries(Array.from(document.querySelectorAll("[data-check]"), element =>
  [element.id, element.dataset.check ? element.getAttribute(element.dataset.check) : element.textContent])))
"""

# The typing indicator with 1, 2 and 3 people and "several people", in English and in French. Names come from
# Discord's store, not from the props (only {channel, isThreadCreation}), and are written in <strong>. Here they are
# dictionary words or hold a comma ("Paris, France", "Settings, Home"), and one person is called "and", another "et";
# the words between the names and the end of the sentence are interface text and are translated.
TYPING_DICTIONARY = {
    'is typing…': 'scrive…', 'are typing…': 'scrivenu…', 'Several people': 'Parechje persone', 'and': 'è',
    # Only the "..." spelling, as in the lexicon: Discord writes "…".
    "est en train d'écrire...": 'hè à scrive...', "sont en train d'écrire…": 'sò à scrive…',
    'Plusieurs personnes': 'Parechje persone', 'et': 'è',
    'Settings': 'Parametri', 'Home': 'Accolta', 'Paris': 'Parigi', 'France': 'Francia', 'Online': 'In linea',
    'Work': 'Travagliu', 'Members': 'Membri',
}

TYPING_PAGE = HELPERS + r"""
const channel = { id: "666666666666666666", guild_id: "444444444444444444", type: 0, name: "Home", recipients: [] };
const indicator = { channel, isThreadCreation: false };
const typing = {
  en1: [["Paris, France"], " is typing…"],
  en2: [["Settings, Home"], " and ", ["Work"], " are typing…"],
  en3: [["Online"], ", ", ["and"], ", and ", ["Paris, France"], " are typing…"],
  enMany: [["Several people"], " are typing…"],
  fr1: [["Settings, Home"], " est en train d'écrire…"],
  fr2: [["Paris, France"], " et ", ["et"], " sont en train d'écrire…"],
  fr3: [["Work"], ", ", ["Online"], " et ", ["Home"], " sont en train d'écrire…"],
  frMany: [["Plusieurs personnes"], " sont en train d'écrire…"],
};
// Half of them inside an element whose class names the indicator, the others only known by the component's props.
document.body.innerHTML = Object.keys(typing).map((id, index) => index % 2
  ? `<div class="typing_a"><span id="${id}" data-check=""></span></div>`
  : `<div class="chatFooter_z"><span id="${id}" data-check=""></span></div>`).join("") + `
  <div class="typing_a"><button id="membersButton" data-check="">Members</button></div>
  <div class="chatFooter_z"><span id="onlineLabel" data-check="">Online</span></div>`;
for (const [id, parts] of Object.entries(typing)) {
  const span = document.getElementById(id);
  mount(span, indicator);
  setChildren(span, parts, indicator);
}
window.indicator = indicator;
window.translator = Corsu.createTranslator(document);
window.translator.start();
"""

# People start and stop typing: React keeps the nodes and changes their text.
TYPING_CHANGE = r"""
setChildren(document.getElementById("en1"), [["Paris, France"], " and ", ["Home"], " are typing…"], indicator);
setChildren(document.getElementById("en2"), [["Several people"], " are typing…"], indicator);
setChildren(document.getElementById("enMany"), [["Work"], " is typing…"], indicator);
setChildren(document.getElementById("fr3"), [["Work"], " et ", ["Online"], " sont en train d'écrire…"], indicator);
setChildren(document.getElementById("frMany"), [["Settings, Home"], ", ", ["Paris, France"], " et ", ["Online"],
  " sont en train d'écrire…"], indicator);
setChildren(document.getElementById("fr1"), [["Plusieurs personnes"], " sont en train d'écrire…"], indicator);
"""

TYPING_EXPECTED = {
    'en1': 'Paris, France scrive…',
    'en2': 'Settings, Home è Work scrivenu…',
    'en3': 'Online, and, è Paris, France scrivenu…',
    'enMany': 'Parechje persone scrivenu…',
    'fr1': 'Settings, Home hè à scrive…',
    'fr2': 'Paris, France è et sò à scrive…',
    'fr3': 'Work, Online è Home sò à scrive…',
    'frMany': 'Parechje persone sò à scrive…',
    # Interface labels next to the indicator.
    'membersButton': 'Membri', 'onlineLabel': 'In linea',
}
TYPING_AFTER_CHANGE = {
    **TYPING_EXPECTED,
    'en1': 'Paris, France è Home scrivenu…',            # 1 person, then 2: the reused text node becomes " and "
    'en2': 'Parechje persone scrivenu…',                # 2 people, then several: the reused <strong> is a label
    'enMany': 'Work scrive…',                           # several, then 1: the reused <strong> is a name again
    'fr3': 'Work è Online sò à scrive…',                # 3 people, then 2
    'frMany': 'Settings, Home, Paris, France è Online sò à scrive…',  # several, then 3
    'fr1': 'Parechje persone sò à scrive…',
}

# Moving between conversations, servers and channels: React keeps the header's nodes and gives them new text and
# props, while the node keeps the fiber that created it. The new name is kept, a label shown in a node that showed a
# name is translated, and the previous name does not stop the labels shown with the new conversation.
NAVIGATION_DICTIONARY = {
    'Online': 'In linea', 'Offline': 'Fora di linea', 'Members': 'Membri', 'Error': 'Sbagliu', 'Work': 'Travagliu',
    'Settings': 'Parametri', 'Home': 'Accolta', 'Paris': 'Parigi', 'France': 'Francia', 'Call': 'Chjamà',
    'Envoyer un message dans #\u00001\u0000': 'Mandà un messaghju in #\u00001\u0000',
    'Start a Voice Call with \u00001\u0000': 'Principià una chjama vucale cù \u00001\u0000',
}

NAVIGATION_PAGE = HELPERS + r"""
const user = (id, globalName) => ({ id, username: "u" + id.slice(0, 3), globalName });
const offline = user("111111111111111111", "Offline"), work = user("222222222222222222", "Work");
const paris = user("333333333333333333", "Paris, France"), settings = user("444444444444444444", "Settings, Home");
const raw = person => ({ id: person.id, username: person.username, global_name: person.globalName });
const dm = person => ({ id: "5" + person.id.slice(1), type: 1, name: "", recipients: [person.id], rawRecipients: [raw(person)], nicks: {} });
window.people = { offline, work, paris, settings, dm, raw };
const guild = { id: "666666666666666666", name: "Settings, Home" }, role = { id: "777777777777777777", name: "Settings" };
const homeChannel = { id: "888888888888888888", guild_id: guild.id, type: 0, name: "Home", recipients: [] };
const group = { id: "999999999999999999", type: 3, name: "", recipients: [paris.id, settings.id],
  rawRecipients: [raw(paris), raw(settings)], nicks: {} };
Object.assign(window.people, { guild, role, homeChannel, group });
document.body.innerHTML = `
  <section><h1 id="dmName" class="title_x" data-check="">Offline</h1><span id="dmStatus" data-check="">Online</span>
    <button id="dmCall" data-check="aria-label" aria-label="Start a Voice Call with Offline">Call</button></section>
  <section><h1 id="groupName" class="title_x" data-check="">Paris, France, Settings, Home</h1>
    <div id="groupItem" data-check="aria-label" aria-label="Paris, France, Settings, Home, Online"></div></section>
  <section><h2 id="guildHeader" class="header_g" data-check="">Settings, Home</h2>
    <button id="guildMembers" data-check="">Members</button>
    <h3 id="groupOnline" class="membersGroup_x" data-check="">Online — 3</h3>
    <h3 id="groupRole" class="membersGroup_x" data-check="">Settings — 2</h3></section>
  <section><h1 id="channelHeader" class="title_y" data-check="">Home</h1>
    <div id="channelTab" class="tab_x" data-check="">Work</div>
    <div id="composer" class="placeholder_x" data-check="">Envoyer un message dans #Home</div></section>
  <div id="sepName" data-check="title" title="Work — Online"></div>
  <div id="countName" data-check="aria-label" aria-label="Members 5, Online"></div>`;
const id = name => document.getElementById(name);
for (const name of ["dmName", "dmStatus", "dmCall"]) mount(id(name), { channel: dm(offline) });
for (const name of ["groupName", "groupItem"]) mount(id(name), { channel: group });
for (const name of ["guildHeader", "guildMembers", "groupOnline"]) mount(id(name), { guild });
mount(id("groupRole"), { role }, { guild });
for (const name of ["channelHeader", "channelTab", "composer"]) mount(id(name), { channel: homeChannel }, { guild });
mount(id("sepName"), { user: work });
mount(id("countName"), { user: user("141414141414141414", "Members 5") });
window.translator = Corsu.createTranslator(document);
window.translator.start();
"""

NAVIGATION_CHANGE = r"""
{
const id = name => document.getElementById(name);
const { offline, work, paris, settings, dm, guild, role, homeChannel } = people;
// Another DM: from "Offline", who is online, to "Work", who is offline.
rerender(id("dmName"), "Work", { channel: dm(work) });
rerender(id("dmStatus"), "Offline", { channel: dm(work) });
rerender(id("dmCall"), null, { channel: dm(work) });
id("dmCall").setAttribute("aria-label", "Start a Voice Call with Work");
// From the group DM to a DM with "Paris, France": the title node now shows one name, the list item a label.
rerender(id("groupName"), "Paris, France", { channel: dm(paris) });
rerender(id("groupItem"), null, { channel: dm(paris) });
id("groupItem").setAttribute("aria-label", "Paris, France, Offline");
// Another server, "Work": its header, and the role group's node now shows the "Offline" group.
const other = { id: "121212121212121212", name: "Work" };
rerender(id("guildHeader"), "Work", { guild: other });
rerender(id("groupOnline"), "Online — 5", { guild: other });
rerender(id("groupRole"), "Offline — 4", { guild: other });
// Another channel, "Work": the tab that showed "Work" now shows "Home", the channel the user left.
const workChannel = { ...homeChannel, id: "131313131313131313", name: "Work" };
rerender(id("channelHeader"), "Work", { channel: workChannel }, { guild: other });
rerender(id("channelTab"), "Home", { channel: workChannel }, { guild: other });
rerender(id("composer"), "Envoyer un message dans #Work", { channel: workChannel }, { guild: other });
}
"""

NAVIGATION_EXPECTED = {
    'dmName': 'Offline', 'dmStatus': 'In linea', 'dmCall': 'Principià una chjama vucale cù Offline',
    'groupName': 'Paris, France, Settings, Home', 'groupItem': 'Paris, France, Settings, Home, In linea',
    'guildHeader': 'Settings, Home', 'guildMembers': 'Membri', 'groupOnline': 'In linea — 3',
    'groupRole': 'Settings — 2',                       # a role group: the role's name and its count
    'channelHeader': 'Home',
    'channelTab': 'Travagliu',
    'composer': 'Mandà un messaghju in #Home',
    'sepName': 'Work — In linea',                      # a name between separators, the label next to it translated
    'countName': 'Members 5, In linea',                # a name that reads like a label and a count
}
NAVIGATION_AFTER_CHANGE = {
    'dmName': 'Work',                                  # the new name, though it is a dictionary word
    'dmStatus': 'Fora di linea',                       # the previous person's name ("Offline") does not stop the label
    'dmCall': 'Principià una chjama vucale cù Work',
    'groupName': 'Paris, France',
    'groupItem': 'Paris, France, Fora di linea',
    'guildHeader': 'Work', 'guildMembers': 'Membri', 'groupOnline': 'In linea — 5',
    'groupRole': 'Fora di linea — 4',                  # the node showed the role "Settings"; now a label
    'channelHeader': 'Work',
    'channelTab': 'Accolta',                           # "Home" was the previous channel's name; now a label
    'composer': 'Mandà un messaghju in #Work',
    'sepName': 'Work — In linea', 'countName': 'Members 5, In linea',
}

# (name, dictionary, page, read, expected, change, expected after the change)
SCENARIOS = [
    ('records', DICTIONARY, PAGE, READ, EXPECTED, CHANGE, AFTER_CHANGE),
    ('typing', TYPING_DICTIONARY, TYPING_PAGE, READ_CHECKED, TYPING_EXPECTED, TYPING_CHANGE, TYPING_AFTER_CHANGE),
    ('navigation', NAVIGATION_DICTIONARY, NAVIGATION_PAGE, READ_CHECKED, NAVIGATION_EXPECTED, NAVIGATION_CHANGE,
     NAVIGATION_AFTER_CHANGE),
]


def run_all(chrome, vencord):
    """Every scenario, each in its own simulated page in a throwaway Chrome profile; the values that differ."""
    wrong = {}
    for name, *scenario in SCENARIOS:
        print(f'-- {name} (simulated page in Chrome)')
        wrong.update({f'{name} {key}': value for key, value in run(chrome, vencord, *scenario).items()})
    return wrong


def main(chrome, vencord):
    wrong = run_all(chrome, vencord)
    if wrong:
        raise SystemExit(f'FAIL: {wrong}')
    print('PASS: nicknames, DM recipients, people typing, names with commas and reused nodes keep their names; '
          'labels around them are translated')


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding='utf-8', errors='replace')
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else str(ROOT / 'Vencord'))
