-- The one list of Corsu's keys: binds.lua registers these binds and writes the key help (SUPER + F1) from them, so
-- the help shown is always what is bound. Help texts are Corsican; "label" replaces the key text where the raw key
-- name would not tell the person what to press.
--
-- Each entry has "keys" and "help", and one action:
--   ipc = "…"           a Noctalia command (noctalia msg …)
--   app = "terminal"    a desktop entry from "apps" (detection may replace them in machine.lua)
--   dsp = "window.close", args = {…}   a Hyprland dispatcher
--   workspaces = "focus" | "move"      the ten number-row keys, by keycode so that AZERTY works (& é " ' ( - è _ ç à)

local M = {}

M.apps = {
    terminal = "org.kde.konsole",
    files = "org.kde.dolphin",
    browser = "firefox",
}

-- Keycodes 10 to 19 are the number row whatever the layout: on AZERTY they are & é " ' ( - è _ ç à.
M.number_row = { "code:10", "code:11", "code:12", "code:13", "code:14",
                 "code:15", "code:16", "code:17", "code:18", "code:19" }

local locked = { locked = true }
local repeating = { locked = true, repeating = true }

M.binds = {
    -- Noctalia
    { keys = "SUPER + Space", ipc = "panel-toggle launcher", help = "Apre o chjode u lanciadore d'appiecazioni" },
    { keys = "SUPER + F1", ipc = "panel-toggle launcher /tasti", help = "Affissà st'aiutu nant'à i tasti" },
    { keys = "SUPER + S", ipc = "panel-toggle control-center", help = "Apre o chjode u centru di cuntrollu" },
    { keys = "SUPER + V", ipc = "panel-toggle clipboard", help = "Cronolugia di u preme’papei" },
    { keys = "SUPER + N", ipc = "notification-dnd-toggle", help = "Attivà o disattivà « Ùn disturbà micca »" },
    { keys = "SUPER + comma", label = "SUPER + ,", ipc = "settings-toggle", help = "Parametri di Noctalia" },
    { keys = "SUPER + W", ipc = "panel-toggle wallpaper", help = "Sceglie u fondu di screnu" },
    { keys = "SUPER + L", ipc = "session lock", help = "Bluccà u screnu" },
    { keys = "SUPER + Escape", ipc = "panel-toggle session", help = "Chjode a sessione, rilancià, spenghje…" },
    { keys = "CTRL + ALT + Delete", ipc = "panel-toggle session", help = "Chjode a sessione, rilancià, spenghje…" },
    { keys = "ALT + Tab", ipc = "window-switcher hold", help = "Passà da una finestra à l'altra" },
    { keys = "Print", label = "Impr écran (Print)", ipc = "screenshot-region", help = "Cattura di screnu d'una zona" },
    { keys = "SUPER + SHIFT + S", ipc = "screenshot-region", help = "Cattura di screnu d'una zona" },
    { keys = "SHIFT + Print", label = "SHIFT + Impr écran (Print)", ipc = "screenshot-fullscreen",
      help = "Cattura di tuttu u screnu" },

    -- Programs
    { keys = "SUPER + Return", label = "SUPER + Entrée (Return)", app = "terminal", help = "Apre un terminale" },
    { keys = "SUPER + E", app = "files", help = "Apre u gestore di schedarii" },
    { keys = "SUPER + B", app = "browser", help = "Apre u navigatore web" },

    -- Windows
    { keys = "SUPER + Q", dsp = "window.close", help = "Chjode a finestra" },
    { keys = "ALT + F4", dsp = "window.close", help = "Chjode a finestra" },
    { keys = "SUPER + M", dsp = "window.fullscreen", args = { mode = "maximized" },
      help = "Massimizà a finestra o rimette a so dimensione" },
    { keys = "SUPER + F", dsp = "window.fullscreen", args = { mode = "fullscreen" },
      help = "Screnu sanu o ritornu" },
    { keys = "SUPER + T", dsp = "window.float", help = "Finestra fluttante o in mosaicu" },
    { keys = "SUPER + left", label = "SUPER + ←", dsp = "focus", args = { direction = "left" },
      help = "Andà à a finestra à manca" },
    { keys = "SUPER + right", label = "SUPER + →", dsp = "focus", args = { direction = "right" },
      help = "Andà à a finestra à diritta" },
    { keys = "SUPER + up", label = "SUPER + ↑", dsp = "focus", args = { direction = "up" },
      help = "Andà à a finestra di sopra" },
    { keys = "SUPER + down", label = "SUPER + ↓", dsp = "focus", args = { direction = "down" },
      help = "Andà à a finestra di sottu" },
    { keys = "SUPER + SHIFT + left", label = "SUPER + SHIFT + ←", dsp = "window.move", args = { direction = "left" },
      help = "Spustà a finestra à manca" },
    { keys = "SUPER + SHIFT + right", label = "SUPER + SHIFT + →", dsp = "window.move",
      args = { direction = "right" }, help = "Spustà a finestra à diritta" },
    { keys = "SUPER + SHIFT + up", label = "SUPER + SHIFT + ↑", dsp = "window.move", args = { direction = "up" },
      help = "Spustà a finestra in sù" },
    { keys = "SUPER + SHIFT + down", label = "SUPER + SHIFT + ↓", dsp = "window.move", args = { direction = "down" },
      help = "Spustà a finestra in ghjò" },
    { keys = "SUPER + mouse:272", label = "SUPER + clic manca tenutu", dsp = "window.drag",
      opts = { mouse = true }, help = "Spustà a finestra cù u topu" },
    { keys = "SUPER + mouse:273", label = "SUPER + clic dirittu tenutu", dsp = "window.resize",
      opts = { mouse = true }, help = "Ridimensiunà a finestra cù u topu" },

    -- Workspaces
    { keys = "SUPER", label = "SUPER + 1 … 0 (fila di e cifre)", workspaces = "focus",
      help = "Andà à u spaziu di travagliu 1 à 10" },
    { keys = "SUPER + SHIFT", label = "SUPER + SHIFT + 1 … 0 (fila di e cifre)", workspaces = "move",
      help = "Mandà a finestra à u spaziu di travagliu 1 à 10" },
    { keys = "SUPER + CTRL + right", label = "SUPER + CTRL + →", dsp = "focus", args = { workspace = "e+1" },
      help = "Spaziu di travagliu seguente" },
    { keys = "SUPER + CTRL + left", label = "SUPER + CTRL + ←", dsp = "focus", args = { workspace = "e-1" },
      help = "Spaziu di travagliu precedente" },
    { keys = "SUPER + mouse_down", label = "SUPER + rotula in ghjò", dsp = "focus", args = { workspace = "e+1" },
      help = "Spaziu di travagliu seguente" },
    { keys = "SUPER + mouse_up", label = "SUPER + rotula in sù", dsp = "focus", args = { workspace = "e-1" },
      help = "Spaziu di travagliu precedente" },

    -- Laptop and multimedia keys, also on the lock screen
    { keys = "XF86AudioRaiseVolume", label = "Tastu vulume +", ipc = "volume-up", opts = repeating,
      help = "Alzà u vulume" },
    { keys = "XF86AudioLowerVolume", label = "Tastu vulume −", ipc = "volume-down", opts = repeating,
      help = "Calà u vulume" },
    { keys = "XF86AudioMute", label = "Tastu mutu", ipc = "volume-mute", opts = locked,
      help = "Rende mutu o rende u sonu" },
    { keys = "XF86AudioMicMute", label = "Tastu micrufonu", ipc = "mic-mute", opts = locked,
      help = "Micrufonu mutu o attivu" },
    { keys = "XF86MonBrightnessUp", label = "Tastu luminosità +", ipc = "brightness-up", opts = repeating,
      help = "Cresce a luminosità" },
    { keys = "XF86MonBrightnessDown", label = "Tastu luminosità −", ipc = "brightness-down", opts = repeating,
      help = "Scresce a luminosità" },
    { keys = "XF86AudioPlay", label = "Tastu lettura", ipc = "media toggle", opts = locked,
      help = "Leghje o mette in pausa" },
    { keys = "XF86AudioPause", label = "Tastu pausa", ipc = "media toggle", opts = locked,
      help = "Leghje o mette in pausa" },
    { keys = "XF86AudioNext", label = "Tastu seguente", ipc = "media next", opts = locked, help = "Pezzu seguente" },
    { keys = "XF86AudioPrev", label = "Tastu precedente", ipc = "media previous", opts = locked,
      help = "Pezzu precedente" },
}

return M
