"use strict";
// The « Report a translation » page: the person describes a wrong Corsican text (program and version, the text seen,
// where it appears, a proposal) and gets a report to read, copy, or open as a prefilled GitHub issue.
// Nothing here talks to Corsu's server and nothing is sent by itself: the issue opens in the browser only on a click,
// and GitHub then asks the person whether to submit it. Nothing is kept either (no storage): the form lives in this
// window. Personal folder paths and e-mail addresses are replaced before they reach the report.
(() => {
  const ISSUE = "https://github.com/Platykalt/corsu/issues/new";
  // Browsers and GitHub refuse very long addresses; past this the issue opens without the long fields.
  const MAX_URL = 7500;
  const SYSTEMS = { windows: "Windows", macos: "macOS", linux: "Linux" };
  const OTHER = "other", WINDOW = "corsu";
  // Field ids, in the order of the form and the report; the same ids as .github/ISSUE_TEMPLATE/translation.yml.
  const FIELDS = [
    { id: "seen", label: "rp_seen", hint: "rp_seen_hint", required: true, multiline: true },
    { id: "where", label: "rp_where", hint: "rp_where_hint", required: true },
    { id: "key", label: "rp_key", hint: "rp_key_hint" },
    { id: "proposal", label: "rp_proposal", lang: "co" },
    { id: "notes", label: "rp_notes", multiline: true },
  ];
  const draft = { app: "", appName: "", version: "", seen: "", where: "", key: "", proposal: "", notes: "" };
  let rendered = null, said = "";

  const corsu = () => window.corsu || {};
  function language() {
    const value = typeof corsu().language === "function" ? corsu().language() : null;
    return value && textsReport[value] ? value : "fr";
  }
  const t = (name, values = {}) => (textsReport[language()][name] ?? (corsu().t ? corsu().t(name) : name))
    .replace(/\{(\w+)\}/g, (_, key) => values[key]);
  const state = () => (typeof corsu().state === "function" ? corsu().state() : null) || {};

  // Folder paths that name the person's account, and e-mail addresses, never reach the report.
  const PRIVATE = [
    [/(?:\/var)?\/home\/[^/\s"'<>|]+/g, "~"], [/\/Users\/[^/\s"'<>|]+/g, "~"], [/\/root(?=\/|\b)/g, "~"],
    [/\b[A-Za-z]:\\+(?:Users|Documents and Settings)\\+[^\\\s"'<>|]+/gi, "~"],
    [/[\w.+-]+@[\w-]+(?:\.[\w-]+)+/g, "[…]"],
  ];
  function scrub(value) {
    let text = String(value || "").trim(), replaced = false;
    for (const [pattern, by] of PRIVATE) text = text.replace(pattern, () => { replaced = true; return by; });
    return { text, replaced };
  }

  function programs() {
    const lang = language();
    const items = (state().items || []).map(item => ({ value: item.name, label: ((item.text || {})[lang] || (item.text || {}).fr || [item.name])[0] }));
    return [{ value: WINDOW, label: t("rp_corsu_window") }, ...items, { value: OTHER, label: t("rp_app_other") }];
  }
  function programName() {
    if (draft.app === OTHER) return draft.appName.trim();
    const found = programs().find(option => option.value === draft.app);
    return found ? (draft.app === WINDOW ? "Corsu" : found.label) : "";
  }
  function context() {
    const info = state();
    return info.version ? t("rp_context", { version: info.version, system: SYSTEMS[info.platform] || info.platform || "?" }) : "";
  }

  // What the report and the issue carry, already scrubbed.
  function values() {
    let replaced = false;
    const clean = value => { const result = scrub(value); replaced = replaced || result.replaced; return result.text; };
    const found = { app: clean(programName()), version: clean(draft.version), corsu: context() };
    for (const field of FIELDS) found[field.id] = clean(draft[field.id]);
    return { found, replaced };
  }
  function missing(found) {
    const names = [];
    if (!found.app) names.push(t("rp_app"));
    for (const field of FIELDS) if (field.required && !found[field.id]) names.push(t(field.label));
    return names;
  }
  function reportText(found) {
    // French and Corsican put a space before the colon.
    const colon = language() === "en" ? ": " : " : ";
    const lines = [t("rp_title"), t("rp_app") + colon + [found.app || "—", found.version].filter(Boolean).join(" ")];
    for (const field of FIELDS) if (found[field.id]) lines.push(t(field.label) + colon + found[field.id].replace(/\s*\n\s*/g, " / "));
    if (found.corsu) lines.push(found.corsu);
    return lines.join("\n");
  }
  function issueUrl(found, short = false) {
    const title = `${found.app ? found.app + " : " : ""}${found.seen}`.slice(0, 90);
    const fields = { template: "translation.yml", title, app: found.app, version: found.version, where: found.where,
      key: found.key, corsu: found.corsu };
    if (!short) Object.assign(fields, { seen: found.seen, proposal: found.proposal, notes: found.notes });
    const query = new URLSearchParams(Object.entries(fields).filter(([, value]) => value));
    return ISSUE + "?" + query.toString();
  }

  function el(id) { return document.getElementById(id); }
  // Refreshes what depends on the fields, without rebuilding the form (the focus and the caret stay where they are).
  function update() {
    const { found, replaced } = values();
    const area = el("rp-text");
    if (!area) return;
    area.value = reportText(found);
    const lacking = missing(found);
    el("rp-issue").disabled = lacking.length > 0;
    el("rp-copy").disabled = lacking.length > 0;
    el("rp-missing").textContent = lacking.length ? t("rp_missing", { fields: lacking.join(", ") }) : "";
    el("rp-replaced").hidden = !replaced;
    el("rp-app-name-row").hidden = draft.app !== OTHER;
    el("rp-said").textContent = said;
  }
  function say(text) { said = text; update(); }

  async function copy() {
    const area = el("rp-text");
    try {
      await navigator.clipboard.writeText(area.value);
      say(t("rp_copied"));
    } catch (error) {
      area.focus(); area.select();
      say(t("rp_copy_failed"));
    }
  }
  async function openIssue() {
    const { found } = values();
    if (missing(found).length) return;
    let url = issueUrl(found);
    if (url.length > MAX_URL) {
      url = issueUrl(found, true);
      try { await navigator.clipboard.writeText(el("rp-text").value); } catch (error) {}
      say(t("rp_too_long"));
    }
    window.open(url, "_blank", "noopener");
  }

  function field(spec) {
    const { make } = corsu();
    const id = "rp-" + spec.id, hint = spec.hint ? id + "-hint" : null;
    const control = make(spec.multiline ? "textarea" : "input", { id, name: spec.id, type: spec.multiline ? null : "text",
      rows: spec.multiline ? "2" : null, spellcheck: "false", autocomplete: "off", required: Boolean(spec.required),
      "aria-required": spec.required ? "true" : null, "aria-describedby": hint, lang: spec.lang || null,
      oninput: event => { draft[spec.id] = event.target.value; said = ""; update(); } });
    control.value = draft[spec.id];
    if (spec.multiline) control.textContent = draft[spec.id];
    return make("div", { class: "rp-field" },
      make("label", { for: id }, make("span", { text: t(spec.label) }),
        make("span", { class: "rp-flag", text: t(spec.required ? "rp_required" : "rp_optional") })),
      control, hint ? make("p", { class: "rp-hint", id: hint, text: t(spec.hint) }) : null);
  }

  function render() {
    const { make, icon } = corsu();
    const body = el("report-body");
    if (!body || !make || !icon) return;
    if (!draft.app) draft.app = WINDOW;
    const select = make("select", { id: "rp-app", name: "app", onchange: event => { draft.app = event.target.value; said = ""; update();
      if (draft.app === OTHER) el("rp-app-name").focus(); } },
      ...programs().map(option => make("option", { value: option.value, selected: option.value === draft.app, text: option.label })));
    const appName = make("input", { id: "rp-app-name", name: "app-name", type: "text", autocomplete: "off",
      "aria-required": "true", oninput: event => { draft.appName = event.target.value; update(); } });
    appName.value = draft.appName;
    const version = make("input", { id: "rp-version", name: "version", type: "text", autocomplete: "off", "aria-describedby": "rp-version-hint",
      oninput: event => { draft.version = event.target.value; update(); } });
    version.value = draft.version;
    rendered = language() + (state().items || []).map(item => item.name).join();
    body.replaceChildren(
      make("p", { class: "muted section-text rp-privacy", id: "rp-privacy" }, t("rp_privacy")),
      make("form", { class: "group panel rp-form", "aria-describedby": "rp-privacy", novalidate: true, onsubmit: event => event.preventDefault() },
        make("div", { class: "rp-row" },
          make("div", { class: "rp-field" },
            make("label", { for: "rp-app" }, make("span", { text: t("rp_app") }), make("span", { class: "rp-flag", text: t("rp_required") })), select),
          make("div", { class: "rp-field", id: "rp-app-name-row" },
            make("label", { for: "rp-app-name" }, make("span", { text: t("rp_app_name") }), make("span", { class: "rp-flag", text: t("rp_required") })), appName),
          make("div", { class: "rp-field" },
            make("label", { for: "rp-version" }, make("span", { text: t("rp_version") }), make("span", { class: "rp-flag", text: t("rp_optional") })), version,
            make("p", { class: "rp-hint", id: "rp-version-hint", text: t("rp_version_hint") }))),
        ...FIELDS.map(field)),
      make("h2", { id: "rp-preview-title", text: t("rp_preview") }),
      make("div", { class: "group panel" },
        make("p", { class: "muted", id: "rp-preview-hint", text: t("rp_preview_hint") }),
        make("textarea", { id: "rp-text", class: "rp-text", readonly: true, rows: "7", spellcheck: "false",
          "aria-labelledby": "rp-preview-title", "aria-describedby": "rp-preview-hint" }),
        make("p", { class: "rp-note", id: "rp-replaced", hidden: true }, icon("about"), make("span", { text: t("rp_replaced") })),
        make("p", { class: "rp-missing", id: "rp-missing", "aria-live": "polite" }),
        make("div", { class: "buttons" },
          make("button", { type: "button", class: "button default", id: "rp-copy", onclick: copy }, make("span", { text: t("rp_copy") })),
          make("button", { type: "button", class: "button", id: "rp-issue", "aria-describedby": "rp-issue-hint", onclick: openIssue },
            icon("external"), make("span", { text: t("rp_issue") }), make("span", { class: "sr-only", text: " " + t("opens_browser") })),
          make("button", { type: "button", class: "button quiet", id: "rp-clear", onclick: () => {
            for (const name of Object.keys(draft)) draft[name] = "";
            said = ""; render(); el("rp-seen").focus();
          } }, make("span", { text: t("rp_clear") }))),
        make("p", { class: "muted rp-hint", id: "rp-issue-hint", text: t("rp_issue_hint") }),
        make("p", { class: "muted", id: "rp-said", role: "status" })));
    update();
  }

  // The window redraws itself every 1.5 s (corsu:render): the form is rebuilt only when the language or the list of
  // programs changed, so typing is never interrupted.
  const key = () => language() + (state().items || []).map(item => item.name).join();
  document.addEventListener("corsu:render", () => { if (rendered !== key()) render(); else update(); });
  document.addEventListener("corsu:page", event => { if (event.detail === "report" && rendered !== key()) render(); });
  window.corsuReport = { render, scrub, issueUrl, reportText, values, draft, fields: FIELDS };
})();
