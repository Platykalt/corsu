# vendor

Third-party files Corsu ships or fetches, pinned so that a release always installs the same thing.

| File | What it is | In git |
| --- | --- | --- |
| `vencord-installer-source.tar.gz` | Source code of the official Vencord installer (GPL-3.0), kept next to the binaries Corsu distributes | yes |
| `VencordInstallerCli-linux`, `VencordInstallerCli.exe`, `VencordInstallerCli-darwin` | The official Vencord installer. Downloaded at install time if absent, and run only when its SHA-256 matches `src/release.json` | no |
| `firefox-fr.xpi` | Mozilla's French language pack, used when archive.mozilla.org cannot be reached | no |

`tools/package_release.py` puts the binaries in the release archives.

---

Fichiers tiers que Corsu distribue ou télécharge, figés pour qu'une version installe toujours la même chose. Le source
de l'installeur Vencord (GPL-3.0) est gardé à côté des binaires distribués. Les binaires ne sont exécutés que si leur
somme SHA-256 correspond à celle de `src/release.json`.
