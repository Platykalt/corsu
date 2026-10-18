"use strict";
// The « On the phone » page: writing Corsican on Android and iPhone with the Keyman keyboard and Corsu's dictionary.
// Nothing here talks to Corsu's server: the page only shows public addresses (GitHub, the stores), opened in the
// browser, and QR codes drawn beforehand by tools/make_qr.py (src/app/qr/), which point to the public guides.
(() => {
  const DOCS = "https://github.com/Platykalt/corsu/blob/main/docs/";
  const RELEASE = "https://github.com/Platykalt/corsu/releases/latest/download/";
  const PLATFORMS = {
    android: { name: "Android", steps: ["ph_a1", "ph_a2", "ph_a3", "ph_a4", "ph_a5", "ph_a6"], store: "ph_store_android",
      storeUrl: "https://play.google.com/store/apps/details?id=com.tavultesoft.kmapro",
      guide: { fr: "fr/telephone/android.md", en: "en/phone/android.md" } },
    iphone: { name: "iPhone", steps: ["ph_i1", "ph_i2", "ph_i3", "ph_i4", "ph_i5"], store: "ph_store_iphone",
      storeUrl: "https://apps.apple.com/app/keyman/id933676545",
      guide: { fr: "fr/telephone/iphone.md", en: "en/phone/iphone.md" } },
  };
  // Only the dictionaries attached to the latest published release. A variant joins this list in the release that
  // carries its file, never before (a file announced here and missing would be a broken download).
  const VARIANTS = [{ file: "corsu-keyboard.kmp", name: "ph_variant_general", detail: "ph_variant_general_detail" }];
  // Built on the development branch for the next version, not published yet: shown apart, without a download. At
  // release time, move the entries that the release carries into VARIANTS (and empty this list).
  const COMING = [
    { file: "corsu-keyboard-cismuntincu.kmp", name: "ph_variant_cismuntincu", detail: "ph_variant_cismuntincu_detail" },
    { file: "corsu-keyboard-pumuntincu.kmp", name: "ph_variant_pumuntincu", detail: "ph_variant_pumuntincu_detail" },
  ];
  const SAVED = "corsu-phone-platform";

  let platform = "android";
  try { const saved = localStorage.getItem(SAVED); if (saved in PLATFORMS) platform = saved; } catch (error) {}
  let rendered = null;

  const corsu = () => window.corsu || {};
  function language() {
    const value = typeof corsu().language === "function" ? corsu().language() : null;
    return value && textsPhone[value] ? value : "fr";
  }
  // This page's texts first, then the window's (opens_browser…).
  const t = (name, values = {}) => (textsPhone[language()][name] ?? (corsu().t ? corsu().t(name) : name))
    .replace(/\{(\w+)\}/g, (_, key) => values[key]);
  // There are no Corsican guides: Corsican readers get the French ones.
  const guideLanguage = () => language() === "en" ? "en" : "fr";
  const guideUrl = name => DOCS + PLATFORMS[name].guide[guideLanguage()];

  function external(href, title, detail, glyph) {
    const { make, icon } = corsu();
    return make("li", { class: "link" },
      make("span", { class: "app-icon", "aria-hidden": "true" }, icon(glyph)),
      make("a", { class: "label", href, target: "_blank", rel: "noopener noreferrer" },
        make("span", { class: "name", text: title }), detail ? make("span", { class: "detail", text: detail }) : null,
        make("span", { class: "sr-only", text: " " + t("opens_browser") })),
      make("span", { class: "external", "aria-hidden": "true" }, icon("external")));
  }

  function choice() {
    const { make } = corsu();
    return make("div", { class: "segmented", role: "radiogroup", "aria-labelledby": "ph-choose" },
      ...Object.entries(PLATFORMS).map(([name, info]) => make("label", {},
        make("input", { type: "radio", name: "ph-platform", value: name, checked: name === platform, onchange: () => {
          platform = name;
          try { localStorage.setItem(SAVED, name); } catch (error) {}
          render();
          const chosen = document.querySelector(`#phone input[value="${name}"]`);
          if (chosen) chosen.focus();
        } }),
        make("span", { text: info.name }))));
  }

  function render() {
    const { make, icon } = corsu();
    const body = document.getElementById("phone-body");
    if (!body || !make || !icon) return;
    const info = PLATFORMS[platform];
    const url = guideUrl(platform);
    rendered = language() + platform;
    body.replaceChildren(
      make("ul", { class: "group" },
        make("li", { class: "tall" }, make("span", { class: "app-icon", "aria-hidden": "true" }, icon("phone")),
          make("span", { class: "label" }, make("span", { class: "name", text: t("ph_keyman") }),
            make("span", { class: "detail", text: t("ph_keyman_detail") }))),
        make("li", { class: "tall" }, make("span", { class: "app-icon", "aria-hidden": "true" }, icon("book")),
          make("span", { class: "label" }, make("span", { class: "name", text: t("ph_corsu") }),
            make("span", { class: "detail", text: t("ph_corsu_detail") })))),
      make("p", { class: "muted section-text ph-not", text: t("ph_not") }),
      make("h2", { id: "ph-choose", text: t("ph_choose") }),
      choice(),
      make("div", { class: "ph-columns" },
        make("section", { class: "group panel ph-steps", "aria-labelledby": "ph-steps-title" },
          make("h3", { id: "ph-steps-title", text: t("ph_steps") + " · " + info.name }),
          make("ol", {}, ...info.steps.map(key => make("li", { text: t(key) }))),
          make("p", { class: "muted", text: t("ph_auto") }),
          make("p", { class: "muted", text: t("ph_update") })),
        make("figure", { class: "group panel ph-qr" },
          make("img", { src: `qr/${platform}-${guideLanguage()}.svg`, width: "180", height: "180",
            alt: t("ph_qr_alt", { url }) }),
          make("figcaption", {},
            make("strong", { text: t("ph_qr") }),
            make("span", { class: "detail", text: t("ph_qr_text", { platform: info.name }) }),
            make("span", { class: "ph-url", text: url })))),
      make("ul", { class: "group list ph-links" },
        external(RELEASE + VARIANTS[0].file, t("ph_download"), t("ph_download_detail"), "update"),
        external(info.storeUrl, t(info.store), null, "app"),
        external(url, t("ph_guide"), info.name, "book")),
      make("h2", { text: t("ph_variants") }),
      make("ul", { class: "group" }, ...VARIANTS.map(variant => make("li", {},
        make("span", { class: "app-icon", "aria-hidden": "true" }, icon("translate")),
        make("span", { class: "label" }, make("span", { class: "name", text: t(variant.name) }),
          make("span", { class: "detail", text: t(variant.detail) + " · " + variant.file }))))),
      COMING.length ? make("h2", { text: t("ph_coming") }) : null,
      COMING.length ? make("p", { class: "muted section-text", text: t("ph_coming_text") }) : null,
      COMING.length ? make("ul", { class: "group ph-coming" }, ...COMING.map(variant => make("li", {},
        make("span", { class: "app-icon", "aria-hidden": "true" }, icon("clock")),
        make("span", { class: "label" }, make("span", { class: "name", text: t(variant.name) }),
          make("span", { class: "detail", text: t(variant.detail) + " · " + variant.file }))))) : null);
  }

  // The window redraws itself every 1.5 s (corsu:render): this page is rebuilt only when the language changed.
  document.addEventListener("corsu:render", () => { if (rendered !== language() + platform) render(); });
  document.addEventListener("corsu:page", event => { if (event.detail === "phone" && rendered !== language() + platform) render(); });
  window.corsuPhone = { render, platforms: PLATFORMS, variants: VARIANTS, coming: COMING, guideUrl };
})();
