-- Keyboard, pointer and touchpad. The layout comes from detection (machine.lua); nothing here assumes AZERTY.
local machine = require("corsu.machine_values")

local input = {
    follow_mouse = 1,
    touchpad = {
        natural_scroll = true,
        tap_to_click = true,
        disable_while_typing = true,
        -- Clickpads have no buttons: two fingers click right, three click middle, wherever they press.
        clickfinger_behavior = true,
        tap_and_drag = true,
    },
}

local kb = type(machine.keyboard) == "table" and machine.keyboard or {}
for _, field in ipairs({ "layout", "variant", "model", "options" }) do
    if type(kb[field]) == "string" and kb[field] ~= "" then
        input["kb_" .. field] = kb[field]
    end
end

if type(machine.pointer) == "table" and type(machine.pointer.accel_profile) == "string" then
    input.accel_profile = machine.pointer.accel_profile
end

hl.config({ input = input })

-- Three fingers sideways change workspace, as on Plasma.
hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })
