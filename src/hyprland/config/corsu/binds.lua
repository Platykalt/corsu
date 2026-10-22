-- Registers the binds of keys.lua and writes, from the same loop, the key help that Noctalia's launcher lists
-- under /tasti (SUPER + F1): one line per entry, "keys<TAB>help", in $XDG_RUNTIME_DIR/corsu/hypr-keys.tsv.
local keys = require("corsu.keys")
local machine = require("corsu.machine_values")

local apps = {}
for name, id in pairs(keys.apps) do
    apps[name] = id
end
if type(machine.apps) == "table" then
    for name, id in pairs(machine.apps) do
        if type(id) == "string" and id ~= "" then
            apps[name] = id
        end
    end
end

local function quote(text)
    return "'" .. text:gsub("'", "'\\''") .. "'"
end

-- Programs start from their desktop entry (name, icon and Corsu's Firefox wrapper come with it): through uwsm when the
-- session runs under it, else gtk-launch.
local function launch(id)
    local entry = quote(id .. ".desktop")
    return hl.dsp.exec_cmd("uwsm app -- " .. entry .. " 2>/dev/null || gtk-launch " .. quote(id))
end

local function dispatcher(name, args)
    local fn = hl.dsp
    for part in name:gmatch("[^.]+") do
        fn = fn[part]
    end
    if args ~= nil then
        return fn(args)
    end
    return fn()
end

local function bind(chord, action, entry)
    local opts = { description = entry.help }
    for flag, value in pairs(entry.opts or {}) do
        opts[flag] = value
    end
    hl.bind(chord, action, opts)
end

local help = {}

for _, entry in ipairs(keys.binds) do
    if entry.workspaces then
        for i, code in ipairs(keys.number_row) do
            local action
            if entry.workspaces == "move" then
                action = hl.dsp.window.move({ workspace = i })
            else
                action = hl.dsp.focus({ workspace = i })
            end
            bind(entry.keys .. " + " .. code, action, entry)
        end
    elseif entry.ipc then
        bind(entry.keys, hl.dsp.exec_cmd("noctalia msg " .. entry.ipc), entry)
    elseif entry.app then
        bind(entry.keys, launch(apps[entry.app]), entry)
    else
        bind(entry.keys, dispatcher(entry.dsp, entry.args), entry)
    end
    help[#help + 1] = (entry.label or entry.keys) .. "\t" .. entry.help
end

-- The help file is rewritten at each config load; failing to write it never stops the binds.
local runtime = os.getenv("XDG_RUNTIME_DIR")
if runtime and runtime ~= "" then
    os.execute("mkdir -p " .. quote(runtime .. "/corsu"))
    local file = io.open(runtime .. "/corsu/hypr-keys.tsv", "w")
    if file then
        file:write(table.concat(help, "\n"), "\n")
        file:close()
    end
end
