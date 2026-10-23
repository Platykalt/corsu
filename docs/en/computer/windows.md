# Installing Corsu on Windows

[Français](../../fr/ordinateur/windows.md)

Windows 10 and 11 (64-bit).

1. Download [corsu-windows.zip](https://github.com/Platykalt/corsu/releases/latest/download/corsu-windows.zip).
2. Right-click the file, choose Extract All, and open the `corsu` folder.
3. Double-click `Install for Windows.cmd`.
4. The Corsu app opens in its own window and lists the programs found, all ticked. Untick what you do not want,
   click Continue, read what Corsu will change, then click Install.

Windows may warn you that the file comes from the internet. Choose Run, or More info and then Run anyway. The file
is a short text script, and Windows shows this warning for any downloaded script that is not signed.

There is nothing else to install: the archive carries its own Python, with what Corsu's window needs (WebView2,
already part of Windows 10 and 11). From the source code, Python 3.10 or newer is needed; when it is missing, the
script offers to install it with `winget`.

You can also install from PowerShell in one line:

```powershell
irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1 | iex
```

Close Firefox, Chrome, Opera GX and Discord before confirming, and open them again afterwards. Firefox in Corsican
opens from the Firefox Corsu shortcut in the Start menu. Chrome, Opera GX and Edge keep their usual shortcut. For
Discord, see [Discord](../discord.md). Corsu also sets to Corsican the language of programs that have their own
Corsican translation (VLC, 7-Zip, Notepad++, Audacity, PDFsam…) and puts Minecraft: Java Edition in Corsican, see
[Translation status](../translation-status.md).

## Corsu 0.27.0: the window closes at start

With Corsu 0.27.0 (and already 0.26.0) on Windows, Corsu's window closes as soon as it opens (when installing as
well as from the Start menu): Corsu gave the window an icon in a format Windows refuses, and the program stopped. The
fix comes with the next version. Meanwhile, Corsu works in the browser with the `--browser` option: the same page
opens in a tab instead of its window.

Corsu is not installed yet (the window closed during installation): install it in the terminal, with the `--text`
option passed to the one-line installation:

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/Platykalt/corsu/main/install/get.ps1))) --text
```

Or, from the `corsu` folder extracted from the archive (right-click inside the folder, Open in Terminal), with the
archive's Python:

```powershell
.\runtime\x86_64\python\python.exe .\src\app.py --browser
```

Corsu is installed (Corsu is in the Start menu): these commands read the Start menu's Corsu shortcut and start it with
`--browser`, without changing it:

```powershell
$corsu = (New-Object -ComObject WScript.Shell).CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Corsu.lnk")
Start-Process -FilePath $corsu.TargetPath -ArgumentList "$($corsu.Arguments) --browser" -WorkingDirectory $corsu.WorkingDirectory
```

To avoid typing them again, make a "Corsu (browser)" shortcut on the Desktop:

```powershell
$shell = New-Object -ComObject WScript.Shell
$corsu = $shell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Corsu.lnk")
$copy = $shell.CreateShortcut("$([Environment]::GetFolderPath('Desktop'))\Corsu (browser).lnk")
$copy.TargetPath = $corsu.TargetPath
$copy.Arguments = "$($corsu.Arguments) --browser"
$copy.WorkingDirectory = $corsu.WorkingDirectory
$copy.IconLocation = $corsu.IconLocation
$copy.Save()
```

Do not change the Start menu's Corsu shortcut itself: Corsu rewrites it at every update and refuses to touch a
shortcut changed by hand, which would make the update fail. Once Corsu is updated to the fixed version, delete the
"Corsu (browser)" Desktop shortcut: it points to the previous version.

## Changing your mind

Open the Corsu app from the Start menu to add a program, switch a part off for a while, or remove Corsu. Removing it
puts back the original files.
