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
Discord, see [Discord](../discord.md).

## Changing your mind

Open the Corsu app from the Start menu to add a program, switch a part off for a while, or remove Corsu. Removing it
puts back the original files.
