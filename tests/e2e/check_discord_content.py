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

PAGE = r'''
const ID1 = "111111111111111111", ID2 = "222222222222222222", ID3 = "333333333333333333", GUILD = "444444444444444444";
const work = { id: ID1, username: "work.home", globalName: "Work" }, error = { id: ID2, username: "err", globalName: null };
const online = { id: "555555555555555555", username: "on", globalName: "Online" };
const raw = user => ({ id: user.id, username: user.username, global_name: user.globalName, display_name: null });
const general = { id: "666666666666666666", guild_id: GUILD, type: 0, name: "General", recipients: [], rawRecipients: [] };
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
  element.firstChild.data = text;
};
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


def main(chrome, vencord):
    wrong = run(chrome, vencord, DICTIONARY, PAGE, READ, EXPECTED, CHANGE, AFTER_CHANGE)
    if wrong:
        raise SystemExit(f'FAIL: {wrong}')
    print('PASS: nicknames, DM recipients, people typing and reused nodes keep their names; labels are translated')


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding='utf-8', errors='replace')
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else str(ROOT / 'Vencord'))
