# Installing Corsu on Windows

[En français plus bas](#en-français)

1. Download [corsu-windows.zip](https://github.com/Platykalt/corsu/releases/latest/download/corsu-windows.zip).
2. Right-click the file and choose Extract All, then open the `corsu` folder that appears.
3. Double-click `Install for Windows.cmd`.
4. Every program found is selected; type a number to leave one out, then press Enter and type `y` to confirm.

Windows may warn you that the file comes from the internet. Choose Run, or More info and then Run anyway. The file
is a short text script, and Windows shows this warning for any downloaded script that is not signed.

Corsu needs Python 3.10 or newer. If it is missing, the script offers to install it with `winget`; answer `y`,
wait for the installation to finish, and double-click `Install for Windows.cmd` again.

Close Firefox, Chrome, Opera GX and Discord before confirming, and open them again afterwards. Firefox in
Corsican opens from the new Firefox Corsu shortcut in the Start menu. Chrome and Opera GX keep their usual
shortcut.

To install without downloading the zip yourself, open PowerShell and run:

```powershell
irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex
```

## Changing your mind later

Open Corsu Setup from the Start menu. From there you can add a program, go back to French, or remove Corsu
entirely. Removing it restores the original files.

## En français

1. Téléchargez [corsu-windows.zip](https://github.com/Platykalt/corsu/releases/latest/download/corsu-windows.zip).
2. Faites un clic droit sur le fichier, choisissez Extraire tout, puis ouvrez le dossier `corsu`.
3. Double-cliquez sur `Install for Windows.cmd`.
4. Tous les logiciels trouvés sont sélectionnés ; tapez un numéro pour en retirer un, puis appuyez sur Entrée et tapez `y` pour confirmer.

Windows peut prévenir que le fichier vient d'Internet. Choisissez Exécuter, ou Informations complémentaires puis
Exécuter quand même. Windows affiche cet avertissement pour tout script téléchargé qui n'est pas signé.

Corsu a besoin de Python 3.10 ou plus récent. S'il manque, le script propose de l'installer avec `winget` :
répondez `y`, attendez la fin de l'installation, puis double-cliquez de nouveau sur `Install for Windows.cmd`.

Fermez Firefox, Chrome, Opera GX et Discord avant de confirmer, puis rouvrez-les. Firefox en corse s'ouvre avec
le nouveau raccourci Firefox Corsu du menu Démarrer. Chrome et Opera GX gardent leur raccourci habituel.

Pour revenir au français ou tout retirer, ouvrez Corsu Setup dans le menu Démarrer.
