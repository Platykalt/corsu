# How Noctalia 5.3 loads `co.json`, and what Corsu writes

Read in Noctalia's source at tag `v5.3.0` (commit `a33122c`, the package's `assets/` are byte-identical to it). Paths
below are relative to that source tree. Nothing here was observed in a running Noctalia: Noctalia and Hyprland are not
installed on the machine this was written on.

## How the language is chosen

1. At start, `ApplicationServices` calls `i18n::Service::init(config.shell.lang)`, and again `setLanguage()` on every
   config reload (`src/app/application_services.cpp:636-640`). So `[shell] lang` in any config layer switches the
   language live.
2. When `lang` is empty, the language comes from `$LC_ALL`, then `$LC_MESSAGES`, then `$LANG`
   (`src/i18n/i18n_service.cpp:31-40`). **`$LANGUAGE` is not read**, so the `LANGUAGE=co:fr:en` of the Hyprland session
   does not select Corsican, and setting `LC_MESSAGES=co_FR.UTF-8` would require a glibc locale that does not exist.
   Corsu therefore sets `lang = "co"` in config.
3. The tag is normalised (`co_FR.UTF-8` → `co-FR`, `src/i18n/language_tag.cpp:162-203`); the files tried for `co` are
   just `co.json` (`catalogLanguageCandidates`, lines 214-242).
4. The Settings window's language list is the fixed array `kSupportedLanguages` (`src/i18n/i18n_service.h:117-145`,
   used by `languageSelect()` in `src/shell/settings/settings_registry.cpp:290-298`): Corsican is not offered there.
   A language picked there goes to `settings.toml` and wins over Corsu's file, as it should.

## Where the catalogue is read from

- `loadCatalog()` opens `paths::assetPath("translations/<lang>.json")` (`src/i18n/i18n_service.cpp:49-69`).
- The asset root is resolved once per process and cached (`src/core/files/resource_paths.cpp:103-106`): first
  `$NOCTALIA_ASSETS_DIR`, **used alone** when it is a valid bundle, then folders next to the executable, then the
  compiled-in `/usr/share/noctalia/assets` (lines 60-99).
- A valid bundle must contain `emoji.json`, `fonts/noctalia-tabler.ttf`, `templates/builtin.toml` and
  `translations/en.json` (`isAssetRoot`, lines 28-38). An invalid one is logged and ignored.
- There is no per-user translation folder. Plugin translations (`src/scripting/plugin_i18n.cpp`) only serve a plugin's
  own keys, not the shell's.

So the only way to add `co` without touching package files is a **user asset bundle** named by `NOCTALIA_ASSETS_DIR`.

## What happens when a key is missing

- `lookup()` returns the active catalogue's value, else English, else nothing (`src/i18n/i18n_service.cpp:120-128`);
  English is always loaded as the fallback (lines 80-84). There is no second fallback language.
- A key found in neither shows as `!!key!!` (`src/i18n/i18n.h:22`, `62-64`). An **empty string** counts as missing
  too (the empty view is tested, not the presence of the key), so `co.json` must never contain `""`.
- Plurals: `trp()` uses `key` when count is 1 and `key-plural` otherwise, 0 included (`src/i18n/i18n.h:75-82`).
- `{name}` placeholders are replaced by name; an unknown name stays visible as `{name}` (`src/i18n/i18n.cpp`).

To get Corsican, then French, then English, Corsu builds the bundle's `co.json` itself: French catalogue of the
installed Noctalia, overlaid by Corsu's Corsican; Noctalia adds English for whatever is still missing.

## The lock screen

The password check runs in a re-executed `noctalia pam-helper <service> <language>`, which inherits the environment
and refuses to run if it cannot load the same language (`src/auth/pam_authenticator.cpp:360-381`, `419-425`; the
language passed is the active one, `src/shell/lockscreen/lock_screen.cpp:1399`). Consequence for disabling: the bundle
must not disappear while a Noctalia started with `lang = "co"` is running, or unlocking fails. Remove
`00-corsu-language.toml` first (Noctalia reloads and leaves Corsican), and the bundle afterwards, or only at the next
login. PAM's own messages come from Linux-PAM's gettext catalogue, chosen by the locale Noctalia sets at start
(`src/main.cpp:257`) and `LANGUAGE`: French exists (`/usr/share/locale/fr/LC_MESSAGES/Linux-PAM.mo`), Corsican does
not.

## What Corsu writes (language component)

| File | Content |
| --- | --- |
| `~/.local/share/corsu/noctalia/assets/` | the bundle: one symbolic link per entry of `/usr/share/noctalia/assets/` (`emoji.json`, `fonts`, `templates`, `firefox_theme`, `noctalia.svg`, `noctalia-wallpaper.png`) except `translations/` |
| `…/assets/translations/` | a real folder: one link per `*.json` of the package's `translations/`, plus Corsu's generated `co.json` |
| `~/.config/uwsm/env-hyprland` (A's block) | `export NOCTALIA_ASSETS_DIR="$HOME/.local/share/corsu/noctalia/assets"`: only the Hyprland session sees it |
| `~/.config/noctalia/00-corsu-language.toml` | `[shell] lang = "co"`; sorted before `config.toml`, so the person's own files and `settings.toml` win |

Generating the bundle's `co.json` (at enable, and whenever the installed `en.json` changes, for instance after a
Noctalia update):

1. read the installed `en.json` and `fr.json` and flatten them (dotted keys, as Noctalia does);
2. start from `fr.json` restricted to the keys of `en.json`;
3. for each key of `src/hyprland/translations/co.json`: keep it only if the key still exists in `en.json` and the SHA-1
   of the installed English text starts with the hash recorded in `co.source-hashes.tsv` (a changed English text means
   the Corsican may be wrong: French or English shows until it is translated again);
4. drop any empty value, write nested JSON (UTF-8) atomically.

If the package moves or a link breaks, `isAssetRoot` fails, Noctalia logs a warning and uses its own assets: English,
nothing breaks. A new top-level asset in a later Noctalia version is missing from the bundle until Corsu refreshes the
links; refreshing at every Corsu start, comparing the folder listing, avoids that.
