# Installer Corsu sous Windows

[English](../../en/computer/windows.md)

Windows 10 et 11 (64 bits).

1. Téléchargez [corsu-windows.zip](https://github.com/Platykalt/corsu/releases/latest/download/corsu-windows.zip).
2. Faites un clic droit sur le fichier, choisissez Extraire tout, puis ouvrez le dossier `corsu`.
3. Double-cliquez sur `Install for Windows.cmd`.
4. L'application Corsu s'ouvre dans sa fenêtre et affiche les logiciels trouvés, tous cochés. Décochez ce que vous ne voulez pas,
   cliquez sur Continuer, lisez ce que Corsu va changer, puis cliquez sur Installer.

Windows peut prévenir que le fichier vient d'Internet. Choisissez Exécuter, ou Informations complémentaires puis
Exécuter quand même. Windows affiche cet avertissement pour tout script téléchargé qui n'est pas signé.

Il n'y a rien d'autre à installer : l'archive contient son propre Python, avec ce qu'il faut pour la fenêtre de
Corsu (WebView2, déjà présent dans Windows 10 et 11). Depuis le code source, il faut Python 3.10 ou plus récent ; s'il
manque, le script propose de l'installer avec `winget`.

On peut aussi installer en une ligne depuis PowerShell :

```powershell
irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex
```

Fermez Firefox, Chrome, Opera GX et Discord avant de confirmer, puis rouvrez-les. Firefox en corse s'ouvre avec le
raccourci Firefox Corsu du menu Démarrer. Chrome, Opera GX et Edge gardent leur raccourci habituel. Pour Discord,
voir [Discord](../discord.md). Corsu règle aussi sur le corse la langue des logiciels qui ont leur propre traduction
corse (VLC, 7-Zip, Notepad++, Audacity, PDFsam…) et met en corse Minecraft: Java Edition, voir
[État des traductions](../etat-des-traductions.md).

## Corsu 0.27.0 : la fenêtre se ferme au démarrage

Avec Corsu 0.27.0 (et déjà 0.26.0) sous Windows, la fenêtre de Corsu se ferme aussitôt ouverte (à l'installation
comme depuis le menu Démarrer) : Corsu donnait à la fenêtre une icône dans un format que Windows refuse, et le
programme s'arrêtait. La correction arrivera avec la prochaine version. En attendant, Corsu marche dans le navigateur avec
l'option `--browser` : la même page s'ouvre dans un onglet au lieu de sa fenêtre.

Corsu n'est pas encore installé (la fenêtre s'est fermée pendant l'installation) : installez-le dans le terminal,
avec l'option `--text` passée à l'installation en une ligne :

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1))) --text
```

Ou, depuis le dossier `corsu` extrait de l'archive (clic droit dans le dossier, Ouvrir dans le Terminal), avec le Python
de l'archive :

```powershell
.\runtime\x86_64\python\python.exe .\src\app.py --browser
```

Corsu est installé (Corsu figure dans le menu Démarrer) : ces commandes lisent le raccourci Corsu du menu Démarrer et
le lancent avec `--browser`, sans le modifier :

```powershell
$corsu = (New-Object -ComObject WScript.Shell).CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Corsu.lnk")
Start-Process -FilePath $corsu.TargetPath -ArgumentList "$($corsu.Arguments) --browser" -WorkingDirectory $corsu.WorkingDirectory
```

Pour ne pas retaper ces commandes, créez un raccourci « Corsu (navigateur) » sur le Bureau :

```powershell
$shell = New-Object -ComObject WScript.Shell
$corsu = $shell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Corsu.lnk")
$copie = $shell.CreateShortcut("$([Environment]::GetFolderPath('Desktop'))\Corsu (navigateur).lnk")
$copie.TargetPath = $corsu.TargetPath
$copie.Arguments = "$($corsu.Arguments) --browser"
$copie.WorkingDirectory = $corsu.WorkingDirectory
$copie.IconLocation = $corsu.IconLocation
$copie.Save()
```

Ne modifiez pas le raccourci Corsu du menu Démarrer lui-même : Corsu le réécrit à chaque mise à jour et refuse de
toucher à un raccourci changé à la main, ce qui ferait échouer la mise à jour. Une fois Corsu mis à jour vers la
version corrigée, supprimez le raccourci « Corsu (navigateur) » du Bureau : il désigne la version précédente.

## Changer d'avis

Ouvrez l'application Corsu dans le menu Démarrer pour ajouter un logiciel, mettre une partie en pause ou retirer Corsu. Le
retirer remet les fichiers d'origine.
