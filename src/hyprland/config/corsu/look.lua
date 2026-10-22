-- Corsu's look: maquis green and sea blue borders on dark surfaces, modest gaps and rounding, no blur, short
-- animations. Colours follow the "maquis" and "mare" palettes of Corsu's window (src/app/style.css).
-- Every value can be overridden in user.lua with another hl.config() call.

local maquis = "6cc4ad"  -- maquis accent, dark variant
local mare = "7ab8e8"    -- sea accent, dark variant
local line = "2b3531"    -- maquis outline, dark variant

hl.config({
    general = {
        gaps_in = 4,
        gaps_out = 8,
        border_size = 2,
        col = {
            active_border = { colors = { "rgba(" .. maquis .. "ee)", "rgba(" .. mare .. "ee)" }, angle = 45 },
            inactive_border = "rgba(" .. line .. "cc)",
        },
        resize_on_border = true,
        layout = "dwindle",
    },
    decoration = {
        rounding = 8,
        rounding_power = 2,
        shadow = { enabled = true, range = 6, render_power = 3, color = "rgba(0a0f0d66)" },
        -- Blur costs GPU time on every frame for little legibility gain; off unless the person turns it on.
        blur = { enabled = false },
    },
    animations = { enabled = true },
    dwindle = { preserve_split = true },
    misc = {
        disable_hyprland_logo = true,
        disable_splash_rendering = true,
        force_default_wallpaper = 0,
        -- Shown for a moment before Noctalia draws the wallpaper.
        background_color = "rgb(111614)",
    },
    -- Hyprland would otherwise copy its cursor theme into GSettings, a setting Plasma shares.
    cursor = { sync_gsettings_theme = false },
    ecosystem = { no_update_news = true, no_donation_nag = true },
})

-- Short and subtle: fades and a slight slide, nothing that delays work.
hl.curve("corsuOut", { type = "bezier", points = { { 0.22, 1 }, { 0.36, 1 } } })
hl.animation({ leaf = "global", enabled = true, speed = 4, bezier = "corsuOut" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 3, bezier = "corsuOut", style = "popin 92%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 2, bezier = "corsuOut", style = "popin 92%" })
hl.animation({ leaf = "border", enabled = true, speed = 4, bezier = "corsuOut" })
hl.animation({ leaf = "fade", enabled = true, speed = 3, bezier = "corsuOut" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 3, bezier = "corsuOut", style = "slidefade 15%" })

-- Noctalia animates its own bar, panels and notifications; Hyprland's layer animation would play on top of it.
hl.layer_rule({
    name = "corsu-noctalia-own-animations",
    match = { namespace = "^noctalia-.+$" },
    no_anim = true,
})
