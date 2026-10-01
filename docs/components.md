# What Corsu changes

Corsu only touches the programs you pick. Each file it writes is listed in `installation.json`, and the original
is copied to a `backups` folder next to it. Both live in Corsu's data folder: `%LOCALAPPDATA%\corsu` on Windows,
`~/Library/Application Support/corsu` on macOS and `~/.local/share/corsu` on Linux.

Uninstalling puts back every original file. If you edited one of those files yourself after installing, Corsu
leaves your version in place and tells you where the original copy is.

## Firefox

Corsu makes a copy of your Firefox in its data folder and translates the copy. Your own Firefox is not modified.
The copy opens your normal profile, so your bookmarks, passwords and extensions are there.

The translation is built from Mozilla's French language pack for your exact version of Firefox. Corsu downloads
it from archive.mozilla.org and checks it against the checksums Mozilla publishes. If you are offline it uses the
copy included in the release. The Corsican translations are applied on top of the French text.

When Firefox updates, the copy is rebuilt the next time you open it. The copy's own updater is turned off for
that reason. Firefox's security settings and add-on checks are left as they are.

On Windows you open it with the Firefox Corsu shortcut in the Start menu, and on macOS with the Firefox Corsu
app in `~/Applications`. On Linux your usual Firefox menu entry opens it, and `~/.local/bin/firefox-corsu` does
the same from a terminal.

The Snap and Flatpak versions of Firefox cannot be copied, so Corsu needs the regular version from Mozilla or
from your distribution.

## Chromium browsers

This covers Google Chrome, Chromium, Opera, Opera GX, Microsoft Edge, Brave and Vivaldi, on Windows and Linux.

These browsers keep the French text of their interface in one file, `fr.pak`. Corsu rewrites that file with the
Corsican translations. The browser then shows Corsican wherever it would have shown French. Your profile,
saved passwords and cookies are not touched.

On Windows, Corsu sets the browser's language to French so that it reads that file. A browser installed for all
users lives in `Program Files`, so Windows asks for permission before Corsu can change it.

On Linux, the browser's menu entry goes through Corsu, which starts the browser with `LANGUAGE=co:fr`. If the
browser was installed by your distribution, you are asked for your password.

A browser update brings a fresh French file. Corsu translates it again the next time you log in on Windows, or
when you open the browser from its menu entry on Linux.

On macOS, changing a browser's files breaks its signature, and the browser then loses access to the passwords and
cookies it keeps in the Keychain. Corsu does not support these browsers on macOS for that reason.

## Discord

Corsu uses Vencord, an open-source modification of the Discord app, with a small plugin that translates the
interface. Messages, server names and user names are never translated.

The Discord app is patched with the official Vencord installer, after Corsu has checked its checksum against
the one recorded in `release.json`. Vesktop, a Discord app that already includes Vencord, only needs a setting.
Vencord's automatic updates are turned off because they would remove the plugin.

A Discord update can undo the patch. If Discord is back in French after an update, open Corsu Setup again.

## KDE Plasma

On Linux, Corsu builds Corsican translation files for the desktop and the KDE programs from the French ones
installed on your system, and puts them in `~/.local/share/locale/co`. It then sets Plasma's language to
`co:fr`, so anything without a Corsican translation is shown in French. Program names in the menu are kept as
they are. Log out and back in to see the change.

Qt, the toolkit KDE is built on, has its own standard buttons and file dialogs. Their translations live in
`/usr/share/qt6/translations`, which belongs to the system. The optional `qt` component copies Corsican files
there after asking for your password, and removes them when you uninstall.

## Going back to French

Switching Corsican off returns every program to the language it had before, but keeps the translated files, so
switching it on again is immediate.
