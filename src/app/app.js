"use strict";
const docs = "https://github.com/Platykalt/corsu/blob/main/docs/";
const systems = { windows: "Windows", macos: "macOS", linux: "Linux" };

let language = null;
try { language = localStorage.getItem("corsu-language"); } catch (error) {}
let chosen = Boolean(language);
let state = null, page = null, picks = null, closed = false, showLog = false;
// Set while Corsu restarts from a newer installed copy: {pid of the old server, give up after}.
let restarting = null, savingPreference = false;
const restartHints = new Map(), openDetails = new Map();

const $ = id => document.getElementById(id);
// Browsers have no Corsican number and time formats; the French ones match Corsican usage.
const numbers = () => language === "co" ? "fr" : language;
const t = (name, values = {}) => (text[language || "fr"][name] ?? name).replace(/\{(\w+)\}/g, (_, k) => values[k]);
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

async function call(path, body) {
  const response = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: { "X-Corsu": "1", "Content-Type": "application/json" },
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
  if (state) renderUpdate();
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
  return key in text[language || "fr"] ? t(key) : activation;
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

// What a row adds under the program's description: status, coverage, testing, and each installation when useful.
// Empty for the fixed parts (Firefox, Discord…) and old saved states: the switch already says it all.
function statusBlock(item) {
  const activation = activationOf(item);
  const instances = Array.isArray(item.instances) ? item.instances : [];
  const coverage = coverageText(item.coverage);
  const tested = validationText(item.validation);
  const ordinary = activation === "active" || activation === "inactive" || activation === null;
  if (ordinary && !instances.length && !coverage && !tested) return { nodes: [], kind: null };
  const nodes = [];
  if (activation !== null || coverage) {
    nodes.push(make("span", { class: "status", id: "status-" + item.name },
      activation !== null ? make("span", { class: "badge " + activation, text: activationLabel(activation) }) : null,
      activation !== null && coverage ? " · " : null, coverage));
  }
  if (tested) nodes.push(make("span", { class: "tested", text: tested }));
  const attention = !ordinary || instances.some(instance => instance.activation !== "active" && instance.activation !== "inactive") || instances.some(noted);
  if (instances.length > 1 || instances.some(instance => instance.activation !== "active") || instances.some(noted)) {
    // Opened by default when something needs the person's attention; then it stays as they leave it.
    const open = openDetails.has(item.name) ? openDetails.get(item.name) : attention;
    nodes.push(make("details", { open, ontoggle: event => {
      // The first event only echoes the default; from then on the person's choice is kept.
      if (event.target.open !== open || openDetails.has(item.name)) openDetails.set(item.name, event.target.open);
    } },
      make("summary", { id: "details-" + item.name, text: instances.length === 1 ? t("instances_one") : t("instances_many", { n: instances.length }) }),
      make("ul", { class: "instances" }, ...instances.map(instanceRow),
        item.updated ? make("li", { class: "when", text: t("status_as_of", { time: new Date(item.updated * 1000).toLocaleString(numbers(), { dateStyle: "short", timeStyle: "short" }) }) }) : null)));
  }
  const kind = troubled(activation) ? "problem" : attention ? "attention" : null;
  return { nodes, kind };
}

function instanceRow(instance) {
  // Minecraft folders also name their mod loader (Fabric, NeoForge…) next to the game version.
  const title = [instance.kind, instance.version, instance.loader].filter(Boolean).join(" ");
  const coverage = coverageText(instance.coverage);
  const note = instance.coverage && instance.coverage.note;
  // Reason and action come written by the installer, in French or English: shown as they are.
  return make("li", {},
    make("span", {}, title ? make("b", { text: title }) : null, title ? " · " : null,
      make("span", { class: "badge " + instance.activation, text: activationLabel(instance.activation) }),
      coverage ? " · " + coverage : null),
    instance.location ? make("span", { class: "where", text: instance.location }) : null,
    instance.reason ? make("span", { text: instance.reason }) : null,
    instance.action ? make("span", { class: "hint", text: instance.action }) : null,
    note ? make("span", { class: "muted", text: note }) : null,
    instance.note ? make("span", { class: "hint", text: instance.note }) : null);
}

function rowClass(block) {
  return [block.nodes.length > 1 || block.nodes.some(node => node.tagName === "DETAILS") ? "tall" : null, block.kind].filter(Boolean).join(" ") || null;
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
  return make("li", { class: [...classes].join(" ") || null },
    make("span", { class: "label" },
      make("label", { for: id, text: name }),
      make("span", { class: "detail", text: detail }),
      ...block.nodes,
      hint ? make("span", { class: "hint", text: hint }) : null,
      // New Minecraft game folders found since the installation: switched only when the person asks.
      item.waiting ? make("span", { class: "buttons" }, make("button", { type: "button", class: "button", id: "activate-" + item.name,
        text: t("minecraft_switch_new"), disabled: busy, onclick: () => { showLog = false; call("/api/install", { components: [item.name] }).then(refresh); } })) : null,
      option),
    make("span", { class: "switch" },
      // Always the server's word: after a failed or deferred change, the next refresh puts it back.
      make("input", { type: "checkbox", role: "switch", id, checked: item.on, disabled: busy,
        "aria-describedby": block.nodes.some(node => node.id === "status-" + item.name) ? "status-" + item.name : null, onchange: event => {
        restartHints.set(item.name, item.name === "desktop" ? t("restart_desktop") : t("restart", { name }));
        call("/api/switch", { components: [item.name], on: event.target.checked }).catch(() => null).then(refresh);
      } }),
      make("i")));
}

// Rows are rebuilt at every refresh: keep the focused control and the opened details where they were.
function replaceKeepingFocus(list, rows) {
  const focused = list.contains(document.activeElement) ? document.activeElement.id : null;
  list.replaceChildren(...rows);
  if (focused && $(focused)) $(focused).focus();
}

function renderPrograms() {
  const busy = state.job.running;
  const list = $("switches");
  const rows = [];
  for (const item of state.items) {
    if (item.name === "terminal") continue;
    if (item.switchable) rows.push(switchRow(item, busy));
    else if (item.installed) {
      const [name, detail] = item.text[language];
      const block = statusBlock(item);
      rows.push(make("li", { class: rowClass(block) },
        make("span", { class: "label" }, make("span", { text: name }), make("span", { class: "detail", text: detail }), ...block.nodes),
        make("span", { class: "state", text: t("installed") })));
    }
  }
  if (!rows.length) {
    rows.push(make("li", {}, make("span", { class: "label muted", text: t("programs_none") }),
      make("button", { type: "button", class: "button", text: t("go_add"), onclick: () => show("add") })));
  }
  replaceKeepingFocus(list, rows);
  $("programs-lead").textContent = t("programs_lead");

  const terminal = state.items.find(item => item.name === "terminal");
  $("terminal-block").hidden = !terminal;
  if (terminal) {
    const until = state.terminal_paused_until;
    $("switch-terminal").checked = until === null;
    $("switch-terminal").disabled = busy;
    $("terminal-detail").textContent = until === null ? t("terminal_on") : until === 0 ? t("terminal_off")
      : t("terminal_until", { time: new Date(until * 1000).toLocaleTimeString(numbers(), { hour: "2-digit", minute: "2-digit" }) });
    $("pause-hour").hidden = until !== null;
    $("pause-hour").disabled = busy;
  }

  const off = state.everything_off;
  $("everything-text").textContent = t(off ? "everything_off_text" : "everything_on_text");
  $("everything").textContent = t(off ? "everything_on" : "everything_off");
  $("everything").disabled = busy || !state.installed;
}

function renderAdd() {
  const candidates = state.items.filter(item => !item.installed && item.name !== "terminal");
  if (picks === null) picks = new Set(candidates.map(item => item.name));
  $("add-lead").textContent = t("add_lead");
  const rows = candidates.map(item => {
    const [name, detail] = item.text[language];
    const id = "pick-" + item.name;
    // A first attempt that switched nothing leaves the program here: say why.
    const block = statusBlock(item);
    return make("li", { class: rowClass(block) },
      make("input", { type: "checkbox", class: "pick", id, checked: picks.has(item.name), onchange: event => {
        if (event.target.checked) picks.add(item.name); else picks.delete(item.name);
      } }),
      make("span", { class: "label" }, make("label", { for: id, text: name }), make("span", { class: "detail", text: detail }), ...block.nodes));
  });
  replaceKeepingFocus($("choices"), rows.length ? rows : [make("li", {}, make("span", { class: "label muted", text: t("add_none") }))]);
  $("review").hidden = !candidates.length;
  $("review").disabled = state.job.running;
}

function linkRow(href, title, detail) {
  return make("li", { class: "link" },
    make("a", { class: "label", href, target: "_blank", rel: "noopener noreferrer" },
      make("span", { text: title }), detail ? make("span", { class: "detail", text: detail }) : null),
    make("span", { class: "external", "aria-hidden": "true", text: "↗" }));
}

function renderHelp() {
  const fr = language !== "en";
  const computer = fr ? `fr/ordinateur/${state.platform}.md` : `en/computer/${state.platform}.md`;
  $("guides").replaceChildren(
    linkRow(docs + computer, t("guide_install", { system: systems[state.platform] || state.platform })),
    linkRow(docs + (fr ? "fr/discord.md" : "en/discord.md"), t("guide_discord")),
    linkRow(docs + (fr ? "fr/telephone/android.md" : "en/phone/android.md"), t("guide_phone")),
    linkRow(docs + (fr ? "fr/compatibilite.md" : "en/compatibility.md"), t("guide_compat")),
    linkRow(docs + (fr ? "fr/ce-que-corsu-modifie.md" : "en/what-corsu-changes.md"), t("guide_changes")),
    linkRow(docs + (fr ? "fr/pourquoi-corsu.md" : "en/why-corsu.md"), t("guide_why")),
    linkRow("https://github.com/Platykalt/corsu/issues/new?template=translation.yml", t("report")));
  $("practice").replaceChildren(
    linkRow("https://www.sapienzia.io", "Sapienzia", t("sapienzia")),
    linkRow("https://astutu.corsica", "Astutu", t("astutu")),
    linkRow("https://liv.corsica", "LIV", t("liv")));
}

function renderAbout() {
  const rows = [[t("system"), systems[state.platform] || state.platform],
    [t("lexicon"), t("lexicon_count", { n: state.lexicon_entries.toLocaleString(numbers()) })]];
  if (state.firefox_profile) rows.push([t("profile"), state.firefox_profile]);
  const facts = rows.flatMap(([term, value]) => [make("dt", { text: term }), make("dd", { text: value })]);
  facts.push(make("dt", { text: t("source") }),
    make("dd", {}, make("a", { href: "https://github.com/Platykalt/corsu", target: "_blank", rel: "noopener noreferrer", text: "github.com/Platykalt/corsu" })));
  $("facts").replaceChildren(...facts);
  $("remove").disabled = !state.installed || state.job.running;
}

function renderActivity() {
  const job = state.job;
  const bar = $("activity");
  bar.hidden = !job.title;
  if (!job.title) return;
  const name = t("job_" + job.title);
  bar.classList.toggle("failed", job.ok === false);
  // A filling bar when the task reports its progress; the small spinner only for quick changes.
  const progress = job.progress;
  $("meter").hidden = !progress;
  $("busy").hidden = !job.running || Boolean(progress);
  if (progress) {
    const percent = job.running ? progress.percent : job.ok ? 100 : progress.percent;
    $("meter-fill").style.width = percent + "%";
    $("meter").setAttribute("aria-valuenow", percent);
  }
  $("step").textContent = job.running && progress ? progress.label : "";
  // The installer lock stopped the run: another window or installer is at work, nothing failed.
  $("activity-text").textContent = !job.running && job.busy ? t("busy") : t(job.running ? "running" : job.ok ? "done" : "failed", { job: name });
  if (job.ok === false) showLog = true;
  $("details-toggle").textContent = t(showLog ? "hide_details" : "show_details");
  const log = $("log");
  log.hidden = !showLog;
  const atEnd = log.scrollTop + log.clientHeight >= log.scrollHeight - 8;
  log.textContent = job.lines.join("\n");
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
  const response = await fetch("/api/review", { method: "POST", headers: { "X-Corsu": "1", "Content-Type": "application/json" },
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

function updateStatus() {
  const info = updateInfo();
  const current = info.current || state.version;
  if (info.checking) return { kind: "checking", text: t("update_checking") };
  // Installed but this window still runs the previous copy: that is what matters now.
  if (restartInfo().available && !restarting) return { kind: "available", text: t("update_restart_text", { version: restartInfo().version }) };
  if (info.status === "up_to_date") return { kind: "up_to_date", text: t("update_up_to_date") };
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
  const checked = info.checked ? new Date(info.checked * 1000).toLocaleString(numbers(), { dateStyle: "medium", timeStyle: "short" }) : "—";
  $("update-facts").replaceChildren(...[[t("update_current"), info.current || state.version], [t("update_latest"), info.latest || "—"], [t("update_checked"), checked]]
    .flatMap(([term, value]) => [make("dt", { text: term }), make("dd", { text: value })]));
  const status = updateStatus();
  $("update-status").className = "update-status " + status.kind;
  $("update-status").textContent = status.text;
  const result = updateResult();
  $("update-result").hidden = !result.lines.length;
  $("update-result").className = "update-result" + (result.kind ? " " + result.kind : "");
  $("update-result").replaceChildren(...result.lines.map(line => make("span", { text: line })));
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
  const show = !restarting && page !== "about" && (restart.available || autoRunning || (info.status === "available" && !(job.title === "update" && job.running)));
  $("update-banner").hidden = !show;
  if (show) $("update-text").textContent = restart.available ? t("update_restart_text", { version: restart.version })
    : autoRunning ? t("update_auto_started", { version: info.auto_started }) : t("update_available", { version: info.latest, current: info.current || state.version });
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
    const response = await fetch("/api/restart", { method: "POST", headers: { "X-Corsu": "1", "Content-Type": "application/json" }, body: JSON.stringify({ language }) });
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
  for (const node of document.querySelectorAll("[data-t]")) node.textContent = t(node.dataset.t);
  $("language").value = language;
  if (!state) return;
  $("version").textContent = state.version;
  // Shown as the server wrote it (French or English): it names the damaged file and what was kept.
  $("problem").textContent = state.problem || "";
  $("problem").hidden = !state.problem;
  renderPrograms(); renderAdd(); renderHelp(); renderAbout(); renderActivity(); renderExtras();
}

async function refresh() {
  try {
    const next = await call("/api/state");
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
    // While Corsu restarts, the address is silent for a moment.
    if (restarting && Date.now() < restarting.until) return;
    if (closed) return;
    closed = true;
    document.querySelector("main").replaceChildren(make("p", { class: "closed", text: t("closed") }));
    $("activity").hidden = true;
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
$("everything").addEventListener("click", () => call("/api/all", { on: state.everything_off }).then(refresh));
$("details-toggle").addEventListener("click", () => { showLog = !showLog; renderActivity(); });
$("review").addEventListener("click", async () => {
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

// Corsican first: the app speaks the language it puts on the computer.
language = language || "co";
render();
refresh();
setInterval(() => { if (!closed) refresh(); }, 1500);
