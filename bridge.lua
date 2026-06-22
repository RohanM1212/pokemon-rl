--[[
    rl_bridge.lua
    reads live battle state from memory and writes it to a json file
    so environment.py can train on real game data instead of a simulation

    how to use:
    1. open mgba with pokemon emerald loaded
    2. go to tools > scripting and load this file
    3. run environment.py with use_live_memory=True
    4. start a battle and it will pick up automatically

    addresses were found by scanning memory during live battles
    on the usa, europe rom (game code bpee)
--]]

-- change output_file if your folder is different
-- set debug to false once you know it's working
local CONFIG = {
    output_file    = "C:/Users/rmukh/Desktop/pokemon-accessibility-dev/battle_state.json",
    write_interval = 30,  -- every 30 frames, twice per second
    debug          = true,
}

-- all addresses confirmed by live memory scanning
-- player hp is dynamic in iwram so we use the battle struct in ewram instead
local ADDR = {
    player_hp_current = 0x020240AC,  -- 16-bit
    player_hp_max     = 0x02024544,  -- 16-bit
    player_level      = 0x02024540,  -- 8-bit
    enemy_hp_current  = 0x0202479A,  -- 16-bit
    enemy_hp_max      = 0x0202479C,  -- 16-bit
    enemy_level       = 0x02024798,  -- 8-bit
    game_state        = 0x02024064,  -- 8-bit, 2 = in battle, 0 = overworld
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

local frame_count = 0

callbacks:add("frame", function()
    frame_count = frame_count + 1
    if frame_count % CONFIG.write_interval == 0 then
        write_battle_state()
    end
end)

console:log("rl bridge loaded")
console:log("writing to: " .. CONFIG.output_file)