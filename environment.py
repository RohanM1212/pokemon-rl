import gymnasium as gym
import numpy as np
import json
import os
from gymnasium import spaces
import time

# path to the json file that rl_bridge.lua writes to
BRIDGE_FILE = "C:/Users/rmukh/Desktop/pokemon-accessibility-dev/battle_state.json"
ACTION_FILE = "C:/Users/rmukh/Desktop/pokemon-accessibility-dev/action.txt"

# type effectiveness chart pulled straight from the games data
# rows are attacker type, columns are defender type
# 0 = no effect, 0.5 = not very effective, 1 = normal, 2 = super effective
# only the types that actually show up in early hoenn routes
TYPE_CHART = {
    "normal":   {"normal": 1, "fire": 1, "water": 1, "grass": 1, "electric": 1, "ice": 1, "fighting": 1, "poison": 1, "ground": 1, "rock": 0.5, "ghost": 0, "dragon": 1},
    "fire":     {"normal": 1, "fire": 0.5, "water": 0.5, "grass": 2, "electric": 1, "ice": 2, "fighting": 1, "poison": 1, "ground": 1, "rock": 0.5, "ghost": 1, "dragon": 0.5},
    "water":    {"normal": 1, "fire": 2, "water": 0.5, "grass": 0.5, "electric": 1, "ice": 1, "fighting": 1, "poison": 1, "ground": 2, "rock": 2, "ghost": 1, "dragon": 0.5},
    "grass":    {"normal": 1, "fire": 0.5, "water": 2, "grass": 0.5, "electric": 1, "ice": 1, "fighting": 1, "poison": 0.5, "ground": 2, "rock": 2, "ghost": 1, "dragon": 0.5},
    "electric": {"normal": 1, "fire": 1, "water": 2, "grass": 0.5, "electric": 0.5, "ice": 1, "fighting": 1, "poison": 1, "ground": 0, "rock": 1, "ghost": 1, "dragon": 0.5},
    "fighting": {"normal": 2, "fire": 1, "water": 1, "grass": 1, "electric": 1, "ice": 2, "fighting": 1, "poison": 0.5, "ground": 1, "rock": 2, "ghost": 0, "dragon": 1},
}

# move data for the 4 starter moves
# [power, type] - power is base damage, type is used for effectiveness calc
MOVE_DATA = [
    (40, "normal"),   # move 1 - tackle/scratch/pound etc
    (65, "normal"),   # move 2
    (60, "water"),    # move 3 - water gun for mudkip etc
    (80, "normal"),   # move 4
]

def get_effectiveness(move_type, defender_type):
    # look up the multiplier, default to 1 if we don't have it
    if move_type in TYPE_CHART and defender_type in TYPE_CHART[move_type]:
        return TYPE_CHART[move_type][defender_type]
    return 1.0


class PokemonBattleEnv(gym.Env):

    def __init__(self, use_live_memory=True, reward_version=1):
        super().__init__()

        self.use_live_memory = use_live_memory

        # reward_version lets us swap between reward functions without rewriting the class
        # v1 = original, v2 = speed bonus, v3 = type effectiveness, v4 = HP preservation + tuned speed, with a tunable risk weight
        self.reward_version = reward_version

        # 4 moves + switch + item
        self.action_space = spaces.Discrete(4)

        # what the agent sees each turn:
        # [player_hp, player_max_hp, enemy_hp, enemy_max_hp,
        #  player_level, enemy_level, move1_power, move2_power,
        #  move3_power, move4_power, turns_remaining]
        self.observation_space = spaces.Box(
            low=0,
            high=1000,
            shape=(11,),
            dtype=np.float32
        )

        self.player_hp = 0
        self.player_max_hp = 0
        self.enemy_hp = 0
        self.enemy_max_hp = 0
        self.player_level = 0
        self.enemy_level = 0
        self.enemy_type = "normal"  # default, cant read from memory so we assume normal
        self.moves = [m[0] for m in MOVE_DATA]
        self.turn_count = 0
        self.max_turns = 50
        self.wins = 0
        self.losses = 0
        self.total_episodes = 0

    def _read_live_state(self):
        # reads from the json file rl_bridge.lua writes every 10 frames
        # returns False if the file doesn't exist or we're not in a battle
        try:
            with open(BRIDGE_FILE, 'r') as f:
                data = json.load(f)

            if data.get('in_battle') != 1:
                return False

            self.player_hp     = data['player_hp']
            self.player_max_hp = data['player_hp_max']
            self.player_level  = data['player_level']
            self.enemy_hp      = data['enemy_hp']
            self.enemy_max_hp  = data['enemy_hp_max']
            self.enemy_level   = data['enemy_level']
            return True

        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return False

    def _calculate_reward(self, action, damage_dealt, damage_taken, terminated, truncated):
        reward = 0

        if self.reward_version == 1:
            # v1 - original reward function
            # simple damage dealt vs damage taken, win/loss bonus
            reward += damage_dealt / max(self.enemy_max_hp, 1) * 2
            reward -= damage_taken / max(self.player_max_hp, 1) * 1.5

        elif self.reward_version == 2:
            # v2 - speed bonus added on top of v1
            # the faster we win the better, agent should learn to be aggressive
            # turns_remaining gives a bonus for winning early
            reward += damage_dealt / max(self.enemy_max_hp, 1) * 2
            reward -= damage_taken / max(self.player_max_hp, 1) * 1.5
            if terminated and self.enemy_hp <= 0:
                turns_remaining = self.max_turns - self.turn_count
                reward += turns_remaining * 0.1  # small bonus per turn saved

        elif self.reward_version == 3:
            # v3 - type effectiveness bonus on top of v2
            # agent should learn to use moves that hit harder based on type
            # this is the most interesting version because it requires the agent
            # to learn something about the game beyond just spamming the highest power move
            reward += damage_dealt / max(self.enemy_max_hp, 1) * 2
            reward -= damage_taken / max(self.player_max_hp, 1) * 1.5
            if terminated and self.enemy_hp <= 0:
                turns_remaining = self.max_turns - self.turn_count
                reward += turns_remaining * 0.1
            if action < 4:
                move_type = MOVE_DATA[action][1]
                effectiveness = get_effectiveness(move_type, self.enemy_type)
                if effectiveness > 1:
                    reward += 0.5  # bonus for landing a super effective hit
                elif effectiveness < 1:
                    reward -= 0.3  # penalty for using a not very effective move
        elif self.reward_version == 4:
            reward += (damage_dealt / max(self.enemy_max_hp, 1)) * 2
            reward -= (damage_taken / max(self.player_max_hp, 1)) * 1.5
            hp_weight = 5.86  # tunable risk knob: below this trends reckless, above it cautious
            if self.enemy_hp <= 0:
                reward += (self.max_turns - self.turn_count) / max(self.turn_count, 1)   # speed
                reward += (self.player_hp / max(self.player_max_hp, 1)) * hp_weight  # HP retention
            if action < 4:
                eff = get_effectiveness(MOVE_DATA[action][1], self.enemy_type)
                if eff > 1:   reward += 0.5
                elif eff < 1: reward -= 0.3

        # win/loss bonus is the same across all versions
        if self.enemy_hp <= 0:
            reward += 10.0
        elif self.player_hp <= 0:
            reward -= 10.0
        elif truncated:
            reward -= 2.0

        return reward

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        if self.use_live_memory:
            # wait until mgba is in a battle
            if not self._read_live_state():
                print("waiting for battle in mgba...")
                while not self._read_live_state():
                    time.sleep(0.1)
                print("battle found, starting episode")
        else:
            # randomized fallback for testing without mgba
            self.player_level  = np.random.randint(5, 50)
            self.enemy_level   = np.random.randint(5, 50)
            self.player_max_hp = self.player_level * 3 + 10
            self.enemy_max_hp  = self.enemy_level * 3 + 10
            self.player_hp     = self.player_max_hp
            self.enemy_hp      = self.enemy_max_hp

        self.moves = [m[0] for m in MOVE_DATA]
        self.turn_count = 0
        self.total_episodes += 1

        return self._get_observation(), {}

    def step(self, action):
        self.turn_count += 1
        terminated = False
        truncated = False
        damage_dealt = 0
        damage_taken = 0

        if self.use_live_memory:
            with open(ACTION_FILE, 'w') as f:
                f.write(str(action))

            # agent picks an action but the game decides the actual damage
            # we just read what changed and reward based on that
            prev_enemy_hp  = self.enemy_hp
            prev_player_hp = self.player_hp

            for i in range(100):
                self._read_live_state()
                if self.enemy_hp != prev_enemy_hp:
                    break
                time.sleep(0.1)

            damage_dealt = max(0, prev_enemy_hp - self.enemy_hp)
            damage_taken = max(0, prev_player_hp - self.player_hp)

        else:
            # simulated combat, same reward function logic
            if action < 4:
                move_power    = self.moves[action]
                move_type     = MOVE_DATA[action][1]
                effectiveness = get_effectiveness(move_type, self.enemy_type)
                damage_dealt  = max(1, int(move_power * self.player_level / (self.enemy_level * 2) * effectiveness))
                self.enemy_hp = max(0, self.enemy_hp - damage_dealt)
            elif action == 4:
                # item use, heals a little but costs a turn
                heal = min(20, self.player_max_hp - self.player_hp)
                self.player_hp += heal
            elif action == 5:
                # switching costs a turn with no benefit here
                pass

            enemy_damage   = max(1, int(40 * self.enemy_level / (self.player_level * 2)))
            self.player_hp = max(0, self.player_hp - enemy_damage)
            damage_taken   = enemy_damage

        if self.enemy_hp <= 0:
            terminated = True
            self.wins += 1
        elif self.player_hp <= 0:
            terminated = True
            self.losses += 1
        elif self.turn_count >= self.max_turns:
            # penalty for dragging it out
            truncated = True

        reward = self._calculate_reward(action, damage_dealt, damage_taken, terminated, truncated)

        if terminated or truncated:
            win_rate = self.wins / max(self.total_episodes, 1)
            print(f"episode {self.total_episodes} done | result: {'win' if self.enemy_hp <= 0 else 'loss'} | turns: {self.turn_count} | win rate: {win_rate:.2%}")

        return self._get_observation(), reward, terminated, truncated, {}

    def _get_observation(self):
        return np.array([
            self.player_hp,
            self.player_max_hp,
            self.enemy_hp,
            self.enemy_max_hp,
            self.player_level,
            self.enemy_level,
            self.moves[0],
            self.moves[1],
            self.moves[2],
            self.moves[3],
            self.max_turns - self.turn_count  # turns remaining so agent knows how much time it has
        ], dtype=np.float32)

    def render(self):
        print(f"turn {self.turn_count}")
        print(f"player hp: {self.player_hp}/{self.player_max_hp} lv{self.player_level}")
        print(f"enemy hp:  {self.enemy_hp}/{self.enemy_max_hp} lv{self.enemy_level}")
        print("---")