# What Corsu changes

[Français](../fr/ce-que-corsu-modifie.md)

Corsu only touches the programs you pick. Each file it writes is listed in `installation.json`, and the original
is copied to a `backups` folder next to it. Both live in Corsu's data folder: `%LOCALAPPDATA%\corsu` on Windows,
`~/Library/Application Support/corsu` on macOS and `~/.local/share/corsu` on Linux.

Uninstalling puts back every original file. If you edited one of those files yourself after installing, Corsu
leaves your version in place and tells you where the original copy is.

## Firefox

Corsu makes a copy of your Firefox in its data folder and translates the copy. Your own Firefox is not modified.
The copy opens your normal profile, so your bookmarks, passwords, extensions, home page and settings are there, and
Corsu changes none of them. So that this also holds when the copy is started without Corsu (as the default browser,
for example), Corsu adds a line to `profiles.ini` that links it to that profile. If you make Firefox Corsu your
default browser, Corsu points that choice at the Firefox menu entry, which keeps its icon. Copies made for older
Firefox versions are removed.

Firefox can update its New Tab page separately, into your profile, with its own text. Corsu translates that text too
each time Firefox opens.

The translation is built from Mozilla's French language pack for your exact version of Firefox. Corsu downloads
it from archive.mozilla.org and checks it against the checksums Mozilla publishes. If you are offline it uses the
copy included in the release. The Corsican translations are applied on top of the French text.

The copy also tells websites that you prefer Corsican, then French. Sites that offer Corsican, Google among them,
then show it. Google's own Corsican interface is incomplete and falls back to French or English on some buttons and
menus; on Google's pages the copy completes those labels with the Corsu lexicon. Search results and other page
text are never changed, and no other website is touched.

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
saved passwords and cookies are not touched. The browser is also set to tell websites that you prefer Corsican,
then French.

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
the one recorded in `src/release.json`. Vesktop, a Discord app that already includes Vencord, only needs a setting.
Vencord's automatic updates are turned off because they would remove the plugin.

A Discord update can undo the patch. If Discord is back in French after an update, open the Corsu app again.

## KDE Plasma

On Linux, Corsu builds Corsican translation files for the desktop and the KDE programs from the French ones
installed on your system, and puts them in `~/.local/share/locale/co`. It then sets Plasma's language to
`co:fr`, so anything without a Corsican translation is shown in French. Program names in the menu are kept as
they are. Log out and back in to see the change.

Programs outside KDE (GTK programs, terminal commands) and Qt's own buttons and file dialogs only read
translations from system folders. The optional system translations copy the Corsican files to
`/usr/share/locale/co` and `/usr/share/qt6/translations` after asking for your password. Files that belong to an
installed package are never overwritten, and uninstalling removes what Corsu copied.

New terminals follow a small switch read by bash, zsh and fish, so the terminal can go back to French on its own,
for an hour or until you switch it on again.

## The Corsu app

The Corsu app is a page served by Corsu itself at a local address (`127.0.0.1`) that only your computer can
reach, protected by a key drawn at random each time it opens. Nothing is sent to the internet apart from the downloads
described above. It stops by itself ten minutes after you close the page.

While it is open, the app asks GitHub, at most once an hour, for the number of the latest Corsu release. When a newer
one exists, the Update button downloads the archive for your system, checks its SHA-256 checksum and reinstalls the
same programs as before. Nothing is installed without that click.

The Review page shows the translations written for Corsu, one at a time. Your corrections are saved in
`lexicon-user.tsv`, in Corsu's data folder, and read before every other translation; they are also copied into the
Discord plugin's settings. They stay on the computer unless you choose to send them to the project as a GitHub issue.

The Original text on hover option, under Programs, adds a tooltip with the replaced text to what Corsu translates in
Discord and on Google.

## Going back to French

Each part can be switched off on its own: Firefox, the Chromium browsers, Discord, Vesktop, the desktop, the
terminal. Switching a part off returns it to the language it had before but keeps the translated files, so
switching it on again is immediate.
