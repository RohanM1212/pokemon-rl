-- bridge.lua : connects mGBA's live battle memory to the Python RL env
-- reads battle state -> writes JSON for Python; reads Python's action -> presses buttons

local STATE_FILE  = "C:/Users/rmukh/Desktop/pokemon-accessibility-dev/battle_state.json"
local ACTION_FILE = "C:/Users/rmukh/Desktop/pokemon-accessibility-dev/action.txt"

-- read state from the memory
local function read_battle_state()
    local state = {}
    local raw = emu:read8(0x02024064)
    if raw == 2 then
        state.in_battle = 1
    else
        state.in_battle = 0
    end
    state.player_hp     = emu:read16(0x020240AC)
    state.player_hp_max = emu:read16(0x02024544)
    state.player_level  = emu:read8(0x02024540)
    state.enemy_hp      = emu:read16(0x0202479A)
    state.enemy_hp_max  = emu:read16(0x0202479C)
    state.enemy_level   = emu:read8(0x02024798)
    return state
end

-- write state to JSON file
local function write_state(state)
    local json = "{"
    json = json .. '"in_battle": '     .. tostring(state.in_battle)     .. ", "
    json = json .. '"player_hp": '     .. tostring(state.player_hp)     .. ", "
    json = json .. '"player_hp_max": ' .. tostring(state.player_hp_max) .. ", "
    json = json .. '"player_level": '  .. tostring(state.player_level)  .. ", "
    json = json .. '"enemy_hp": '      .. tostring(state.enemy_hp)      .. ", "
    json = json .. '"enemy_hp_max": '  .. tostring(state.enemy_hp_max)  .. ", "
    json = json .. '"enemy_level": '   .. tostring(state.enemy_level)
    json = json .. "}"

    local f = io.open(STATE_FILE, "w")
    f:write(json)
    f:close()
end

-- read and consume action
local function read_action()
    local f = io.open(ACTION_FILE, "r")
    if f == nil then
        return nil
    end
    local contents = f:read("a")
    f:close()
    os.remove(ACTION_FILE)        -- consume it so we never re-read a stale action
    return tonumber(contents)
end

-- map the actions to the button list
local function action_to_buttons(action)
    local buttons = {}
    table.insert(buttons, "A")       -- confirm FIGHT
    table.insert(buttons, "Up")      -- home the cursor to move 1
    table.insert(buttons, "Left")
    if action == 1 then
        table.insert(buttons, "Right")
    elseif action == 2 then
        table.insert(buttons, "Down")
    elseif action == 3 then
        table.insert(buttons, "Right")
        table.insert(buttons, "Down")
    end
    table.insert(buttons, "A")       -- confirm the move
    return buttons
end

-- read before act, one combined call back
local pending = {}
local press_index = 0
local frame = 0

callbacks:add("frame", function()
    frame = frame + 1

    -- read the state and write it every 10 frames
    if frame % 10 == 0 then
        local state = read_battle_state()
        if state.in_battle == 1 then
            write_state(state)
        end
    end

    -- act and load action only after done reading and writing (observing)
    if press_index == 0 or press_index > #pending then
        local action = read_action()
        if action ~= nil then
            pending = action_to_buttons(action)
            press_index = 1
        end
    end

    -- press one queued button, with spacing so inputs don't drop
    if press_index > 0 and press_index <= #pending then
        if frame % 3 == 0 then
            emu:addKey(pending[press_index])
            press_index = press_index + 1
        end
    end
end)