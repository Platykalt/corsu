"use strict";
const docs = "https://github.com/Platykalt/corsu/blob/main/docs/";
const systems = { windows: "Windows", macos: "macOS", linux: "Linux" };

let language = null;
try { language = localStorage.getItem("corsu-language"); } catch (error) {}
let chosen = Boolean(language);
let state = null, page = null, picks = null, closed = false, showLog = false;
// Set while Corsu restarts from a newer installed copy: {pid of the old server, give up after}.
let restarting = null, savingPreference = false, failureShown = null;
const restartHints = new Map(), openDetails = new Map();

const $ = id => document.getElementById(id);
// Browsers have no Corsican number and time formats; the French ones match Corsican usage.
const numbers = () => language === "co" ? "fr" : language;
// The page's own texts, then those of the Appearance and phone pages (texts-appearance.js, texts-phone.js, same
// {co, fr, en} shape) when loaded.
function lookup(name) {
  const lang = language || "fr";
  if (name in text[lang]) return text[lang][name];
  for (const extra of [typeof textsAppearance === "undefined" ? null : textsAppearance,
    typeof textsPhone === "undefined" ? null : textsPhone]) {
    if (extra && extra[lang] && name in extra[lang]) return extra[lang][name];
  }
  return undefined;
}
const t = (name, values = {}) => (lookup(name) ?? name).replace(/\{(\w+)\}/g, (_, k) => values[k]);
function make(tag, attributes = {}, ...children) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) {
    if (name === "text") node.textContent = value;
    else if (name.startsWith("on")) node.addEventListener(name.slice(2), value);
    else if (value === true) node.setAttribute(name, "");
    else if (value !== false && value != null) node.setAttribute(name, value);
  }
  node.append(...children.filter(child => child != null));
  return node;
}

// An icon of the page's sprite (index.html): decorative, the text next to it or the control's name says it all.
const SVG = "http://www.w3.org/2000/svg";
function icon(name, extra) {
  const svg = document.createElementNS(SVG, "svg");
  svg.setAttribute("class", extra ? "icon " + extra : "icon");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  const use = document.createElementNS(SVG, "use");
  use.setAttribute("href", "#i-" + name);
  svg.append(use);
  return svg;
}

// A recognisable shape for each kind of program; any other gets the plain application icon.
const programIcons = { firefox: "globe", chromium: "globe", discord: "chat", vesktop: "chat", desktop: "monitor", kde: "monitor",
  qt: "monitor", terminal: "terminal", minecraft: "cube", vlc: "play", audacity: "wave", tenacity: "wave", freac: "wave",
  poedit: "translate", pdfsam: "file" };
const appIcon = name => make("span", { class: "app-icon", "aria-hidden": "true" }, icon(programIcons[name] || "app"));

// Each state's tone and icon: a chip always carries a word, the colour only repeats it.
const tones = { active: ["ok", "ok"], inactive: ["neutral", "off"], partial: ["warn", "partial"], restart_required: ["info", "restart"],
  blocked: ["danger", "blocked"], failed: ["danger", "error"], waiting: ["warn", "clock"] };
function chip(activation, attributes = {}, label = null, tone = null) {
  const [own, glyph] = tones[activation] || ["neutral", "about"];
  return make("span", { ...attributes, class: `badge chip ${activation} tone-${tone || own}` },
    icon(tone === "warn" && own !== "warn" ? "warn" : glyph), make("span", { text: label || activationLabel(activation) }));
}

async function call(path, body) {
  await corsuAccess.ready;
  const response = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: corsuAccess.headers({ "Content-Type": "application/json" }),
    body: body ? JSON.stringify({ language, ...body }) : undefined,
  });
  if (response.status === 409) { alert(t("busy")); return null; }
  if (!response.ok) throw new Error(String(response.status));
  return response.json();
}

function show(name) {
  page = name;
  for (const button of document.querySelectorAll("[data-page]")) {
    if (button.dataset.page === name) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  }
  for (const panel of document.querySelectorAll("[data-page-panel]")) panel.hidden = panel.id !== name;
  if (state) { renderSummary(); renderUpdate(); }
  // The Appearance page (appearance.js) and anything else that renders on demand listens to this.
  if (typeof CustomEvent === "function" && document.dispatchEvent) document.dispatchEvent(new CustomEvent("corsu:page", { detail: name }));
}

// Activation (is Corsican switched on?) and coverage (how much of the program is translated) are separate:
// a program fully switched on with a partial catalogue is "active", not a partial failure.
// Older saved states only carry `on`; the state is read from it then.
function activationOf(item) {
  if (item.activation) return item.activation;
  if (item.on) return "active";
  return item.installed && item.switchable ? "inactive" : null;
}

function activationLabel(activation) {
  const key = "activation_" + activation;
  return lookup(key) != null ? t(key) : activation;
}

function coverageText(coverage) {
  if (!coverage) return null;
  if (coverage.state === "complete") return t("coverage_complete");
  if (coverage.state !== "partial") return null;
  const { translated, total } = coverage;
  if (!Number.isFinite(translated) || !Number.isFinite(total) || total <= 0) return t("coverage_partial");
  // Never "100 %" while messages are still missing.
  let percent = Math.round(translated / total * 100);
  if (translated < total) percent = Math.min(percent, 99);
  return t("coverage_count", { translated: translated.toLocaleString(numbers()), total: total.toLocaleString(numbers()),
    percent: (percent / 100).toLocaleString(numbers(), { style: "percent" }) });
}

function validationText(validation) {
  if (!validation) return null;
  const real = validation.real_app || [];
  if (!validation.simulated && !real.length && !validation.visual && !validation.linguistic_review) return t("tested_none");
  const parts = [];
  if (validation.simulated) parts.push(t("tested_simulated"));
  parts.push(real.length ? t("tested_real", { systems: real.map(system => systems[system] || system).join(", ") }) : t("tested_no_real"));
  parts.push(t(validation.visual ? "tested_visual" : "tested_no_visual"));
  parts.push(t(validation.linguistic_review ? "tested_review" : "tested_no_review"));
  return t("tested", { list: parts.join(" · ") });
}

const troubled = activation => activation === "blocked" || activation === "failed";
const noted = instance => Boolean(instance.reason || instance.action);
const ordinaryState = activation => activation === "active" || activation === "inactive" || activation === null;

// What a row says about its program. The chip (state as icon + word) only when something is unusual; coverage, tests and
// each installation sit in a disclosure, opened by default when something needs the person's attention.
// Nothing for the fixed parts (Firefox, Discord…) and old saved states: the switch already says it all.
function statusBlock(item) {
  const activation = activationOf(item);
  const instances = Array.isArray(item.instances) ? item.instances : [];
  const coverage = coverageText(item.coverage);
  const tested = validationText(item.validation);
  const ordinary = ordinaryState(activation);
  if (ordinary && !instances.length && !coverage && !tested) return { chip: null, nodes: [], kind: null };
  const attention = !ordinary || instances.some(instance => instance.activation !== "active" && instance.activation !== "inactive") || instances.some(noted);
  const kind = troubled(activation) ? "problem" : attention ? "attention" : null;
  let badge = null;
  if (activation !== null && kind) {
    const waiting = ordinary && item.waiting;
    badge = chip(waiting ? "waiting" : activation, { id: "status-" + item.name }, waiting ? t("waiting_folders") : null, ordinary && !waiting ? "warn" : null);
  }
  // Opened by default when something needs the person's attention; then it stays as they leave it.
  const open = openDetails.has(item.name) ? openDetails.get(item.name) : attention;
  const details = make("details", { class: "more", open, ontoggle: event => {
    // The first event only echoes the default; from then on the person's choice is kept.
    if (event.target.open !== open || openDetails.has(item.name)) openDetails.set(item.name, event.target.open);
  } },
    make("summary", { id: "details-" + item.name }, icon("chevron", "turn"),
      make("span", { text: !instances.length ? t("row_details") : instances.length === 1 ? t("instances_one") : t("instances_many", { n: instances.length }) })),
    make("div", { class: "more-body" },
      coverage ? make("span", { class: "coverage", text: coverage }) : null,
      tested ? make("span", { class: "tested", text: tested }) : null,
      instances.length ? make("ul", { class: "instances" }, ...instances.map(instanceRow)) : null,
      item.updated ? make("span", { class: "when", text: t("status_as_of", { time: new Date(item.updated * 1000).toLocaleString(numbers(), { dateStyle: "short", timeStyle: "short" }) }) }) : null));
  return { chip: badge, nodes: [details], kind };
}

function instanceRow(instance) {
  // Minecraft folders also name their mod loader (Fabric, NeoForge…) next to the game version.
  const title = [instance.kind, instance.version, instance.loader].filter(Boolean).join(" ");
  const coverage = coverageText(instance.coverage);
  const note = instance.coverage && instance.coverage.note;
  // Reason and action come written by the installer, in French or English: shown as they are.
  return make("li", { class: "instance tone-" + ((tones[instance.activation] || ["neutral"])[0]) },
    make("span", { class: "instance-head" }, title ? make("b", { text: title }) : null, " ",
      chip(instance.activation), coverage ? make("span", { class: "muted", text: " " + coverage }) : null),
    instance.location ? make("span", { class: "where", text: instance.location }) : null,
    instance.reason ? make("span", { class: "reason", text: instance.reason }) : null,
    instance.action ? make("span", { class: "hint", text: instance.action }) : null,
    note ? make("span", { class: "muted", text: note }) : null,
    instance.note ? make("span", { class: "hint", text: instance.note }) : null);
}

function rowClass(block) {
  return [block.nodes.length ? "tall" : null, block.kind].filter(Boolean).join(" ") || null;
}

// VLC's experimental complement (apps/vlc_complement.py): its own switch, off unless the person asks for it. Switching
// it re-applies VLC (with or without the complement); VLC's own switch stays as it is.
function complementOption(item, name, busy) {
  const complement = item.complement;
  if (!complement) return null;
  const id = "switch-" + item.name + "-complement";
  const count = Number.isFinite(complement.translations) && complement.translations > 0 ? complement.translations : null;
  // The reason comes from the server, in French or English: shown as it is.
  const why = !item.on ? t("complement_vlc_off")
    : !complement.available ? t("complement_unavailable", { reason: String(complement.reason || "?").trim().replace(/[.;:]$/, "") }) : null;
  // Still switchable off when the choice is on but cannot be used here, so it never comes back unasked.
  const usable = item.on && (complement.available || complement.enabled);
  return make("span", { class: "option" + (usable ? "" : " off") },
    make("span", { class: "label" },
      make("label", { for: id, text: t("complement_label") }),
      make("span", { class: "detail", id: id + "-detail", text: count ? t("complement_detail_count", { n: count.toLocaleString(numbers()) }) : t("complement_detail") }),
      // Switching VLC on is something to do (a hint); a VLC the complement cannot work with is only explained.
      why ? make("span", { class: item.on ? "detail" : "hint", id: id + "-why", text: why }) : null),
    make("span", { class: "switch" },
      make("input", { type: "checkbox", role: "switch", id, checked: Boolean(complement.enabled), disabled: busy || !usable,
        "aria-describedby": [id + "-detail", why ? id + "-why" : null].filter(Boolean).join(" "), onchange: event => {
        showLog = false;
        restartHints.set(item.name, t("restart", { name }));
        call("/api/vlc-complement", { on: event.target.checked }).catch(() => null).then(refresh);
      } }),
      make("i")));
}

// The program's name with its chip, then its description.
function headline(forId, name, block) {
  return make("span", { class: "headline" }, forId ? make("label", { for: forId, text: name }) : make("span", { class: "name", text: name }), block.chip);
}

function switchRow(item, busy) {
  const [name, detail] = item.text[language];
  const id = "switch-" + item.name;
  const block = statusBlock(item);
  // A restart cannot show a change that did not happen.
  const hint = troubled(activationOf(item)) ? null : restartHints.get(item.name);
  const option = complementOption(item, name, busy);
  // The complement's own switch makes the row tall: VLC's switch stays at the top, next to its name.
  const classes = new Set((rowClass(block) || "").split(" ").filter(Boolean));
  if (option) classes.add("tall");
  return make("li", { class: [...classes].join(" ") || null, id: "row-" + item.name },
    appIcon(item.name),
    make("span", { class: "label" },
      headline(id, name, block),
      make("span", { class: "detail", id: "desc-" + item.name, text: detail }),
      ...block.nodes,
      hint ? make("span", { class: "hint", text: hint }) : null,
      // New Minecraft game folders found since the installation: switched only when the person asks.
      item.waiting ? make("span", { class: "buttons" }, make("button", { type: "button", class: "button small", id: "activate-" + item.name,
        text: t("minecraft_switch_new"), disabled: busy, onclick: () => { showLog = false; call("/api/install", { components: [item.name] }).then(refresh); } })) : null,
      option),
    make("span", { class: "switch" },
      // Always the server's word: after a failed or deferred change, the next refresh puts it back.
      make("input", { type: "checkbox", role: "switch", id, checked: item.on, disabled: busy,
        "aria-describedby": [block.chip ? "status-" + item.name : null, "desc-" + item.name].filter(Boolean).join(" "), onchange: event => {
        restartHints.set(item.name, item.name === "desktop" ? t("restart_desktop") : t("restart", { name }));
        call("/api/switch", { components: [item.name], on: event.target.checked }).catch(() => null).then(refresh);
      } }),
      make("i")));
}

// Parts redrawn at every refresh (every 1.5 s) are only replaced when what they show (the key) changed: a link or button keeps
// the keyboard focus, and a live region (role=status, aria-live) is not announced again with the same words.
const drawn = new Map();
function replaceWhenChanged(parent, key, build) {
  if (drawn.get(parent) === key) return;
  drawn.set(parent, key);
  parent.replaceChildren(...build());
}
const setText = (node, value) => { if (node.textContent !== String(value)) node.textContent = value; };

// Rows are rebuilt at every refresh: keep the focused control and the opened details where they were.
function replaceKeepingFocus(list, rows) {
  const focused = list.contains(document.activeElement) ? document.activeElement.id : null;
  list.replaceChildren(...rows);
  if (focused && $(focused)) $(focused).focus();
}

// Problems first, then what needs attention, then the rest in their usual order.
const rank = item => ({ problem: 0, attention: 1 })[statusBlock(item).kind] ?? 2;
const shown = () => state.items.filter(item => item.name !== "terminal" && item.installed);

function renderPrograms() {
  const busy = state.job.running;
  const list = $("switches");
  const rows = shown().map((item, index) => ({ item, index, rank: rank(item) }))
    .sort((a, b) => a.rank - b.rank || a.index - b.index)
    .map(({ item }) => {
      if (item.switchable) return switchRow(item, busy);
      const [name, detail] = item.text[language];
      const block = statusBlock(item);
      return make("li", { class: rowClass(block), id: "row-" + item.name }, appIcon(item.name),
        make("span", { class: "label" }, headline(null, name, block), make("span", { class: "detail", text: detail }), ...block.nodes),
        make("span", { class: "state" }, icon("ok"), make("span", { text: t("installed") })));
    });
  if (!rows.length) {
    rows.push(make("li", { class: "empty-row" }, make("span", { class: "app-icon", "aria-hidden": "true" }, icon("add")),
      make("span", { class: "label muted", text: t("programs_none") }),
      make("button", { type: "button", class: "button default", text: t("go_add"), onclick: () => show("add") })));
  }
  replaceKeepingFocus(list, rows);
  setText($("programs-lead"), t("programs_lead"));

  const terminal = state.items.find(item => item.name === "terminal");
  $("terminal-block").hidden = !terminal;
  if (terminal) {
    const until = state.terminal_paused_until;
    $("switch-terminal").checked = until === null;
    $("switch-terminal").disabled = busy;
    setText($("terminal-detail"), until === null ? t("terminal_on") : until === 0 ? t("terminal_off")
      : t("terminal_until", { time: new Date(until * 1000).toLocaleTimeString(numbers(), { hour: "2-digit", minute: "2-digit" }) }));
    $("pause-hour").hidden = until !== null;
    $("pause-hour").disabled = busy;
  }

  const off = state.everything_off;
  setText($("everything-text"), t(off ? "everything_off_text" : "everything_on_text"));
  setText($("everything"), t(off ? "everything_on" : "everything_off"));
  $("everything-button").disabled = busy || !state.installed;
}

// Opens a program's details from the summary and brings its row into view, focus on its switch.
function jumpTo(name) {
  openDetails.set(name, true);
  render();
  const row = $("row-" + name);
  if (row && row.scrollIntoView) row.scrollIntoView({ block: "center" });
  const target = $("switch-" + name) || $("details-" + name);
  if (target) target.focus({ preventScroll: true });
}

// Programs at a glance: how many speak Corsican, which need the person, whether Corsu has an update.
function renderSummary() {
  const installed = shown();
  $("summary").hidden = !installed.length;
  if (!installed.length) return;
  const on = installed.filter(item => ["active", "partial", null].includes(activationOf(item))).length;
  setText($("summary-on-value"), t("summary_on", { n: on.toLocaleString(numbers()), total: installed.length.toLocaleString(numbers()) }));
  setText($("summary-on-sub"), on < installed.length ? t("summary_off", { n: (installed.length - on).toLocaleString(numbers()) }) : t("summary_all"));
  $("summary-on").className = "stat tone-" + (on ? "ok" : "neutral");

  const flagged = installed.map(item => ({ item, kind: statusBlock(item).kind })).filter(entry => entry.kind)
    .sort((a, b) => (a.kind === "problem" ? 0 : 1) - (b.kind === "problem" ? 0 : 1));
  const worst = flagged.some(entry => entry.kind === "problem") ? "danger" : flagged.length ? "warn" : "ok";
  $("summary-attention").className = "stat tone-" + worst;
  $("summary-attention-icon").setAttribute("href", "#i-" + (worst === "danger" ? "error" : worst === "warn" ? "warn" : "ok"));
  setText($("summary-attention-value"), !flagged.length ? t("summary_ok")
    : flagged.length === 1 ? t("summary_attention_one") : t("summary_attention_many", { n: flagged.length.toLocaleString(numbers()) }));
  const jumps = flagged.map(({ item }) => {
    const [name] = item.text[language];
    const activation = activationOf(item);
    const instance = (item.instances || []).find(instance => noted(instance) && instance.activation !== "inactive");
    const why = item.waiting && ordinaryState(activation) ? t("waiting_folders") : !ordinaryState(activation) ? activationLabel(activation)
      : instance ? (instance.action || instance.reason).trim().replace(/[.;:]$/, "") : activationLabel(activation);
    return [item.name, name, why];
  });
  replaceWhenChanged($("summary-attention-list"), JSON.stringify([language, jumps]), () => !jumps.length ? [t("summary_ok_detail")]
    : jumps.map(([id, name, why]) => make("button", { type: "button", class: "jump", onclick: () => jumpTo(id) },
      make("span", { class: "jump-text" }, make("b", { text: name }), " ", make("span", { text: why })), icon("chevron"))));

  const info = updateInfo(), restart = restartInfo(), job = state.job;
  const blocked = job.running || Boolean(restarting);
  const updating = job.title === "update" && job.running;
  let tone = "ok", glyph = "ok", value = "Corsu " + (info.current || state.version), text = updateStatus().text;
  if (restart.available && !restarting) { tone = "info"; glyph = "restart"; value = t("summary_update_installed"); text = t("update_restart_text", { version: restart.version }); }
  else if (updating) { tone = "info"; glyph = "update"; text = info.auto_started ? t("update_auto_started", { version: info.auto_started }) : t("running", { job: t("job_update") }); }
  else if (info.status === "available") {
    tone = "info"; glyph = "update"; value = t("summary_update_available");
    text = t("summary_update_versions", { version: info.latest, current: info.current || state.version });
  }
  else if (info.status === "unknown") { tone = "warn"; glyph = "warn"; }
  else if (info.status !== "up_to_date") { tone = "neutral"; glyph = "about"; }
  $("summary-update").className = "stat tone-" + tone;
  $("summary-update-icon").setAttribute("href", "#i-" + glyph);
  setText($("summary-update-value"), value);
  setText($("summary-update-text"), text);
  $("summary-update-install").hidden = Boolean(restart.available) || updating || info.status !== "available";
  $("summary-update-install").disabled = blocked;
  $("summary-update-restart").hidden = !restart.available || Boolean(restarting);
  $("summary-update-restart").disabled = blocked;
}

function renderAdd() {
  const candidates = state.items.filter(item => !item.installed && item.name !== "terminal");
  if (picks === null) picks = new Set(candidates.map(item => item.name));
  setText($("add-lead"), t("add_lead"));
  const rows = candidates.map(item => {
    const [name, detail] = item.text[language];
    const id = "pick-" + item.name;
    // A first attempt that switched nothing leaves the program here: say why.
    const block = statusBlock(item);
    return make("li", { class: rowClass(block) },
      make("input", { type: "checkbox", class: "pick", id, checked: picks.has(item.name), "aria-describedby": "add-desc-" + item.name, onchange: event => {
        if (event.target.checked) picks.add(item.name); else picks.delete(item.name);
      } }),
      appIcon(item.name),
      make("span", { class: "label" }, headline(id, name, block), make("span", { class: "detail", id: "add-desc-" + item.name, text: detail }), ...block.nodes));
  });
  replaceKeepingFocus($("choices"), rows.length ? rows : [make("li", { class: "empty-row" },
    make("span", { class: "app-icon", "aria-hidden": "true" }, icon("ok")), make("span", { class: "label muted", text: t("add_none") }))]);
  $("plan-open").hidden = !candidates.length;
  $("plan-open").disabled = state.job.running;
}

function linkRow(href, title, detail, glyph = "book") {
  return make("li", { class: "link" },
    make("span", { class: "app-icon", "aria-hidden": "true" }, icon(glyph)),
    make("a", { class: "label", href, target: "_blank", rel: "noopener noreferrer" },
      make("span", { class: "name", text: title }), detail ? make("span", { class: "detail", text: detail }) : null,
      make("span", { class: "sr-only", text: " " + t("opens_browser") })),
    make("span", { class: "external", "aria-hidden": "true" }, icon("external")));
}


function renderHelp() {
  const fr = language !== "en";
  const computer = fr ? `fr/ordinateur/${state.platform}.md` : `en/computer/${state.platform}.md`;
  replaceWhenChanged($("guides"), language + state.platform, () => [
    linkRow(docs + computer, t("guide_install", { system: systems[state.platform] || state.platform })),
    linkRow(docs + (fr ? "fr/discord.md" : "en/discord.md"), t("guide_discord")),
    linkRow(docs + (fr ? "fr/telephone/android.md" : "en/phone/android.md"), t("guide_phone")),
    linkRow(docs + (fr ? "fr/compatibilite.md" : "en/compatibility.md"), t("guide_compat")),
    linkRow(docs + (fr ? "fr/ce-que-corsu-modifie.md" : "en/what-corsu-changes.md"), t("guide_changes")),
    linkRow(docs + (fr ? "fr/pourquoi-corsu.md" : "en/why-corsu.md"), t("guide_why")),
    linkRow("https://github.com/Platykalt/corsu/issues/new?template=translation.yml", t("report"), null, "review")]);
  replaceWhenChanged($("practice"), language, () => [
    linkRow("https://www.sapienzia.io", "Sapienzia", t("sapienzia"), "translate"),
    linkRow("https://astutu.corsica", "Astutu", t("astutu"), "chat"),
    linkRow("https://liv.corsica", "LIV", t("liv"), "chat")]);
}

function renderAbout() {
  const rows = [[t("system"), systems[state.platform] || state.platform],
    [t("lexicon"), t("lexicon_count", { n: state.lexicon_entries.toLocaleString(numbers()) })]];
  if (state.firefox_profile) rows.push([t("profile"), state.firefox_profile]);
  replaceWhenChanged($("facts"), JSON.stringify([language, rows]), () => [
    ...rows.flatMap(([term, value]) => [make("dt", { text: term }), make("dd", { text: value })]),
    make("dt", { text: t("source") }),
    make("dd", {}, make("a", { href: "https://github.com/Platykalt/corsu", target: "_blank", rel: "noopener noreferrer", text: "github.com/Platykalt/corsu" }))]);
  $("remove").disabled = !state.installed || state.job.running;
}

function renderActivity() {
  const job = state.job;
  const bar = $("activity");
  bar.hidden = !job.title;
  if (!job.title) return;
  const name = t("job_" + job.title);
  // running, done or failed: the icon beside the sentence follows it (the sentence says it in words).
  bar.className = "activity " + (job.running ? "running" : job.ok === false || job.busy ? "failed" : "done");
  // A filling bar when the task reports its progress; the small spinner only for quick changes.
  const progress = job.progress;
  $("meter").hidden = !progress;
  $("busy").hidden = !job.running;
  if (progress) {
    const percent = job.running ? progress.percent : job.ok ? 100 : progress.percent;
    $("meter-fill").style.width = percent + "%";
    $("meter").setAttribute("aria-valuenow", percent);
  }
  setText($("step"), job.running && progress ? progress.label : "");
  // The installer lock stopped the run: another window or installer is at work, nothing failed.
  setText($("activity-text"), !job.running && job.busy ? t("busy") : t(job.running ? "running" : job.ok ? "done" : "failed", { job: name }));
  // A failed run opens its log once; «Hide details» then keeps it closed (the next run may open it again).
  const failure = job.ok === false && !job.running ? [job.title, job.lines.length, job.lines[job.lines.length - 1]].join("\n") : null;
  if (job.running) failureShown = null;
  else if (failure && failure !== failureShown) { showLog = true; failureShown = failure; }
  setText($("details-toggle"), t(showLog ? "hide_details" : "show_details"));
  $("details-toggle").setAttribute("aria-expanded", String(showLog));
  const log = $("log");
  log.hidden = !showLog;
  const atEnd = log.scrollTop + log.clientHeight >= log.scrollHeight - 8;
  setText(log, job.lines.join("\n"));
  if (atEnd) log.scrollTop = log.scrollHeight;
}

let reviewItem = null, reviewSection = "Discord";

async function loadReview() {
  const result = await call(`/api/review/next?section=${reviewSection}`);
  if (!result) return;
  reviewItem = result.item;
  const progress = result.progress[reviewSection];
  $("review-progress").textContent = t("review_progress", { done: progress.done.toLocaleString(numbers()), total: progress.total.toLocaleString(numbers()), fixed: t((language === "fr" ? progress.fixed <= 1 : progress.fixed === 1) ? "corrections_one" : "corrections_many", { n: progress.fixed }) });
  $("review-card").hidden = !reviewItem;
  $("review-done").hidden = Boolean(reviewItem);
  $("review-error").hidden = true;
  if (!reviewItem) return;
  $("review-french").textContent = reviewItem.french || "—";
  $("review-english").textContent = reviewItem.english || "—";
  $("review-corsican").value = reviewItem.corsican;
  $("review-fix").disabled = true;
}

async function answer(verdict) {
  if (!reviewItem) return;
  const corsican = $("review-corsican").value;
  const response = await fetch("/api/review", { method: "POST", headers: corsuAccess.headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ language, french: reviewItem.french, english: reviewItem.english, verdict, corsican }) });
  if (!response.ok) {
    const result = await response.json().catch(() => ({}));
    $("review-error").textContent = result.error || response.status;
    $("review-error").hidden = false;
    return;
  }
  await loadReview();
  $("review-corsican").focus();
}

// Sentences from update.py and the installer come in French or English, sometimes without a final full stop.
const sentence = value => /[.!?…]$/.test(value.trim()) ? value.trim() : value.trim() + ".";
const updateInfo = () => state.update || {};
const restartInfo = () => updateInfo().restart || {};
// When GitHub gave the answer shown: a saved answer keeps its own date, it never reads as a check just made.
const checkedAt = info => info.checked ? new Date(info.checked * 1000).toLocaleString(numbers(), { dateStyle: "medium", timeStyle: "short" }) : "—";

function updateStatus() {
  const info = updateInfo();
  const current = info.current || state.version;
  if (info.checking) return { kind: "checking", text: t("update_checking") };
  // Installed but this window still runs the previous copy: that is what matters now.
  if (restartInfo().available && !restarting) return { kind: "available", text: t("update_restart_text", { version: restartInfo().version }) };
  if (info.status === "up_to_date") return { kind: "up_to_date", text: t("update_up_to_date", { version: info.latest, date: checkedAt(info) }) };
  if (info.status === "available") return { kind: "available", text: t("update_available", { version: info.latest, current }) };
  if (info.status === "ahead") return { kind: "ahead", text: t("update_ahead", { version: info.latest, current }) };
  if (info.status === "unknown") return { kind: "unknown", text: info.error ? t("update_unknown", { reason: info.error.trim().replace(/\.$/, "") }) : t("update_unknown_plain") };
  return { kind: "none", text: t("update_never") };
}

// The parts an update could not switch yet (a program open, a new Minecraft folder), with the installer's advice.
function waitingParts() {
  return state.items.filter(item => item.installed && (["blocked", "restart_required", "partial"].includes(activationOf(item)) || item.waiting))
    .map(item => {
      const [name] = item.text[language];
      const instance = (item.instances || []).find(instance => instance.activation !== "active" && (instance.action || instance.reason));
      const why = instance ? (instance.action || instance.reason).trim().replace(/[.;:]$/, "") : null;
      return why ? `${name} (${why})` : name;
    });
}

// What the last update did, in a few lines: Corsu itself, then the parts still waiting, then the restart.
function updateResult() {
  const job = state.job, info = updateInfo(), restart = restartInfo();
  const lines = [];
  let kind = null;
  if (restarting) lines.push(t("update_restarting"));
  else if (job.title === "update" && job.running && info.auto_started) lines.push(t("update_auto_started", { version: info.auto_started }));
  else if (job.title === "update" && !job.running) {
    const result = job.result || {};
    if (job.busy) { lines.push(t("busy")); kind = "attention"; }
    else if (["updated", "repaired", "unchanged"].includes(result.corsu) && job.ok !== false) {
      lines.push(t("update_" + result.corsu, { version: result.to || info.latest || state.version }));
      const waiting = waitingParts();
      if (waiting.length) {
        lines.push(waiting.length === 1 ? t("update_waiting_one", { list: waiting[0] }) : t("update_waiting_many", { n: waiting.length, list: waiting.join(language === "en" ? "; " : " ; ") }));
        kind = "attention";
      }
    } else if (job.ok === false || result.corsu === "failed") {
      lines.push(result.error ? t("update_failed", { error: sentence(result.error) }) : t("update_failed_plain"));
      kind = "problem";
    }
  }
  if (!restarting && restart.error) { lines.push(t("update_restart_failed", { error: restart.error.replace(/\.$/, "") })); kind = "problem"; }
  return { lines, kind };
}

function renderUpdate() {
  const info = updateInfo(), restart = restartInfo(), job = state.job;
  // The window's own version, the installed copy's (another one after an update until Corsu restarts), GitHub's.
  const installed = info.installed || restart.version || "—";
  const updateFacts = [[t("update_current"), info.current || state.version], [t("update_installed"), installed],
    [t("update_latest"), info.latest || "—"], [t("update_checked"), checkedAt(info)]];
  replaceWhenChanged($("update-facts"), JSON.stringify(updateFacts), () => updateFacts.flatMap(([term, value]) => [make("dt", { text: term }), make("dd", { text: value })]));
  const status = updateStatus();
  $("update-status").className = "update-status " + status.kind;
  const glyph = { up_to_date: "ok", available: "update", unknown: "warn", ahead: "about", none: "clock" }[status.kind];
  replaceWhenChanged($("update-status"), status.kind + "\n" + status.text, () => [status.kind === "checking" ? make("span", { class: "busy", "aria-hidden": "true" }) : icon(glyph),
    make("span", { text: status.text })]);
  const result = updateResult();
  $("update-result").hidden = !result.lines.length;
  $("update-result").className = "update-result" + (result.kind ? " " + result.kind : "");
  replaceWhenChanged($("update-result"), JSON.stringify(result.lines), () => result.lines.map(line => make("span", { text: line })));
  // One job at a time: every button waits while something runs, or while Corsu restarts.
  const blocked = job.running || Boolean(restarting);
  $("update-now").hidden = Boolean(restart.available);
  $("update-now").disabled = info.status !== "available" || blocked;
  $("update-restart").hidden = !restart.available;
  $("update-restart").disabled = blocked;
  $("update-check").disabled = Boolean(info.checking) || blocked;
  $("switch-auto-update").checked = Boolean(state.preferences && state.preferences.auto_update);
  $("switch-auto-update").disabled = savingPreference;

  // The banner on every page: a release to install, an automatic update under way, or a restart to do.
  const autoRunning = job.title === "update" && job.running && info.auto_started;
  // On Programs the summary carries it (when there is one); About has its own section.
  const show = !restarting && page !== "about" && !(page === "programs" && !$("summary").hidden) && (restart.available || autoRunning || (info.status === "available" && !(job.title === "update" && job.running)));
  $("update-banner").hidden = !show;
  if (show) setText($("update-text"), restart.available ? t("update_restart_text", { version: restart.version })
    : autoRunning ? t("update_auto_started", { version: info.auto_started }) : t("update_available", { version: info.latest, current: info.current || state.version }));
  $("update-install").hidden = Boolean(restart.available || autoRunning);
  $("update-install").disabled = blocked;
  $("update-banner-restart").hidden = !restart.available;
  $("update-banner-restart").disabled = blocked;
}

function renderExtras() {
  renderUpdate();
  $("switch-original").checked = Boolean(state.options && state.options.showOriginal);
}

async function startUpdate() {
  showLog = false;
  await call("/api/update", {}).catch(() => null);
  refresh();
}

async function restartCorsu() {
  const before = state.pid;
  let result = null;
  try {
    const response = await fetch("/api/restart", { method: "POST", headers: corsuAccess.headers({ "Content-Type": "application/json" }), body: JSON.stringify({ language }) });
    result = await response.json().catch(() => ({}));
    if (response.status === 409) { alert(t("busy")); return refresh(); }
    if (!response.ok) { alert(t("update_restart_failed", { error: String(result.error || response.status).replace(/\.$/, "") })); return refresh(); }
  } catch (error) { return refresh(); }
  // The address stays the same: the page waits for the new copy, then reloads from it.
  restarting = { pid: before, until: Date.now() + 45000 };
  render();
}

function render() {
  document.documentElement.lang = language;
  document.title = "Corsu";
  for (const node of document.querySelectorAll("[data-t]")) setText(node, t(node.dataset.t));
  for (const node of document.querySelectorAll("[data-t-label]")) node.setAttribute("aria-label", t(node.dataset.tLabel));
  // Icon-only navigation on narrow windows: the label stays the name, the tooltip shows it to the pointer.
  for (const node of document.querySelectorAll("[data-page]")) node.title = t("nav_" + node.dataset.page);
  $("language").value = language;
  if (!state) return;
  setText($("version"), state.version);
  // Shown as the server wrote it (French or English): it names the damaged file and what was kept.
  setText($("problem-text"), state.problem || "");
  $("problem").hidden = !state.problem;
  renderPrograms(); renderSummary(); renderAdd(); renderHelp(); renderAbout(); renderActivity(); renderExtras();
  if (typeof CustomEvent === "function" && document.dispatchEvent) document.dispatchEvent(new CustomEvent("corsu:render", { detail: language }));
}

async function refresh() {
  let next;
  try {
    next = await call("/api/state");
  } catch (error) {
    // While Corsu restarts, the address is silent for a moment.
    if (restarting && Date.now() < restarting.until) return;
    if (closed) return;
    closed = true;
    // Refused: this page has no key (an old tab or bookmark, a key replaced), Corsu is open but not for it.
    const refused = error.message === "403";
    document.querySelector("main").replaceChildren(make("p", { class: "closed", text: t(refused ? "locked" : "closed") }));
    $("activity").hidden = true;
    return;
  }
  // A mistake while drawing is not Corsu closing: it is reported, and the next refresh draws again.
  try {
    if (restarting) {
      // Another process answers: the new copy, with its own page.
      if (next.pid !== restarting.pid) { window.location.reload(); return; }
      if ((next.update && next.update.restart && next.update.restart.error) || Date.now() > restarting.until) restarting = null;
    }
    if (state && state.job.running && !next.job.running) picks = null;
    state = next;
    if (page === null) show(state.installed ? "programs" : "add");
    render();
  } catch (error) {
    console.error(error);
  }
}

for (const button of document.querySelectorAll("[data-page]")) button.addEventListener("click", () => {
  show(button.dataset.page);
  if (button.dataset.page === "review") loadReview();
});
$("review-section").addEventListener("change", event => { reviewSection = event.target.value; loadReview(); });
$("review-corsican").addEventListener("input", () => { $("review-fix").disabled = !reviewItem || $("review-corsican").value === reviewItem.corsican; });
$("review-corsican").addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); answer($("review-fix").disabled ? "ok" : "fix"); }
});
$("review-ok").addEventListener("click", () => answer("ok"));
$("review-fix").addEventListener("click", () => answer("fix"));
$("review-skip").addEventListener("click", () => answer("skip"));
$("review-send").addEventListener("click", async () => {
  const result = await call("/api/review/issue");
  if (!result || !result.count) { alert(t("review_none")); return; }
  if (result.url.includes("body=")) { window.open(result.url, "_blank", "noopener"); return; }
  try { await navigator.clipboard.writeText(result.text); } catch (error) {}
  alert(t("review_copied"));
  window.open(result.url, "_blank", "noopener");
});
$("switch-original").addEventListener("change", event => call("/api/options", { showOriginal: event.target.checked }).then(refresh));
$("open-logs").addEventListener("click", () => call("/api/logs", {}));
$("update-install").addEventListener("click", startUpdate);
$("summary-update-install").addEventListener("click", startUpdate);
$("summary-update-restart").addEventListener("click", restartCorsu);
$("update-now").addEventListener("click", startUpdate);
$("update-restart").addEventListener("click", restartCorsu);
$("update-banner-restart").addEventListener("click", restartCorsu);
$("update-check").addEventListener("click", () => {
  $("update-check").disabled = true;
  call("/api/update/check", {}).catch(() => null).then(refresh);
});
$("switch-auto-update").addEventListener("change", event => {
  savingPreference = true;
  call("/api/preferences", { auto_update: event.target.checked }).catch(() => null).then(() => { savingPreference = false; refresh(); });
});
$("rescan").addEventListener("click", () => { picks = null; call("/api/rescan", {}).then(refresh); });
$("language").addEventListener("change", event => {
  language = event.target.value; chosen = true;
  try { localStorage.setItem("corsu-language", language); } catch (error) {}
  render();
});
$("switch-terminal").addEventListener("change", event => {
  call(event.target.checked ? "/api/switch" : "/api/pause", { components: ["terminal"], on: true }).then(refresh);
});
$("pause-hour").addEventListener("click", () => call("/api/pause", { hours: 1 }).then(refresh));
$("everything-button").addEventListener("click", () => call("/api/all", { on: state.everything_off }).then(refresh));
$("details-toggle").addEventListener("click", () => { showLog = !showLog; renderActivity(); });
$("plan-open").addEventListener("click", async () => {
  if (!picks.size) { alert(t("pick_one")); return; }
  const result = await call("/api/plan", { components: [...picks] });
  if (!result) return;
  $("plan").textContent = result.plan;
  $("install").hidden = !result.ok;
  $("plan-dialog").showModal();
});
$("install").addEventListener("click", () => {
  $("plan-dialog").close();
  showLog = false;
  call("/api/install", { components: [...picks] }).then(refresh);
});
$("remove").addEventListener("click", () => $("remove-dialog").showModal());
$("remove-confirm").addEventListener("click", () => {
  $("remove-dialog").close();
  call("/api/uninstall", {}).then(refresh);
});
for (const button of document.querySelectorAll("[data-close]")) button.addEventListener("click", () => button.closest("dialog").close());

// What appearance.js (the Appearance page) needs from the page: texts, elements, the server, the language.
window.corsu = { t, make, call, icon, language: () => language };

// Corsican first: the app speaks the language it puts on the computer.
language = language || "co";
render();
refresh();
setInterval(() => { if (!closed) refresh(); }, 1500);
