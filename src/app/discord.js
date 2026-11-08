"use strict";
// Discord's status row on the home page and the discord-recovery page (docs/dev/discord-watch.md), drawn from
// state.discord (src/app.py discord_status) at every render of the page. The buttons call /api/discord/* (the rescue
// API of src/discord_watch.py, run by the server) and the update check the About page already uses. Causes stay
// "probable" or "unknown", and an update is never said to fix Discord. app.js render() calls renderDiscord().
const renderDiscord = (() => {
  const $ = id => document.getElementById(id);
  const corsu = () => window.corsu;
  const t = (name, values) => corsu().t(name, values);
  const PROBLEM_ACTIONS = ["check", "rescue", "retry", "later"];
  // The buttons each state offers, in focus order. "rescue" is Corsu's rescue mode (rescue.json), not a watch state.
  const ACTIONS = { "vencord-error": PROBLEM_ACTIONS, "start-error": PROBLEM_ACTIONS, slow: PROBLEM_ACTIONS,
    network: ["retry", "later"], offscreen: ["later"], closed: ["retry"], rescue: ["reactivate", "check"],
    // Rescue mode's phases (rescue.json): the translation back but not yet proved by a start; a failed
    // reactivation waiting for Discord to close before its original archive goes back ("finish" = rescue again).
    "rescue-verifying": ["retry", "rescue"], "rescue-pending": ["finish"] };
  const BUTTONS = ["check", "install", "finish", "rescue", "reactivate", "retry", "later"];
  // The rescue API's buttons need src/discord_watch.py; without it they are not offered.
  const NEEDS_WATCH = ["finish", "rescue", "reactivate", "retry"];
  const ROWS = { active: ["active", "dc_chip_active"], restart: ["restart_required", "activation_restart_required"],
    rescue: ["blocked", "dc_chip_rescue", "warn"], problem: ["failed", "dc_chip_problem"] };

  const PHASES = { verifying: "rescue-verifying", "restore-pending": "rescue-pending" };
  const key = discord => discord.rescue ? PHASES[discord.rescue.phase] || "rescue" : discord.state || "none";
  const when = seconds => {
    const language = corsu().language();
    return new Date(seconds * 1000).toLocaleString(language === "co" ? "fr" : language, { dateStyle: "medium", timeStyle: "short" });
  };

  function actions(discord) {
    const offered = (ACTIONS[key(discord)] || []).filter(name => discord.watch_available || !NEEDS_WATCH.includes(name));
    return discord.dismissed ? offered.filter(name => name !== "later") : offered;
  }

  function renderRow(discord) {
    const row = discord && ROWS[discord.row];
    $("discord-status").hidden = !row;
    if (!row) return;
    const [activation, label, tone] = row;
    replaceWhenChanged($("discord-status-chip"), discord.row + corsu().language(), () => [chip(activation, {}, t(label), tone)]);
    setText($("discord-status-text"), t("dc_row_" + discord.row));
  }

  // The update line: Discord still on the old copy first, then the window's own update status (available,
  // up to date, check impossible, installed but Corsu to restart, development build).
  function updateLine(state, discord) {
    const update = state.update || {}, restart = update.restart || {};
    if (discord.old_corsu) return t("dc_update_processes_old", { version: restart.version || update.installed || state.version });
    const status = updateStatus();
    return update.status === "available" && !restart.available ? status.text + " " + t("dc_update_note") : status.text;
  }

  function resultLine(action) {
    if (!action) return "";
    if (action.running) return t("dc_busy_" + action.name);
    const result = action.result || {};
    if (result.ok) return t("dc_done_" + action.name);
    if (result.reason === "running") return t("dc_reason_running");
    if (result.reason === "unavailable") return t("dc_reason_unavailable");
    if (["unconfirmed", "rescue", "restore-pending"].includes(result.reason)) return t("dc_reason_" + result.reason.replace(/-/g, "_"));
    return t("dc_reason_other", { reason: result.error || result.reason || "?" });
  }

  function renderPage(state, discord) {
    const current = key(discord);
    const since = discord.rescue && discord.rescue.since ? when(discord.rescue.since) : "—";
    setText($("dr-message"), t("dc_state_" + current.replace(/-/g, "_"), { date: since }));
    setText($("dr-started"), discord.started_at ? t("dc_started", { date: when(discord.started_at) }) : "");
    const offered = actions(discord);
    const job = state.job || {}, busy = Boolean(job.running) || Boolean(discord.action && discord.action.running);
    const updateAvailable = (state.update || {}).status === "available" && !((state.update || {}).restart || {}).available;
    for (const name of BUTTONS) {
      const button = $("dr-" + name);
      button.hidden = name === "install" ? !(offered.includes("check") && updateAvailable) : !offered.includes(name);
      // Never over an open Discord: rescue and a new start wait until it is closed (the server checks again).
      button.disabled = busy || (NEEDS_WATCH.includes(name) && discord.running)
        || (name === "check" && Boolean((state.update || {}).checking));
    }
    $("dr-running").hidden = !(discord.running && offered.some(name => NEEDS_WATCH.includes(name)));
    $("dr-update").hidden = !offered.includes("check");
    if (offered.includes("check")) setText($("dr-update"), updateLine(state, discord));
    setText($("dr-result"), resultLine(discord.action));
    const vencord = discord.vencord || {};
    const facts = [["dc_diag_state", discord.state || "—"], ["dc_diag_launch", discord.launch || "—"],
      ["dc_diag_discord", discord.app_version || "—"], ["dc_diag_corsu", vencord.corsu_version || "—"],
      ["dc_diag_vencord", vencord.revision ? String(vencord.revision).slice(0, 12) : "—"]];
    const language = corsu().language();
    replaceWhenChanged($("dr-facts"), JSON.stringify(facts) + language, () => facts.flatMap(([term, value]) =>
      [make("dt", { text: t(term) }), make("dd", { text: value })]));
    const evidence = discord.evidence || [];
    replaceWhenChanged($("dr-evidence"), JSON.stringify(evidence) + language, () => evidence.length
      ? evidence.map(entry => make("li", {}, make("code", { text: entry.line }), entry.kind ? " (" + entry.kind + ")" : ""))
      : [make("li", { text: t("dc_diag_none") })]);
    $("dr-help").setAttribute("href", docs + (language === "en" ? "en/discord-start.md" : "fr/discord-demarrage.md"));
  }

  function render() {
    const state = corsu() && corsu().state();
    if (!state) return;
    const discord = state.discord;
    renderRow(discord);
    renderPage(state, discord || { row: null, state: null, evidence: [], watch_available: false });
  }

  async function act(name) {
    const state = corsu().state();
    const incident = state && state.discord ? state.discord.incident : null;
    if (name === "check") await corsu().call("/api/update/check", {}).catch(() => null);
    else if (name === "install") return startUpdate();
    else if (name === "later") {
      await corsu().call("/api/discord/dismiss", { incident }).catch(() => null);
      show("programs");
      $("main").focus();
    } else await corsu().call("/api/discord/" + (name === "finish" ? "rescue" : name), { incident }).catch(() => null);
    refresh();
  }

  for (const name of BUTTONS) $("dr-" + name).addEventListener("click", () => act(name));
  $("discord-status-open").addEventListener("click", () => {
    show("discord-recovery");
    $("dr-heading").focus();
  });
  return render;
})();
