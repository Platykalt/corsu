-- Outputs: the detected ones from machine.lua, else every output at its preferred mode and automatic scale.
local machine = require("corsu.machine_values")

if type(machine.monitors) == "table" and #machine.monitors > 0 then
    for _, spec in ipairs(machine.monitors) do
        hl.monitor(spec)
    end
else
    hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })
end
