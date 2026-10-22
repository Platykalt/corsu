-- Window rules: dialogs and small tools float centred instead of taking half the screen.
-- Sizes are fractions of the output, so they suit any resolution and scale.

hl.window_rule({
    name = "corsu-modal-dialogs",
    match = { modal = true },
    float = true,
    center = true,
})

-- File choosers of the portals (KDE and GTK) and of Qt/GTK programs, titled in English, French or Corsican.
hl.window_rule({
    name = "corsu-file-choosers",
    match = {
        class = "^(xdg-desktop-portal-gtk|org\\.freedesktop\\.impl\\.portal\\.desktop\\.kde|xdg-desktop-portal-kde)$",
    },
    float = true,
    center = true,
    size = { "monitor_w * 0.6", "monitor_h * 0.65" },
})

hl.window_rule({
    name = "corsu-open-save-dialogs",
    match = {
        title = "^(Open|Save|Ouvrir|Enregistrer|Apre|Arregistrà|Choose|Choisir|Sceglie|Select|Sélectionner|Selezziunà).*",
        float = true,
    },
    center = true,
})

hl.window_rule({
    name = "corsu-polkit-and-portal",
    match = { class = "^(org\\.kde\\.polkit-kde-authentication-agent-1|hyprland-share-picker|hyprpolkitagent)$" },
    float = true,
    center = true,
})

hl.window_rule({
    name = "corsu-sound-mixer",
    match = { class = "^(org\\.pulseaudio\\.pavucontrol|pavucontrol)$" },
    float = true,
    center = true,
    size = { "monitor_w * 0.4", "monitor_h * 0.55" },
})

-- Noctalia's settings window, as Noctalia's own documentation suggests.
hl.window_rule({
    name = "corsu-noctalia-settings",
    match = { class = "^dev\\.noctalia\\.Noctalia$" },
    float = true,
    size = { "monitor_w * 0.55", "monitor_h * 0.75" },
    center = true,
})

-- Firefox picture-in-picture: the window title is localised (Mozilla's Corsican says "Videò in finestra").
hl.window_rule({
    name = "corsu-firefox-pip",
    match = {
        class = "^(firefox|org\\.mozilla\\.firefox)$",
        title = "^(Picture-in-Picture|Incrustation vidéo|Videò in finestra)$",
    },
    float = true,
    pin = true,
    keep_aspect_ratio = true,
    size = { "monitor_w * 0.25", "monitor_h * 0.25" },
    move = { "monitor_w * 0.74", "monitor_h * 0.72" },
})
