"use strict";
// The Appearance page and the appearance of the whole window (docs/window-design.md, "Appearance contract").
// The server keeps the settings (DATA/appearance/settings.json, through src/appearance.py); localStorage only caches
// them so the first paint already has the right theme, since the window's address (and so its storage) can change.
(() => {
  const root = document.documentElement;
  const CACHE = "corsu-appearance";
  const LIMITS = { file: 40 * 1024 * 1024, side: 16384, pixels: 80e6, target: 2560, upload: 8 * 1024 * 1024 };
  const ACCEPT = ["image/png", "image/jpeg", "image/webp", "image/gif", "image/avif"];
  const THEMES = ["light", "dark", "system"];
  const PALETTES = ["maquis", "mare", "granitu", "tramontu", "notte"];
  const DENSITIES = ["comfortable", "compact"];
  // Accent suggestions; whatever is chosen is adjusted against the current surfaces before use.
  const PRESETS = [["green", "#2f6f62"], ["blue", "#2f5f9e"], ["ochre", "#a5652a"], ["terracotta", "#b4543a"],
    ["violet", "#6a4c93"], ["wine", "#8a3b5c"], ["olive", "#55702f"]];
  const DEFAULTS = { format: 1, theme: "system", palette: "maquis", accent: null, density: "comfortable",
    background: "none", image: null, dim: 0.55, blur: 0 };
  const AA = 4.5;

  let settings = { ...DEFAULTS };
  let imageUrl = null, imageVersion = null;   // the stored picture, fetched with the X-Corsu header
  let draft = null;                           // a picture being framed: {blob, url, width, height, x, y}
  let saveTimer = null, unsaved = false, confirmReset = false, busy = false;
  let adjusted = null;                        // {chosen, used} after the contrast check
  let refs = null;
  const message = { text: "", kind: "status" };

  // Texts and helpers ------------------------------------------------------------------------------------------------
  const corsu = () => window.corsu || {};
  function language() {
    const value = typeof corsu().language === "function" ? corsu().language() : corsu().language;
    if (value && textsAppearance[value]) return value;
    try { const saved = localStorage.getItem("corsu-language"); if (saved && textsAppearance[saved]) return saved; } catch (error) {}
    return "fr";
  }
  const t = (name, values = {}) => (textsAppearance[language()][name] ?? textsAppearance.fr[name] ?? name)
    .replace(/\{(\w+)\}/g, (_, key) => values[key]);
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
  const media = query => window.matchMedia ? window.matchMedia(query) : { matches: false, addEventListener() {} };
  const darkScheme = media("(prefers-color-scheme: dark)");
  const lessTransparency = media("(prefers-reduced-transparency: reduce)");

  async function request(path, options = {}) {
    const response = await fetch(path, { ...options, headers: { "X-Corsu": "1", ...(options.headers || {}) } });
    let body = null;
    try { body = await response.json(); } catch (error) {}
    if (!response.ok) {
      const failure = new Error((body && body.error) || String(response.status));
      failure.code = (body && body.error) || "status_" + response.status;
      throw failure;
    }
    return body;
  }

  function normalise(value) {
    const result = { ...DEFAULTS };
    if (!value || typeof value !== "object") return result;
    if (THEMES.includes(value.theme)) result.theme = value.theme;
    if (PALETTES.includes(value.palette)) result.palette = value.palette;
    if (DENSITIES.includes(value.density)) result.density = value.density;
    if (typeof value.accent === "string" && /^#[0-9a-f]{6}$/i.test(value.accent)) result.accent = value.accent.toLowerCase();
    if (Number.isFinite(value.dim)) result.dim = Math.min(0.85, Math.max(0, value.dim));
    if (Number.isFinite(value.blur)) result.blur = Math.min(24, Math.max(0, Math.round(value.blur)));
    if (value.image && typeof value.image === "object" && value.image.version) result.image = { ...value.image };
    result.background = value.background === "image" && result.image ? "image" : "none";
    return result;
  }

  // Colour and contrast ----------------------------------------------------------------------------------------------
  let probe = null;
  // Any CSS colour as [r, g, b], read back from a pixel: what the engine really paints, whatever the notation.
  function rgb(colour) {
    if (!probe) {
      const canvas = document.createElement("canvas");
      canvas.width = canvas.height = 1;
      probe = canvas.getContext("2d", { willReadFrequently: true });
    }
    probe.clearRect(0, 0, 1, 1);
    probe.fillStyle = "#000";
    probe.fillStyle = colour;
    probe.fillRect(0, 0, 1, 1);
    const [r, g, b] = probe.getImageData(0, 0, 1, 1).data;
    return [r, g, b];
  }
  function luminance([r, g, b]) {
    const channel = value => { value /= 255; return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
  }
  function contrast(first, second) {
    const [high, low] = [luminance(first), luminance(second)].sort((a, b) => b - a);
    return (high + 0.05) / (low + 0.05);
  }
  function toHsl([r, g, b]) {
    r /= 255; g /= 255; b /= 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b), l = (max + min) / 2, d = max - min;
    if (!d) return [0, 0, l];
    const s = d / (1 - Math.abs(2 * l - 1));
    const h = max === r ? ((g - b) / d) % 6 : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
    return [(h * 60 + 360) % 360, s, l];
  }
  function fromHsl([h, s, l]) {
    const c = (1 - Math.abs(2 * l - 1)) * s, x = c * (1 - Math.abs((h / 60) % 2 - 1)), m = l - c / 2;
    const [r, g, b] = h < 60 ? [c, x, 0] : h < 120 ? [x, c, 0] : h < 180 ? [0, c, x] : h < 240 ? [0, x, c] : h < 300 ? [x, 0, c] : [c, 0, x];
    return [r, g, b].map(value => Math.round((value + m) * 255));
  }
  const hex = colour => "#" + colour.map(value => value.toString(16).padStart(2, "0")).join("");
  function token(name, fallback) {
    const value = getComputedStyle(root).getPropertyValue(name).trim();
    return value ? rgb(value) : fallback;
  }
  // The chosen accent, its lightness moved as little as possible so that text on it (--on-accent) and it on the
  // panels (--surface) both reach the WCAG AA ratio for text (4.5:1). Null when no lightness can (never seen).
  function adjustAccent(chosen) {
    const dark = root.dataset.theme === "dark";
    const surface = token("--surface", null) || token("--bg", dark ? [32, 34, 36] : [255, 255, 255]);
    const onAccent = token("--on-accent", dark ? [16, 20, 24] : [255, 255, 255]);
    const passes = colour => contrast(colour, onAccent) >= AA && contrast(colour, surface) >= AA;
    const original = rgb(chosen);
    if (passes(original)) return hex(original);
    const [h, s, l] = toHsl(original);
    for (let step = 0.005; step <= 1; step += 0.005) {
      for (const lightness of [l - step, l + step]) {
        if (lightness < 0 || lightness > 1) continue;
        const candidate = fromHsl([h, s, lightness]);
        if (passes(candidate)) return hex(candidate);
      }
    }
    return null;
  }

  // Applying ---------------------------------------------------------------------------------------------------------
  const blurAvailable = () => !lessTransparency.matches && window.CSS && CSS.supports &&
    (CSS.supports("backdrop-filter", "blur(2px)") || CSS.supports("-webkit-backdrop-filter", "blur(2px)"));

  function apply() {
    root.dataset.theme = settings.theme === "system" ? (darkScheme.matches ? "dark" : "light") : settings.theme;
    root.dataset.palette = settings.palette;
    root.dataset.density = settings.density;
    adjusted = null;
    root.style.removeProperty("--accent-user");
    if (settings.accent) {
      const used = adjustAccent(settings.accent);
      if (used) {
        root.style.setProperty("--accent-user", used);
        adjusted = { chosen: settings.accent, used };
      }
    }
    const picture = draft ? draft.url : settings.background === "image" && imageUrl ? imageUrl : null;
    const focus = draft || settings.image || { x: 50, y: 50 };
    root.dataset.background = picture ? "image" : "none";
    if (picture) {
      root.style.setProperty("--bg-image", `url("${picture}")`);
      root.style.setProperty("--bg-position", `${focus.x}% ${focus.y}%`);
    } else {
      root.style.removeProperty("--bg-image");
      root.style.removeProperty("--bg-position");
    }
    root.style.setProperty("--bg-dim", String(settings.dim));
    root.style.setProperty("--bg-blur", (blurAvailable() ? settings.blur : 0) + "px");
    if (blurAvailable()) root.removeAttribute("data-reduced-transparency");
    else root.setAttribute("data-reduced-transparency", "");
  }

  function cache() {
    try { localStorage.setItem(CACHE, JSON.stringify({ ...settings, image: null, background: "none" })); } catch (error) {}
  }

  function changed(values) {
    Object.assign(settings, values);
    apply();
    cache();
    sync();
    unsaved = true;
    clearTimeout(saveTimer);
    saveTimer = setTimeout(save, 400);
  }

  function changes() {
    const body = { theme: settings.theme, palette: settings.palette, accent: settings.accent, density: settings.density,
      background: settings.background, dim: settings.dim, blur: settings.blur };
    if (settings.image) body.image = { x: settings.image.x, y: settings.image.y };
    return JSON.stringify(body);
  }

  async function save() {
    clearTimeout(saveTimer);
    if (!unsaved) return;
    unsaved = false;
    try {
      const answer = await request("/api/appearance", { method: "POST", headers: { "Content-Type": "application/json" }, body: changes() });
      if (message.text === t("ap_err_save")) say("");
    } catch (error) {
      unsaved = true;
      say(t("ap_err_save"), "alert");
    }
  }

  // The stored picture is fetched with the X-Corsu header (so allowed() applies to it too) and shown as a blob: URL.
  async function loadImage() {
    const version = settings.image && settings.image.version;
    if (!version || version === imageVersion) return;
    try {
      const response = await fetch("/appearance/background?v=" + version, { headers: { "X-Corsu": "1" } });
      if (!response.ok) throw new Error(String(response.status));
      const blob = await response.blob();
      await createImageBitmap(blob).then(bitmap => bitmap.close && bitmap.close());
      if (imageUrl) URL.revokeObjectURL(imageUrl);
      imageUrl = URL.createObjectURL(blob);
      imageVersion = version;
    } catch (error) {
      if (imageUrl) URL.revokeObjectURL(imageUrl);
      imageUrl = imageVersion = null;
      settings.background = "none";
      settings.image = null;
      say(t("ap_err_missing"), "alert");
    }
    apply();
    sync();
  }

  async function load() {
    try {
      const answer = await request("/appearance/settings");
      settings = normalise(answer);
      if (answer && answer.image_problem) say(t("ap_err_missing"), "alert");
    } catch (error) {
      say(t("ap_err_load"), "alert");
    }
    apply();
    cache();
    sync();
    await loadImage();
  }

  // The picture: read, checked and scaled down here; only the result is sent ---------------------------------------
  // Width and height from the file's header, before anything is decoded (PNG, GIF, JPEG, WebP, AVIF); null if unknown.
  function headerSize(bytes) {
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const text = (start, length) => String.fromCharCode(...bytes.subarray(start, start + length));
    try {
      if (bytes[0] === 0x89 && text(1, 3) === "PNG") return [view.getUint32(16), view.getUint32(20)];
      if (text(0, 3) === "GIF") return [view.getUint16(6, true), view.getUint16(8, true)];
      if (text(0, 4) === "RIFF" && text(8, 4) === "WEBP") {
        const kind = text(12, 4);
        if (kind === "VP8X") return [1 + (view.getUint32(24, true) & 0xffffff), 1 + (view.getUint32(27, true) & 0xffffff)];
        if (kind === "VP8L") { const bits = view.getUint32(21, true); return [(bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1]; }
        if (kind === "VP8 ") return [view.getUint16(26, true) & 0x3fff, view.getUint16(28, true) & 0x3fff];
      }
      if (bytes[0] === 0xff && bytes[1] === 0xd8) {
        let position = 2;
        while (position + 9 < bytes.length) {
          if (bytes[position] !== 0xff) { position++; continue; }
          const marker = bytes[position + 1];
          if (marker === 0xff) { position++; continue; }
          if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker))
            return [view.getUint16(position + 7), view.getUint16(position + 5)];
          if (marker === 0xd8 || marker === 0x01 || (marker >= 0xd0 && marker <= 0xd7)) { position += 2; continue; }
          position += 2 + view.getUint16(position + 2);
        }
      }
      for (let position = 4; position + 16 <= bytes.length; position++) {   // AVIF/HEIF: the 'ispe' property
        if (bytes[position] === 0x69 && text(position, 4) === "ispe") return [view.getUint32(position + 8), view.getUint32(position + 12)];
      }
    } catch (error) {}
    return null;
  }

  class Refused extends Error {}
  const tooLarge = (width, height) => width > LIMITS.side || height > LIMITS.side || width * height > LIMITS.pixels;
  const encode = (canvas, type, quality) => new Promise(resolve => canvas.toBlob(resolve, type, quality));

  async function prepare(file) {
    if (file.type && !ACCEPT.includes(file.type)) throw new Refused(t("ap_err_type"));
    if (file.size > LIMITS.file) throw new Refused(t("ap_err_file_size", { size: (file.size / 1048576).toLocaleString(language() === "en" ? "en" : "fr", { maximumFractionDigits: 1 }) }));
    const head = new Uint8Array(await file.slice(0, 512 * 1024).arrayBuffer());
    const declared = headerSize(head);
    if (declared && tooLarge(...declared)) throw new Refused(t("ap_err_dimensions", { width: declared[0], height: declared[1] }));
    let bitmap;
    try { bitmap = await createImageBitmap(file); }   // the first frame of an animated picture
    catch (error) { throw new Refused(t("ap_err_decode")); }
    try {
      const { width, height } = bitmap;
      if (!width || !height) throw new Refused(t("ap_err_decode"));
      if (tooLarge(width, height)) throw new Refused(t("ap_err_dimensions", { width, height }));
      const scale = Math.min(1, LIMITS.target / Math.max(width, height));
      const target = [Math.max(1, Math.round(width * scale)), Math.max(1, Math.round(height * scale))];
      // Halve first, then the last step: smoother than one large reduction.
      let source = bitmap, size = [width, height];
      while (size[0] / 2 >= target[0] && size[1] / 2 >= target[1]) {
        const half = document.createElement("canvas");
        half.width = Math.round(size[0] / 2); half.height = Math.round(size[1] / 2);
        const context = half.getContext("2d");
        context.imageSmoothingQuality = "high";
        context.drawImage(source, 0, 0, half.width, half.height);
        source = half; size = [half.width, half.height];
      }
      const canvas = document.createElement("canvas");
      [canvas.width, canvas.height] = target;
      const context = canvas.getContext("2d");
      context.imageSmoothingQuality = "high";
      context.drawImage(source, 0, 0, ...target);
      let blob = await encode(canvas, "image/webp", 0.86);
      if (!blob || blob.type !== "image/webp") {
        // JPEG has no transparency: transparent parts become white rather than black.
        const flat = document.createElement("canvas");
        [flat.width, flat.height] = target;
        const flatContext = flat.getContext("2d");
        flatContext.fillStyle = "#fff";
        flatContext.fillRect(0, 0, ...target);
        flatContext.drawImage(canvas, 0, 0);
        blob = await encode(flat, "image/jpeg", 0.86);
        if (blob && blob.size > LIMITS.upload) blob = await encode(flat, "image/jpeg", 0.7);
      } else if (blob.size > LIMITS.upload) {
        blob = await encode(canvas, "image/webp", 0.7);
      }
      if (!blob || blob.size > LIMITS.upload) throw new Refused(t("ap_err_encode"));
      return { blob, url: URL.createObjectURL(blob), width: target[0], height: target[1], x: 50, y: 50 };
    } finally {
      if (bitmap.close) bitmap.close();
    }
  }

  async function chosen(event) {
    const file = event.target.files && event.target.files[0];
    event.target.value = "";
    if (!file) return;
    discardDraft();
    busy = true;
    say(t("ap_preparing"));
    try {
      draft = await prepare(file);
      say("");
    } catch (error) {
      say(error instanceof Refused ? error.message : t("ap_err_decode"), "alert");
    }
    busy = false;
    apply();
    sync();
    if (draft && refs) refs.frame.focus();
  }

  function discardDraft() {
    if (draft) URL.revokeObjectURL(draft.url);
    draft = null;
  }

  async function applyDraft() {
    if (!draft || busy) return;
    busy = true;
    say(t("ap_saving_image"));
    sync();
    try {
      const answer = await request(`/api/appearance/background?x=${draft.x}&y=${draft.y}`,
        { method: "POST", headers: { "Content-Type": draft.blob.type }, body: draft.blob });
      const kept = normalise(answer);
      settings = { ...kept, theme: settings.theme, palette: settings.palette, accent: settings.accent,
        density: settings.density, dim: settings.dim, blur: settings.blur };
      if (imageUrl) URL.revokeObjectURL(imageUrl);
      imageUrl = draft.url;   // the very bytes the server checked and kept
      imageVersion = kept.image && kept.image.version;
      draft = null;
      say(t("ap_image_saved"));
      cache();
    } catch (error) {
      say(t("ap_err_upload", { reason: reason(error.code) }), "alert");
    }
    busy = false;
    apply();
    sync();
    if (refs) refs.choose.focus();
  }

  function reason(code) {
    const known = ["too_large", "not_image", "damaged", "dimensions"];
    return t(known.includes(code) ? "ap_reason_" + code : "ap_reason_other");
  }

  function cancelDraft() {
    discardDraft();
    say(t("ap_image_cancelled"));
    apply();
    sync();
    if (refs) refs.choose.focus();
  }

  async function removeImage() {
    try {
      settings = { ...settings, ...pick(normalise(await request("/api/appearance/background/remove", { method: "POST" })), ["image", "background"]) };
      if (imageUrl) URL.revokeObjectURL(imageUrl);
      imageUrl = imageVersion = null;
      say(t("ap_image_removed"));
    } catch (error) {
      say(t("ap_err_save"), "alert");
    }
    apply();
    sync();
    if (refs) refs.choose.focus();
  }
  const pick = (object, names) => Object.fromEntries(names.map(name => [name, object[name]]));

  async function reset() {
    try {
      settings = normalise(await request("/api/appearance/reset", { method: "POST" }));
      unsaved = false;
      clearTimeout(saveTimer);
      discardDraft();
      if (imageUrl) URL.revokeObjectURL(imageUrl);
      imageUrl = imageVersion = null;
      try { localStorage.removeItem(CACHE); } catch (error) {}
      say(t("ap_reset_done"));
    } catch (error) {
      say(t("ap_err_save"), "alert");
    }
    confirmReset = false;
    apply();
    sync();
    if (refs) refs.reset.focus();
  }

  function say(text, kind = "status") {
    message.text = text;
    message.kind = kind;
    if (!refs) return;
    refs.status.textContent = kind === "status" ? text : "";
    refs.alert.textContent = kind === "alert" ? text : "";
  }

  // The page ---------------------------------------------------------------------------------------------------------
  function choice(name, value, label, checked, onChange, extra = null) {
    const id = `ap-${name}-${value}`;
    return make("label", { class: "ap-choice", for: id },
      make("input", { type: "radio", name: "ap-" + name, id, value, checked, onchange: onChange }),
      extra, make("span", { text: label }));
  }

  function row(label, detail, control, attributes = {}) {
    return make("li", { class: "ap-row", ...attributes },
      make("span", { class: "label" }, label, detail ? make("span", { class: "detail", text: detail }) : null), control);
  }

  function setFocus(x, y) {
    if (!draft) return;
    draft.x = Math.round(Math.min(100, Math.max(0, x)));
    draft.y = Math.round(Math.min(100, Math.max(0, y)));
    apply();
    syncFrame();
  }

  function render() {
    const section = document.getElementById("appearance");
    if (!section) return;
    const focused = document.activeElement && section.contains(document.activeElement) ? document.activeElement.id : null;
    section.replaceChildren();
    refs = {};
    renderedLanguage = language();
    const group = (...items) => make("ul", { class: "group" }, ...items);
    const heading = (key, id) => make("h2", { id, text: t(key) });
    const segmented = (name, values, current, labelKey) => make("div", { class: "segmented", role: "radiogroup", "aria-labelledby": `ap-${name}-label` },
      ...values.map(value => choice(name, value, t(labelKey(value)), current === value, () => changed({ [name]: value }))));

    // Theme and density
    section.append(make("h1", { text: t("ap_title") }), make("p", { class: "lead", text: t("ap_lead") }));
    section.append(group(
      row(make("span", { id: "ap-theme-label", text: t("ap_theme") }), t("ap_theme_detail"),
        refs.theme = segmented("theme", THEMES, settings.theme, value => "ap_theme_" + value)),
      row(make("span", { id: "ap-density-label", text: t("ap_density") }), t("ap_density_detail"),
        refs.density = segmented("density", DENSITIES, settings.density, value => "ap_density_" + value))));

    // Palette
    refs.palette = make("div", { class: "swatches ap-palettes", role: "radiogroup", "aria-labelledby": "ap-palette-label" },
      ...PALETTES.map(value => choice("palette", value, t("ap_palette_" + value), settings.palette === value,
        () => changed({ palette: value }), make("span", { class: "ap-chip", "data-chip": value, "aria-hidden": "true" }))));
    section.append(heading("ap_palette", "ap-palette-label"), make("div", { class: "group ap-block" }, refs.palette));

    // Accent
    refs.custom = make("input", { type: "color", id: "ap-accent-custom", value: settings.accent || "#2f6f62",
      "aria-label": t("ap_accent_custom"), oninput: event => changed({ accent: event.target.value.toLowerCase() }) });
    refs.accent = make("div", { class: "swatches ap-accents", role: "radiogroup", "aria-labelledby": "ap-accent-label" },
      choice("accent", "default", t("ap_accent_default"), !settings.accent, () => changed({ accent: null }),
        make("span", { class: "ap-chip ap-chip-default", "aria-hidden": "true" })),
      ...PRESETS.map(([name, colour]) => {
        const node = choice("accent", name, t("ap_accent_" + name), settings.accent === colour, () => changed({ accent: colour }),
          make("span", { class: "ap-chip", style: `background:${colour}`, "aria-hidden": "true" }));
        node.title = t("ap_accent_" + name);
        node.querySelector("span:last-child").className = "ap-sr";
        return node;
      }),
      make("label", { class: "ap-choice ap-custom", for: "ap-accent-custom" }, refs.custom,
        make("span", { text: t("ap_accent_custom") })));
    refs.accentNote = make("p", { class: "ap-note", id: "ap-accent-note", "aria-live": "polite" });
    section.append(heading("ap_accent", "ap-accent-label"), make("div", { class: "group ap-block" },
      make("p", { class: "detail ap-detail", text: t("ap_accent_detail") }), refs.accent, refs.accentNote,
      make("p", { class: "detail ap-detail", text: t("ap_accent_status") })));

    // Background
    refs.file = make("input", { type: "file", id: "ap-file", class: "ap-sr", tabindex: "-1", "aria-hidden": "true",
      accept: ACCEPT.join(","), onchange: chosen });
    refs.backgroundChoice = segmented("background", ["none", "image"], settings.background, value => value === "none" ? "ap_bg_none" : "ap_bg_image");
    refs.backgroundChoice.setAttribute("aria-labelledby", "ap-bg-kind-label");
    refs.backgroundChoice.querySelector("#ap-background-image").addEventListener("click", event => {
      if (!settings.image && !draft) { event.preventDefault(); refs.file.click(); }
    });
    refs.thumb = make("img", { class: "ap-thumb", alt: t("ap_current_image"), hidden: true });
    refs.imageInfo = make("span", { class: "detail" });
    refs.choose = make("button", { type: "button", class: "button", id: "ap-choose", onclick: () => refs.file.click() });
    refs.remove = make("button", { type: "button", class: "button", id: "ap-remove", text: t("ap_bg_remove"), onclick: removeImage });

    refs.marker = make("span", { class: "ap-marker", "aria-hidden": "true" });
    refs.frameImage = make("img", { class: "ap-frame-image", alt: "", draggable: "false" });
    refs.frame = make("div", { class: "ap-frame", id: "ap-frame", tabindex: "0", role: "group",
      "aria-label": t("ap_frame_area"), "aria-describedby": "ap-frame-help ap-frame-value" }, refs.frameImage, refs.marker);
    refs.frameValue = make("span", { class: "ap-sr", id: "ap-frame-value", "aria-live": "polite" });
    const drag = event => {
      const box = refs.frameImage.getBoundingClientRect();
      if (!box.width || !box.height) return;
      setFocus((event.clientX - box.left) / box.width * 100, (event.clientY - box.top) / box.height * 100);
    };
    refs.frame.addEventListener("pointerdown", event => { refs.frame.setPointerCapture(event.pointerId); drag(event); refs.frame.focus(); });
    refs.frame.addEventListener("pointermove", event => { if (refs.frame.hasPointerCapture(event.pointerId)) drag(event); });
    refs.frame.addEventListener("keydown", event => {
      const step = event.shiftKey ? 10 : 1;
      const moves = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
      if (event.key === "Home") { event.preventDefault(); return setFocus(50, 50); }
      if (event.key === "Enter") { event.preventDefault(); return applyDraft(); }
      if (event.key === "Escape") { event.preventDefault(); return cancelDraft(); }
      if (!moves[event.key] || !draft) return;
      event.preventDefault();
      setFocus(draft.x + moves[event.key][0], draft.y + moves[event.key][1]);
    });
    const axis = name => make("input", { type: "range", class: "range", id: "ap-frame-" + name, min: "0", max: "100", step: "1",
      oninput: event => setFocus(name === "x" ? +event.target.value : draft.x, name === "y" ? +event.target.value : draft.y) });
    refs.frameX = axis("x");
    refs.frameY = axis("y");
    refs.apply = make("button", { type: "button", class: "button default", id: "ap-apply", text: t("ap_apply"), onclick: applyDraft });
    refs.framing = make("div", { class: "ap-framing", id: "ap-framing", role: "region", "aria-labelledby": "ap-frame-title", hidden: true },
      make("h3", { id: "ap-frame-title", text: t("ap_frame_title") }),
      make("p", { class: "detail", id: "ap-frame-help", text: t("ap_frame_help") }),
      refs.frame, refs.frameValue,
      make("div", { class: "ap-axes" },
        make("label", { for: "ap-frame-x" }, make("span", { text: t("ap_frame_x") }), refs.frameX),
        make("label", { for: "ap-frame-y" }, make("span", { text: t("ap_frame_y") }), refs.frameY)),
      make("div", { class: "buttons" }, refs.apply,
        make("button", { type: "button", class: "button", id: "ap-cancel", text: t("ap_cancel"), onclick: cancelDraft })));

    refs.dim = make("input", { type: "range", class: "range", id: "ap-dim", min: "0", max: "85", step: "5",
      oninput: event => changed({ dim: +event.target.value / 100 }) });
    refs.dimValue = make("output", { for: "ap-dim", class: "ap-value" });
    refs.blurSwitch = make("input", { type: "checkbox", role: "switch", id: "ap-blur",
      onchange: event => changed({ blur: event.target.checked ? (settings.blur || 12) : 0 }) });
    refs.blur = make("input", { type: "range", class: "range", id: "ap-blur-amount", min: "2", max: "24", step: "2",
      "aria-label": t("ap_blur_amount"), oninput: event => changed({ blur: +event.target.value }) });
    refs.blurValue = make("output", { for: "ap-blur-amount", class: "ap-value" });
    refs.blurDetail = make("span", { class: "detail" });
    refs.imageRows = [
      row(make("label", { for: "ap-dim", text: t("ap_dim") }), t("ap_dim_detail"), make("span", { class: "ap-range" }, refs.dim, refs.dimValue)),
      make("li", { class: "ap-row" }, make("span", { class: "label" }, make("label", { for: "ap-blur", text: t("ap_blur") }), refs.blurDetail),
        make("span", { class: "ap-range" }, refs.blur, refs.blurValue),
        make("span", { class: "switch" }, refs.blurSwitch, make("i"))),
    ];
    section.append(heading("ap_background", "ap-background-label"), group(
      row(make("span", { id: "ap-bg-kind-label", text: t("ap_bg_kind") }), null, refs.backgroundChoice),
      make("li", { class: "ap-row ap-image-row" }, refs.thumb,
        make("span", { class: "label" }, refs.imageInfo, make("span", { class: "detail", text: t("ap_bg_formats") })),
        make("span", { class: "ap-buttons" }, refs.choose, refs.remove), refs.file),
      ...refs.imageRows), refs.framing);

    // Messages and reset
    refs.status = make("p", { class: "ap-message", id: "ap-status", role: "status" });
    refs.alert = make("p", { class: "ap-message ap-alert", id: "ap-alert", role: "alert" });
    refs.reset = make("button", { type: "button", class: "button", id: "ap-reset", text: t("ap_reset"),
      onclick: () => { confirmReset = true; sync(); refs.resetYes.focus(); } });
    refs.resetYes = make("button", { type: "button", class: "button danger", id: "ap-reset-yes", text: t("ap_reset_yes"), onclick: reset });
    refs.resetConfirm = make("div", { class: "ap-confirm", id: "ap-reset-confirm", role: "group", "aria-labelledby": "ap-reset-question", hidden: true },
      make("p", { id: "ap-reset-question", text: t("ap_reset_confirm") }),
      make("div", { class: "buttons" }, refs.resetYes, make("button", { type: "button", class: "button", id: "ap-reset-no", text: t("ap_cancel"),
        onclick: () => { confirmReset = false; sync(); refs.reset.focus(); } })));
    section.append(refs.status, refs.alert, make("h2", { text: t("ap_reset") }),
      make("p", { class: "muted", text: t("ap_reset_detail") }), make("div", { class: "buttons" }, refs.reset), refs.resetConfirm);
    say(message.text, message.kind);
    sync();
    if (focused && document.getElementById(focused)) document.getElementById(focused).focus();
  }

  function syncFrame() {
    if (!refs || !draft) return;
    refs.marker.style.left = draft.x + "%";
    refs.marker.style.top = draft.y + "%";
    refs.frameX.value = draft.x;
    refs.frameY.value = draft.y;
    refs.frameX.setAttribute("aria-valuetext", t("ap_percent", { n: draft.x }));
    refs.frameY.setAttribute("aria-valuetext", t("ap_percent", { n: draft.y }));
    refs.frameValue.textContent = `${t("ap_frame_x")} ${t("ap_percent", { n: draft.x })}, ${t("ap_frame_y")} ${t("ap_percent", { n: draft.y })}`;
  }

  function sync() {
    if (!refs) return;
    const check = (group, value) => { for (const input of group.querySelectorAll("input[type=radio]")) input.checked = input.value === value; };
    check(refs.theme, settings.theme);
    check(refs.palette, settings.palette);
    check(refs.density, settings.density);
    check(refs.backgroundChoice, draft ? "image" : settings.background);
    const preset = PRESETS.find(([, colour]) => colour === settings.accent);
    check(refs.accent, !settings.accent ? "default" : preset ? preset[0] : "custom");
    const custom = settings.accent && !preset;
    refs.custom.closest(".ap-custom").classList.toggle("ap-checked", Boolean(custom));
    if (settings.accent) refs.custom.value = settings.accent;
    refs.accentNote.textContent = !adjusted ? "" : adjusted.used !== adjusted.chosen
      ? t("ap_accent_adjusted", { chosen: adjusted.chosen, used: adjusted.used }) : t("ap_accent_kept", { used: adjusted.used });

    const hasImage = Boolean(settings.image && imageUrl);
    refs.thumb.hidden = !hasImage;
    if (hasImage && refs.thumb.src !== imageUrl) refs.thumb.src = imageUrl;
    refs.imageInfo.textContent = hasImage ? t("ap_bg_info", settings.image) : t("ap_bg_none_yet");
    refs.choose.textContent = hasImage ? t("ap_bg_replace") : t("ap_bg_choose");
    refs.remove.hidden = !hasImage;
    refs.choose.disabled = busy;
    refs.framing.hidden = !draft;
    refs.apply.disabled = busy;
    if (draft) {
      if (refs.frameImage.src !== draft.url) refs.frameImage.src = draft.url;
      syncFrame();
    }
    const showImageRows = settings.background === "image" || Boolean(draft);
    for (const node of refs.imageRows) node.hidden = !showImageRows;
    refs.dim.value = Math.round(settings.dim * 100);
    refs.dim.setAttribute("aria-valuetext", t("ap_percent", { n: refs.dim.value }));
    refs.dimValue.textContent = t("ap_percent", { n: refs.dim.value });
    const canBlur = blurAvailable();
    refs.blurSwitch.checked = canBlur && settings.blur > 0;
    refs.blurSwitch.disabled = !canBlur;
    refs.blur.disabled = !canBlur || settings.blur === 0;
    refs.blur.value = settings.blur || 12;
    refs.blur.setAttribute("aria-valuetext", t("ap_px", { n: refs.blur.value }));
    refs.blurValue.textContent = settings.blur ? t("ap_px", { n: settings.blur }) : "";
    refs.blurDetail.textContent = canBlur ? t("ap_blur_detail") : t("ap_blur_unavailable");
    refs.resetConfirm.hidden = !confirmReset;
    refs.reset.hidden = confirmReset;
  }

  // Start ------------------------------------------------------------------------------------------------------------
  try { settings = normalise(JSON.parse(localStorage.getItem(CACHE))); } catch (error) {}
  apply();
  darkScheme.addEventListener("change", () => { apply(); sync(); });
  lessTransparency.addEventListener("change", () => { apply(); sync(); });
  // The window redraws itself every 1.5 s (corsu:render): this page is rebuilt only when the language changed, so a
  // slider being dragged, the colour picker and the messages (live regions) are left alone.
  let renderedLanguage = null;
  document.addEventListener("corsu:render", () => { if (!refs || renderedLanguage !== language()) render(); });
  document.addEventListener("corsu:page", () => {
    const section = document.getElementById("appearance");
    if (section && (!refs || !section.contains(refs.status))) render();
  });
  window.addEventListener("pagehide", () => {
    if (unsaved) fetch("/api/appearance", { method: "POST", keepalive: true, headers: { "X-Corsu": "1", "Content-Type": "application/json" }, body: changes() });
  });
  const start = () => { render(); load(); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
  window.corsuAppearance = { get settings() { return { ...settings }; }, adjustAccent, contrast, rgb, flush: save };
})();
