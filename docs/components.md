# What each component changes

The installer only touches the components you select. It records every file it writes, with a backup of the
original, in Corsu's data folder:

| System | Data folder |
| --- | --- |
| Windows | `%LOCALAPPDATA%\corsu` |
| macOS | `~/Library/Application Support/corsu` |
| Linux | `~/.local/share/corsu` |

`installation.json` in that folder lists the managed files; `backups/` holds the originals. `--uninstall` puts
back every file that still holds what Corsu wrote and reports the ones you changed since.

## Firefox

Corsu copies your Firefox into the data folder and translates the copy. Your own Firefox stays untouched, and
the copy opens your usual profile, so bookmarks, passwords and extensions are all there.

The translation starts from Mozilla's French language pack for your exact Firefox version, downloaded from
`archive.mozilla.org` and checked against Mozilla's published `SHA512SUMS` (a copy bundled with the release is
used when you are offline). The Corsican lexicon is then applied on top. When Firefox updates, the copy is
rebuilt the next time you open it.

Firefox's security settings and add-on signature checks are unchanged. The copy's own updater is switched off,
since Corsu rebuilds it from your updated Firefox.

You start it from **Firefox Corsu**: a Start menu shortcut on Windows, an app in `~/Applications` on macOS, and
the usual Firefox entry in the application menu on Linux (`~/.local/bin/firefox-corsu` from a terminal).

The regular Mozilla build is required. Snap and Flatpak versions are sealed and cannot be copied this way.

## Chrome, Opera GX and other Chromium browsers

Supported on Windows and Linux: Google Chrome, Chromium, Opera, Opera GX, Microsoft Edge, Brave and Vivaldi.

Chromium browsers keep their French text in one file per language (`fr.pak`). Corsu rewrites that file with the
Corsican translations, in place, so the browser shows Corsican wherever it would show French. Nothing else in
the browser changes, and your profile, logins and cookies are not touched.

- **Windows:** Corsu selects French in the browser's language setting. Browsers installed for all users (in
  `Program Files`) need administrator rights, so Windows asks for confirmation.
- **Linux:** the browser's menu entry goes through Corsu, which starts it with `LANGUAGE=co:fr`. System-wide
  browsers ask for your password through `pkexec`.

A browser update brings a new French file. Corsu translates it again when you open the browser from its menu
entry (Linux) or when you log in (Windows).

macOS is not supported yet. Changing a signed browser there breaks its access to the passwords and cookies it
keeps in the Keychain.

## Discord and Vesktop

Corsu builds Vencord, an open-source Discord client mod, with a small Corsu plugin that translates Discord's
interface. Chat messages, server names, user names and anything you type are never translated.

Native Discord is patched with the official Vencord installer, after checking its SHA-256 against the version
pinned in `release.json`. Vesktop only needs a setting pointing it at Corsu's Vencord build. Vencord's
automatic updates are switched off so that they do not remove the plugin.

Discord updates can remove the patch. Open **Corsu Setup** again after a Discord update if the interface is
back in French.

## KDE Plasma (Linux)

Corsu writes Corsican translation catalogs to `~/.local/share/locale/co` (gettext `.mo` files and Qt `.qm`
files) from the French catalogs installed on the system, and sets Plasma's interface language to `co:fr`, which
means Corsican first and French for anything not yet translated. Application names in the menu stay as their
authors wrote them. Log out and back in afterwards.

The optional `qt` component also copies Corsican catalogs for Qt's own dialogs (standard buttons, file
choosers) into `/usr/share/qt6/translations`. That folder belongs to the system, so it asks for your password,
and `--uninstall` removes the files again.

## Switching off

`--disable` returns every application to its previous language but keeps everything Corsu built, so that
`--enable` is immediate. It restores the browser language files and settings, the Plasma language setting and
the menu entries, and switches the Discord plugin off.
