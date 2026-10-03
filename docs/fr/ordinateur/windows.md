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

Corsu a besoin de Python 3.10 ou plus récent. S'il manque, le script propose de l'installer avec `winget` : répondez
`y`, attendez la fin, puis double-cliquez de nouveau sur `Install for Windows.cmd`.

On peut aussi installer en une ligne depuis PowerShell :

```powershell
irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex
```

Fermez Firefox, Chrome, Opera GX et Discord avant de confirmer, puis rouvrez-les. Firefox en corse s'ouvre avec le
raccourci Firefox Corsu du menu Démarrer. Chrome, Opera GX et Edge gardent leur raccourci habituel. Pour Discord,
voir [Discord](../discord.md).

## Changer d'avis

Ouvrez l'application Corsu dans le menu Démarrer pour ajouter un logiciel, mettre une partie en pause ou retirer Corsu. Le
retirer remet les fichiers d'origine.
