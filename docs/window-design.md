# Corsu window: visual direction and shared interfaces

This note fixes what the people working on the window share, so the parts written separately fit together.

## Direction

- Calm, precise settings app. Corsican identity through colour and type, never through flags or postcards: the
  default palette "Maquis" takes a deep green-teal accent (maquis, sea in shade) on warm off-white paper; other
  palettes: "Mare" (sea blue), "Granitu" (warm granite grey with an ochre accent), "Tramontu" (dusk terracotta),
  "Notte" (ink blue, designed for dark). Each palette defines a light and a dark variant.
- Type: system UI font, sizes in `rem` (the page follows the person's text size), clear scale: page title
  1.5rem/600, section title 0.8125rem uppercase-free muted 600, row name 1rem/550, details 0.875rem.
- Spacing on a 4px grid, tokens `--space-1` … `--space-8`.
- Icons: one inline SVG sprite (`<svg><symbol id="i-…">`), 20px, 1.75 stroke, `currentColor`, rounded caps.
  Every icon is decorative (`aria-hidden="true"`) next to visible text, or the control has an accessible name.
- Programs page: a compact summary first ("6 in Corsican · 1 needs attention · update available"), then one
  dense list. A row is one line (icon, name, state chip, switch) with its description beneath; details (coverage,
  tests, installations, paths) open on demand. No big cards per program. Attention and errors are sorted first
  and marked by an icon and a word, never by colour alone.

## Tokens (style.css, `:root`)

Surfaces: `--bg` (page), `--surface` (panels, rows; opaque enough over any background image),
`--surface-2` (sidebar, raised parts), `--line`, `--text`, `--muted`, `--accent`, `--on-accent`, `--accent-soft`
(tinted backgrounds), `--focus`. Status colours, protected (not user-settable): `--ok`, `--warn`, `--danger`,
`--info`, each with `-soft` backgrounds; they are checked for contrast against `--surface` in both themes.

## Appearance contract (between style.css/app.js and appearance.js/appearance.py)

Applied on `<html>`:

| Attribute / property | Values | Set by |
|---|---|---|
| `data-theme` | `light`, `dark` (resolved; `system` follows `prefers-color-scheme`) | appearance.js |
| `data-palette` | `maquis`, `mare`, `granitu`, `tramontu`, `notte` | appearance.js |
| `data-density` | `comfortable`, `compact` | appearance.js |
| `--accent-user` | a colour, or unset (palette accent) | appearance.js, after contrast adjustment |
| `data-background` | `none`, `image` | appearance.js |
| `--bg-image` | `url("/appearance/background?v=<hash>")` | appearance.js |
| `--bg-position` | e.g. `50% 30%` | appearance.js |
| `--bg-dim` | 0 … 0.85 (overlay opacity) | appearance.js |
| `--bg-blur` | 0px … 24px | appearance.js |
| `data-reduced-transparency` | present when blur/transparency is unavailable or reduced | appearance.js |

style.css defines the palettes per `data-palette` × `data-theme`, uses `--accent-user` over the palette accent
when set, and draws the background layer (`body::before` image with position, `body::after` dim overlay,
`backdrop-filter: blur(var(--bg-blur))` on surfaces only where `@supports` allows, otherwise opaque surfaces).

The Appearance page lives in `<section id="appearance" data-page-panel>`; appearance.js fills it with the
shared component classes (`.group` rows, `.switch`, `.button`, `.segmented`, `.swatches`, `.range`).

## Server interface (src/appearance.py, wired in src/app.py)

Every route below, reads included, needs allowed(): Host, `X-Corsu: 1`, Origin, the window's key in `X-Corsu-Key`
and, on Linux, the connection's owner (docs/window-security.md). The page gets the key from `src/app/key.js`
(`corsuAccess.ready`, `corsuAccess.headers(extra)`), loaded before every other script.

- `GET /appearance/settings` → current settings JSON (defaults when missing or damaged).
- `POST /api/appearance` (allowed() checks) → validated settings saved to `DATA/appearance/settings.json`.
- `POST /api/appearance/background` (allowed() checks, raw image bytes, size-limited) → stored copy in
  `DATA/appearance/`; answers its id and dimensions.
- `POST /api/appearance/reset` → appearance files removed; installation state untouched.
- `GET /appearance/background` → the stored image, or 404 (the page falls back to the plain background).

`appearance.handle(method, path, body, headers, allowed)` returns `(status, body, content_type)` or None.
