-- Hyprland configuration started by Corsu (https://github.com/Platykalt/corsu).
-- Written only when there was no hyprland.lua; Corsu never rewrites this file afterwards.
-- corsu/ holds Corsu's modules (replaced on update); put your own changes in user.lua, loaded last, so that they win.

require("corsu.init")

-- Hyprland's require raises an error only when the module is missing; errors inside user.lua are shown by Hyprland.
local ok, err = pcall(require, "user")
if not ok and not tostring(err):find("not found", 1, true) then
    error(err)
end
