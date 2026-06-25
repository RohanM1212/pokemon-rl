--[[
    rl_bridge.lua
    reads live battle state from memory and writes it to a json file
    also reads actions from action.txt and presses the right buttons
    so the agent actually controls the game instead of just watching

    how to use:
    1. open mgba with pokemon emerald loaded
    2. go to tools > scripting and load this file
    3. run environment.py with use_live_memory=True
    4. start a battle and it will pick up automatically

    addresses were found by scanning memory during live battles
    on the usa, europe rom (game code bpee)
--]]

-- change output_file and action_file if your folder is different
-- set debug to false once you know it's working
local CONFIG = {
    output_file    = "C:/Users/rmukh/Desktop/pokemon-accessibility-dev/battle_state.json",
    action_file    = "C:/Users/rmukh/Desktop/pokemon-accessibility-dev/action.txt",
    write_interval = 30,
    press_duration = 8,
    debug          = true,
}

-- all addresses confirmed by live memory scanning
-- player hp is dynamic in iwram so we use the battle struct in ewram instead
local ADDR = {
    player_hp_current = 0x020240AC,
    player_hp_max     = 0x02024544,
    player_level      = 0x02024540,
    enemy_hp_current  = 0x0202479A,
    enemy_hp_max      = 0x0202479C,
    enemy_level       = 0x02024798,
    game_state        = 0x02024064,
}

-- gba button values for emu:setKeys()
-- each button is a bit in a bitmask
local BUTTONS = {
    A      = 0x0001,
    B      = 0x0002,
    SELECT = 0x0004,
    START  = 0x0008,
    RIGHT  = 0x0010,
    LEFT   = 0x0020,
    UP     = 0x0040,
    DOWN   = 0x0080,
}

-- action number from environment.py maps to a button sequence
-- UP+LEFT resets the cursor to move 1 before every action
-- 0 = move 1, 1 = move 2, 2 = move 3, 3 = move 4, 4 = item, 5 = run
local ACTION_MAP = {
    [0] = {BUTTONS.UP + BUTTONS.LEFT, BUTTONS.A},
    [1] = {BUTTONS.UP + BUTTONS.LEFT, BUTTONS.DOWN, BUTTONS.A},
    [2] = {BUTTONS.UP + BUTTONS.LEFT, BUTTONS.RIGHT, BUTTONS.A},
    [3] = {BUTTONS.UP + BUTTONS.LEFT, BUTTONS.DOWN + BUTTONS.RIGHT, BUTTONS.A},
    [4] = {BUTTONS.UP + BUTTONS.LEFT, BUTTONS.DOWN, BUTTONS.DOWN, BUTTONS.A},
    [5] = {BUTTONS.UP + BUTTONS.LEFT, BUTTONS.A},
}

local function read16(addr)
    return emu:read16(addr)
end

local function read8(addr)
    return emu:read8(addr)
end

local function write_battle_state()
    local player_hp     = read16(ADDR.player_hp_current)
    local player_hp_max = read16(ADDR.player_hp_max)
    local player_level  = read8(ADDR.player_level)
    local enemy_hp      = read16(ADDR.enemy_hp_current)
    local enemy_hp_max  = read16(ADDR.enemy_hp_max)
    local enemy_level   = read8(ADDR.enemy_level)
    local battle        = read8(ADDR.game_state) == 2 and 1 or 0

    local json = string.format(
        '{"in_battle":%d,"player_hp":%d,"player_hp_max":%d,"player_level":%d,"enemy_hp":%d,"enemy_hp_max":%d,"enemy_level":%d}',
        battle, player_hp, player_hp_max, player_level,
        enemy_hp, enemy_hp_max, enemy_level
    )

    local f = io.open(CONFIG.output_file, "w")
    if f then
        f:write(json)
        f:close()
    end

    if CONFIG.debug then
        console:log(string.format(
            "[bridge] battle:%d | player hp:%d/%d lv%d | enemy hp:%d/%d lv%d",
            battle, player_hp, player_hp_max, player_level,
            enemy_hp, enemy_hp_max, enemy_level
        ))
    end
end

-- input injection state
local current_action    = nil
local action_queue      = {}
local press_frames_left = 0

local function read_action()
    -- python writes a single number to action.txt
    -- we read it, delete it so we don't repeat it, and queue the button presses
    local f = io.open(CONFIG.action_file, "r")
    if not f then return end
    local line = f:read("*l")
    f:close()

    local action = tonumber(line)
    if action == nil then return end

    -- clear the file so we don't read the same action twice
    local fw = io.open(CONFIG.action_file, "w")
    if fw then fw:close() end

    -- get the button sequence for this action
    local seq = ACTION_MAP[action]
    if seq then
        action_queue = {}
        for i = 1, #seq do
            action_queue[i] = seq[i]
        end
        if CONFIG.debug then
            console:log("[bridge] action received: " .. action)
        end
    end
end

local function process_input()
    -- if there are buttons left in the queue, press the next one
    if press_frames_left > 0 then
        press_frames_left = press_frames_left - 1
        if press_frames_left == 0 then
            emu:setKeys(0)
        end
        return
    end

    if #action_queue > 0 then
        local next_button = table.remove(action_queue, 1)
        emu:setKeys(next_button)
        press_frames_left = CONFIG.press_duration
    end
end

local frame_count = 0

callbacks:add("frame", function()
    frame_count = frame_count + 1

    -- read new action from python every 30 frames
    if frame_count % CONFIG.write_interval == 0 then
        write_battle_state()
        read_action()
    end

    -- process button presses every frame so they feel responsive
    process_input()
end)

console:log("rl bridge loaded")
console:log("writing to: " .. CONFIG.output_file)
console:log("reading actions from: " .. CONFIG.action_file)