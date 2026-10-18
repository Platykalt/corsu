#!/usr/bin/env python3
"""The Discord plugin's translator on activity status lines: Discord's own labels are translated, what people and
applications show as their activity stays as written.

Usage: check_discord_activity.py CHROME [VENCORD_DIR]
Like check_discord_names.py (same bundle, same headless Chrome). The pages follow the markup and props of Discord's
web client as its public bundle shows them (read in October 2026, without an account):
- the activity status (ActivityStatus) gets the person's `activities`, `voiceChannel` and `applicationStream`; for a
  call it writes Discord's own label ("Dans un appel" for a direct message or group call) in a text <div> with the
  caller's textClassName, inside a container whose aria-label is "{label} ({channel or conversation name})"; for a
  game it writes the game's name, with "Joue à {game}" as aria-label;
- in the list of direct messages that textClassName is "activityStatusText__972a0" (matched by the name rule
  [class*="activity"]) and the whole item sits in <a href="/channels/@me/{id}"> (matched by the name rule
  a[href^="/channels/"]); on the Friends tab it is "statusText__19b6d" under "subtext__0a06e"; in the account panel
  "activityStatusText__37e49";
- in a profile, the call card writes the same label in "headerText__39ec2", with a hidden heading
  "{label}, {conversation name}".
It checks: "Dans un appel" is translated in the direct message list, on the Friends tab and in the profile; names
("Work", "Error") stay inside the translated labels; a game, rich presence details and state, and a custom status equal
to dictionary words ("Work", "Error", "Dans un appel") stay as written; after the activity changes and after nodes are
reused for another person, each text is still right; repeated passes never translate twice; and the hidden diagnostic
classifies what it sees without giving names or messages.
This is a simulated page, not an observation of the real Discord app.
"""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
from check_discord_names import run  # noqa: E402
from check_discord_content import HELPERS  # noqa: E402

DICTIONARY = {
    'Dans un appel': 'In una chjama', 'Dans un appel (\u00001\u0000)': 'In una chjama (\u00001\u0000)',
    'Joue à \u00001\u0000': 'Ghjoca à \u00001\u0000',
    'Work': 'Travagliu', 'Error': 'Sbagliu', 'En ligne': 'In linea', 'Online': 'In linea',
    # A translation that is itself a key: a second pass over a translated label would show it.
    'In una chjama': 'DOUBLE',
}

PAGE = HELPERS + r'''
const ID1 = "111111111111111111", ID2 = "222222222222222222";
const work = { id: ID1, username: "work.home", globalName: "Work" }, error = { id: ID2, username: "err", globalName: "Error" };
const raw = person => ({ id: person.id, username: person.username, global_name: person.globalName });
const dm = person => ({ id: "3" + person.id.slice(1), type: 1, name: "", recipients: [person.id], rawRecipients: [raw(person)], nicks: {} });
const call = () => [];                                   // in a call: no activity record, a voiceChannel
const game = name => [{ type: 0, name, application_id: "999999999999999999" }];
const custom = state => [{ type: 4, name: "Custom Status", state, emoji: null }];
window.people = { work, error, dm, call, game, custom };
document.body.innerHTML = `
  <nav class="privateChannels_x">
    <div class="channel__972a0 dm__972a0"><div class="interactive__972a0">
      <a id="dmLink" class="link__972a0 channelNameFade__972a0" href="/channels/@me/311111111111111111" aria-label="Work (message direct)">
        <div class="layout__20a53 avatarWithText__972a0"><div class="avatar__20a53"></div><div class="content__20a53">
          <div class="nameAndDecorators__20a53"><div class="name__20a53 text-md/medium__20a53"><div id="dmName" class="overflowTooltip__972a0" data-check="">Work</div></div></div>
          <div class="subText__20a53"><div class="container_c9d15c textXs_c9d15c">
            <div id="dmCallBox" class="container_c9d15c textWithIconContainer_c9d15c textXs_c9d15c" aria-label="Dans un appel (Work)" data-check="aria-label">
              <svg class="icon_c9d15c"></svg>
              <div id="dmActivity" class="text-xs/medium_a truncated_c9d15c activityStatusText__972a0" data-text-variant="text-xs/medium" data-check="">Dans un appel</div>
            </div></div></div>
        </div></div>
      </a></div></div>
    <div class="channel__972a0 dm__972a0"><div class="interactive__972a0">
      <a class="link__972a0 channelNameFade__972a0" href="/channels/@me/322222222222222222">
        <div class="layout__20a53"><div class="content__20a53">
          <div class="nameAndDecorators__20a53"><div class="name__20a53"><div id="nickName" class="overflowTooltip__972a0" data-check="">Online</div></div></div>
          <div class="subText__20a53"><div class="container_c9d15c textXs_c9d15c">
            <div id="dmStatus" class="text-xs/medium_a truncated_c9d15c activityStatusText__972a0" data-check="">Dans un appel</div>
          </div></div>
        </div></div>
      </a></div></div>
  </nav>
  <div class="peopleColumn__133bf"><div class="peopleList__5ec2f">
    <div class="peopleListItem_cc6179"><div class="rowContent_cc6179"><div class="listItemContents_fc004c">
      <div class="userInfo__0a06e"><div class="text__0a06e">
        <div class="discordTag__0a06e"><span id="friendName" class="username__0a06e" data-check="">Error</span></div>
        <div class="subtext__0a06e"><div class="container_c9d15c textSm_c9d15c">
          <div id="friendBox" class="container_c9d15c textWithIconContainer_c9d15c textSm_c9d15c" aria-label="Dans un appel (Work)" data-check="aria-label">
            <div id="friendActivity" class="text-sm/medium_a truncated_c9d15c statusText__19b6d" data-check="">Dans un appel</div>
          </div></div></div>
      </div></div></div></div></div>
    <div class="peopleListItem_cc6179"><div class="rowContent_cc6179"><div class="listItemContents_fc004c">
      <div class="userInfo__0a06e"><div class="text__0a06e">
        <div class="discordTag__0a06e"><span class="username__0a06e">Work</span></div>
        <div class="subtext__0a06e"><div class="container_c9d15c textSm_c9d15c">
          <div id="gameBox" class="container_c9d15c textWithIconContainer_c9d15c textSm_c9d15c" aria-label="Joue à Work" data-check="aria-label">
            <div id="friendGame" class="text-sm/medium_a truncated_c9d15c statusText__19b6d" data-check="">Work</div>
          </div></div></div>
      </div></div></div></div></div>
    <div class="peopleListItem_cc6179"><div class="rowContent_cc6179"><div class="listItemContents_fc004c">
      <div class="userInfo__0a06e"><div class="text__0a06e">
        <div class="subtext__0a06e"><div class="container_c9d15c textSm_c9d15c">
          <div id="friendCustom" class="text-sm/medium_a truncated_c9d15c statusText__19b6d" data-check="">Dans un appel</div>
        </div></div>
      </div></div></div></div></div>
  </div></div>
  <section class="panels_x"><div class="container__37e49"><div class="panelSubtextContainer__37e49">
    <div class="container_c9d15c textXs_c9d15c"><div id="panelCustom" class="text-xs/medium_a truncated_c9d15c activityStatusText__37e49" data-check="">Error</div></div>
  </div></div></section>
  <div class="userProfile_x">
    <div id="voiceCard" class="card__39ec2"><div class="header__39ec2"><div class="text-xs/medium_a headerText__39ec2">
      <div id="profileCall" data-check="">Dans un appel</div></div></div>
      <h2 id="profileHeading" class="hiddenVisually_x" data-check="">Dans un appel, Work</h2></div>
    <div id="gameCard" class="card__39ec2"><div class="header__39ec2"><div class="text-xs/medium_a headerText__39ec2"><div id="gameHeader" data-check="">Online</div></div></div>
      <div class="details__39ec2"><div id="rpName" data-check="">Error</div><div id="rpDetails" data-check="">Work</div>
        <div id="rpState" data-check="">Dans un appel</div></div></div>
  </div>
  <div class="messagesWrapper_x"><div id="message-content-1" class="markup_x messageContent_x" data-check="">Dans un appel</div></div>`;
const id = name => document.getElementById(name);
// The direct message list: PrivateChannel (channel, user, activities, voiceChannel) > AvatarWithText > the name, or
// ActivityStatus (user, activities, voiceChannel) > the call label (channel) > its text (text, aria-label) > Text.
const privateChannel = person => ({ channel: dm(person), user: person, activities: call(), voiceChannel: dm(person), applicationStream: null, status: "online" });
const status = (person, activities, voiceChannel) => ({ user: person, activities, voiceChannel, applicationStream: null, textClassName: "activityStatusText__972a0" });
const callLabel = channel => [{ text: "Dans un appel", textVariant: "text-xs/medium", "aria-label": "Dans un appel (Work)" }, { channel, textVariant: "text-xs/medium" }];
mount(id("dmName"), { children: "Work" }, { name: null, subText: null }, privateChannel(work));
mount(id("dmCallBox"), ...callLabel(dm(work)), status(work, call(), dm(work)), privateChannel(work));
mount(id("dmActivity"), { variant: "text-xs/medium", className: "activityStatusText__972a0" }, ...callLabel(dm(work)), status(work, call(), dm(work)), privateChannel(work));
// A friend nickname: Discord reads it from its store, it is not in the props. It is the conversation's name, not on the
// activity line, so it stays as it is.
const nicknamed = { id: "444444444444444444", username: "someone", globalName: null };
mount(id("nickName"), { children: "Online" }, { name: null }, privateChannel(nicknamed));
mount(id("dmStatus"), { variant: "text-xs/medium" }, ...callLabel(dm(nicknamed)), status(nicknamed, call(), dm(nicknamed)), privateChannel(nicknamed));
// The Friends tab: the row (user, activities) > UserInfo (user, subText) > the subtext (activities, user) > ActivityStatus.
const row = (person, activities) => [{ user: person, activities, applicationStream: null, status: "online" }];
mount(id("friendName"), { user: error, nick: null }, ...row(error, call()));
mount(id("friendBox"), ...callLabel(dm(work)), status(error, call(), dm(work)), ...row(error, call()));
mount(id("friendActivity"), { variant: "text-sm/medium" }, ...callLabel(dm(work)), status(error, call(), dm(work)), ...row(error, call()));
const playing = game("Work");
mount(id("gameBox"), { text: "Work", "aria-label": "Joue à Work" }, { activity: playing[0] }, status(work, playing), ...row(work, playing));
mount(id("friendGame"), { variant: "text-sm/medium" }, { text: "Work", "aria-label": "Joue à Work" }, { activity: playing[0] }, status(work, playing), ...row(work, playing));
// A custom status typed as "Dans un appel", shown without its tooltip (no customStatus class around it).
const typed = custom("Dans un appel");
mount(id("friendCustom"), { variant: "text-sm/medium" }, { customStatusActivity: typed[0] }, status(error, typed), ...row(error, typed));
const own = custom("Error");
mount(id("panelCustom"), { variant: "text-xs/medium" }, { customStatusActivity: own[0] }, status(work, own), { currentUser: work, activities: own });
// The profile's call card (user, voiceChannel) and a rich presence card (activity).
mount(id("profileCall"), { children: "Dans un appel" }, { text: "Dans un appel" }, { user: work, currentUser: error, voiceChannel: dm(work) });
mount(id("profileHeading"), { children: "Dans un appel, Work" }, { user: work, currentUser: error, voiceChannel: dm(work) });
const presence = { type: 0, name: "Error", details: "Work", state: "Dans un appel", assets: { large_text: "Work" } };
for (const name of ["rpName", "rpDetails", "rpState"]) mount(id(name), { children: id(name).textContent }, { activity: presence, user: work });
mount(id("gameHeader"), { children: "Online" }, { activity: presence, user: work });
window.translator = Corsu.createTranslator(document);
window.translator.start();
'''

READ = r"""
JSON.stringify(Object.fromEntries(Array.from(document.querySelectorAll("[data-check]"), element =>
  [element.id, element.dataset.check ? element.getAttribute(element.dataset.check) : element.textContent])))
"""

EXPECTED = {
    'dmName': 'Work',                                  # the person's name, a dictionary word
    'dmCallBox': 'In una chjama (Work)',               # the label translated, the name inside it kept
    'dmActivity': 'In una chjama',                     # defect 1: the label under a name rule in the DM list
    'nickName': 'Online',                              # a name not in the records, outside the activity line
    'dmStatus': 'In una chjama',
    'friendName': 'Error',
    'friendBox': 'In una chjama (Work)', 'friendActivity': 'In una chjama',
    'gameBox': 'Ghjoca à Work',                        # Discord's label around the game's name
    'friendGame': 'Work',                              # a game called "Work"
    'friendCustom': 'Dans un appel',                   # a custom status typed as "Dans un appel"
    'panelCustom': 'Error',                            # one's own custom status in the account panel
    'profileCall': 'In una chjama',                    # the profile's call card
    'profileHeading': 'In una chjama, Work',
    'gameHeader': 'In linea',                          # an interface label in the same card
    'rpName': 'Error', 'rpDetails': 'Work', 'rpState': 'Dans un appel',  # rich presence written by the game
    'message-content-1': 'Dans un appel',              # a message
}

# The activity changes, nodes are reused for someone else, and the page writes the same texts again several times.
CHANGE = r"""
(async () => {
const id = name => document.getElementById(name);
const { work, error, dm, call, game, custom } = people;
const status = (person, activities, voiceChannel) => ({ user: person, activities, voiceChannel, applicationStream: null });
const row = (person, activities) => ({ user: person, activities, applicationStream: null, status: "online" });
const settle = () => new Promise(resolve => setTimeout(resolve, 20));
// The DM list: the person leaves the call and plays a game called "Error".
const playing = game("Error");
rerender(id("dmActivity"), "Error", { variant: "text-xs/medium" }, { text: "Error" }, { activity: playing[0] }, status(work, playing),
  { channel: dm(work), user: work, activities: playing, voiceChannel: null });
// The Friends tab: the player of "Work" joins a call; the custom status row is reused for someone in a call.
rerender(id("friendGame"), "Dans un appel", { variant: "text-sm/medium" }, { text: "Dans un appel" }, { channel: dm(error) },
  status(work, call(), dm(error)), row(work, call()));
id("gameBox").setAttribute("aria-label", "Dans un appel (Error)");
rerender(id("friendCustom"), "Dans un appel", { variant: "text-sm/medium" }, { text: "Dans un appel" }, { channel: dm(work) },
  status(error, call(), dm(work)), row(error, call()));
// The custom status shows on the node that showed the call label.
const typed = custom("Dans un appel");
rerender(id("friendActivity"), "Dans un appel", { variant: "text-sm/medium" }, { customStatusActivity: typed[0] }, status(error, typed), row(error, typed));
// Another profile in the same nodes: its rich presence details read "Online", its state "Dans un appel".
const presence = { type: 0, name: "Work", details: "Online", state: "Dans un appel" };
rerender(id("rpName"), "Work", { activity: presence, user: error });
rerender(id("rpDetails"), "Online", { activity: presence, user: error });
rerender(id("profileCall"), "Dans un appel", { text: "Dans un appel" }, { user: error, currentUser: work, voiceChannel: dm(error) });
rerender(id("profileHeading"), "Dans un appel, Error", { user: error, currentUser: work, voiceChannel: dm(error) });
await settle();
// Several more passes: the page writes back what it shows, and the attributes too.
for (let pass = 0; pass < 3; pass++) {
  for (const element of document.querySelectorAll("[data-check]")) {
    if (element.dataset.check) element.setAttribute(element.dataset.check, element.getAttribute(element.dataset.check));
    else for (const child of element.childNodes) if (child.nodeType === Node.TEXT_NODE) child.data = child.data;
  }
  await settle();
}
})()
"""

AFTER_CHANGE = {
    **EXPECTED,
    'dmActivity': 'Error',                             # a game called "Error", in the node that showed the label
    'friendGame': 'In una chjama',                     # the node that showed a game shows the label
    'gameBox': 'In una chjama (Error)',
    'friendCustom': 'In una chjama',                   # the node that showed a custom status shows the label
    'friendActivity': 'Dans un appel',                 # the node that showed the label shows a custom status
    'rpName': 'Work', 'rpDetails': 'Online',
    'profileCall': 'In una chjama', 'profileHeading': 'In una chjama, Error',
}

# The diagnostic: one text of each kind, with names, a message and a game that must not appear in the report.
DIAGNOSTIC_DICTIONARY = {
    'Online': 'In linea', 'Dans un appel': 'In una chjama', 'Paramètres': 'Parametri',
    'Joue à \u00001\u0000': 'Ghjoca à \u00001\u0000', 'Work': 'Travagliu',
    # Words the diagnostic may give (it gives a word only when some entry uses it).
    'Paramètres avancés': 'Parametri avanzati', 'Paramètres du serveur': 'Parametri di u servore',
    'Appel avec': 'Chjama cù', 'en cours': 'in corsu',
}

DIAGNOSTIC_PAGE = HELPERS + r'''
const bob = { id: "111111111111111111", username: "bob.private", globalName: "Bobette Secretname" };
document.body.innerHTML = `
  <span id="excluded" class="username_x">Online</span>
  <span id="unknownName" class="username_x">Zoélie Privatename</span>
  <div id="missing">Paramètres avancés du serveur</div>
  <div id="withName">Appel avec Bobette Secretname en cours</div>
  <div id="template">Joue à Privategame</div>
  <div id="message-content-7" class="markup_x">Mon message très privé à toi</div>
  <div class="subtext_x"><div id="value">Work</div></div>
  <div id="later"></div>`;
mount(document.getElementById("withName"), { user: bob });
mount(document.getElementById("value"), { activity: { type: 0, name: "Work" } }, { user: bob, activities: [{ type: 0, name: "Work" }] });
window.translator = Corsu.createTranslator(document);
window.translator.start();
'''

# Read in the same turn as the changes, before the observer's microtask: new labels not yet seen (unapplied); after
# the change, a text changed after its translation (stale).
DIAGNOSTIC_READ = r"""
(() => {
if (window.changed) {
  const node = document.getElementById("excluded");
  const before = node.textContent;
  node.firstChild.data = "Dans un appel";
  const report = window.translator.report();
  return JSON.stringify({ translatedFirst: before, stale: report.findings.some(f => f.kind === "stale" && f.text === "Dans un appel") });
}
const plain = document.createElement("div");
plain.textContent = "Dans un appel";
document.getElementById("later").append(plain);
const missed = document.createElement("div");
missed.textContent = "Paramètres";
document.body.append(missed);
const report = window.translator.report();
const output = JSON.stringify(report);
const has = (kind, text, rule) => report.findings.some(f => f.kind === kind && (text === undefined || f.text === text) && (rule === undefined || f.rule === rule));
return JSON.stringify({
  revision: typeof report.revision === "string" && report.revision.length > 0,
  dictionary: report.dictionary,
  // A text kept by a name rule is never given (a nickname can be a dictionary word): only the rule.
  excluded: has("excluded", undefined, '[class*="username"]') && !report.findings.some(f => f.kind === "excluded" && f.text),
  missing: has("missing", "Paramètres avancés du serveur"),
  redacted: has("missing", "Appel avec {name} en cours"),
  template: has("template", "Joue à {1}"),
  unapplied: has("unapplied", "Dans un appel") || has("unapplied", "Paramètres"),
  userValue: (report.counts.userValue ?? 0) >= 1,
  userContent: (report.counts.userContent ?? 0) >= 1,
  unknownInName: (report.counts.unknownInName ?? 0) >= 1,
  private: ["Zoélie", "Privatename", "Bobette", "Secretname", "bob.private", "Privategame", "privé", "Mon message"]
    .filter(word => output.includes(word)),
});
})()
"""

DIAGNOSTIC_CHANGE = r"""
(() => {
// A label translated, then changed by the page; read before the observer runs.
const node = document.getElementById("excluded");
node.className = "plain_x";
window.translator.stop(); window.translator.start();
node.firstChild.data = "Online";
window.changed = true;
})()
"""

def fingerprint(words):
    """The dictionary fingerprint the plugin reports (translate.ts dictionaryFingerprint), computed here from the same
    entries: the number of entries and two order-independent sums of FNV-1a hashes over UTF-16 code units."""
    total, mixed = 0, 0
    for key, value in words.items():
        entry = (key + '\u0000' + value).encode('utf-16-le')
        hashed = 0x811c9dc5
        for index in range(0, len(entry), 2):
            hashed = ((hashed ^ int.from_bytes(entry[index:index + 2], 'little')) * 0x01000193) & 0xFFFFFFFF
        total = (total + hashed) & 0xFFFFFFFF
        mixed ^= (hashed * 0x9e3779b1) & 0xFFFFFFFF
    return f'{len(words)}-{total:08x}{mixed:08x}'


DIAGNOSTIC_EXPECTED = {
    'revision': True, 'dictionary': fingerprint(DIAGNOSTIC_DICTIONARY),
    'excluded': True, 'missing': True, 'redacted': True, 'template': True, 'unapplied': True,
    'userValue': True, 'userContent': True, 'unknownInName': True, 'private': [],
}


def main(chrome, vencord):
    print('-- activity (simulated page in Chrome)')
    wrong = run(chrome, vencord, DICTIONARY, PAGE, READ, EXPECTED, CHANGE, AFTER_CHANGE)
    print('-- diagnostic (simulated page in Chrome)')
    wrong.update({f'diagnostic {key}': value for key, value in
                  run(chrome, vencord, DIAGNOSTIC_DICTIONARY, DIAGNOSTIC_PAGE, DIAGNOSTIC_READ, DIAGNOSTIC_EXPECTED,
                      DIAGNOSTIC_CHANGE, {'translatedFirst': 'In linea', 'stale': True}).items()})
    if wrong:
        raise SystemExit(f'FAIL: {wrong}')
    print('PASS: Discord\'s activity labels are translated; names, games, rich presence and custom statuses stay as '
          'written; the diagnostic gives no personal data')


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding='utf-8', errors='replace')
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else str(ROOT / 'Vencord'))
