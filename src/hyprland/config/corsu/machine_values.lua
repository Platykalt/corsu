-- Reads corsu/machine.lua, written by Corsu's detection at enable time (keyboard, outputs, pointer, preferred apps).
-- It returns a plain table; when it is missing or broken, every module falls back to Hyprland's own defaults.
-- Expected shape (all fields optional):
--   keyboard = { layout = <xkb layout>, variant = <xkb variant>, model = <xkb model>, options = <xkb options> }
--   monitors = { { output = <connector>, mode = <width x height @ rate>, position = <x x y>, scale = <number> }, … }
--   pointer  = { accel_profile = <"flat" | "adaptive"> }
--   apps     = { terminal = <desktop ID>, files = <desktop ID>, browser = <desktop ID> }

local ok, machine = pcall(require, "corsu.machine")
if not ok or type(machine) ~= "table" then
    machine = {}
end
return machine
