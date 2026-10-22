-- Noctalia provides the bar, launcher, notifications, lock screen, idle, OSD, wallpaper, clipboard, screenshots and
-- the polkit agent: besides it, only the KWallet PAM helper is started here. "hyprland.start" fires once per session, not on config reloads.
hl.on("hyprland.start", function()
    -- pgrep keeps a second shell from starting when Noctalia was already launched (by the session or by hand).
    hl.exec_cmd("pgrep -x -u \"$(id -u)\" noctalia >/dev/null || uwsm app -- noctalia 2>/dev/null || exec noctalia")
    -- KWallet opens with the login password only if its PAM helper runs; Plasma starts it, Hyprland does not.
    hl.exec_cmd("[ -x /usr/lib/pam_kwallet_init ] && exec /usr/lib/pam_kwallet_init")
end)
