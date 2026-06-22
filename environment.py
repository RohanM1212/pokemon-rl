import gymnasium as gym
import numpy as np
import json
import os
from gymnasium import spaces

# path to the json file that rl_bridge.lua writes to
BRIDGE_FILE = "C:/Users/rmukh/Desktop/pokemon-accessibility-dev/battle_state.json"

class PokemonBattleEnv(gym.Env):

    def __init__(self, use_live_memory=True):
        super().__init__()

        self.use_live_memory = use_live_memory

        # 4 moves + switch + item
        self.action_space = spaces.Discrete(6)

        # what the agent sees each turn:
        # [player_hp, player_max_hp, enemy_hp, enemy_max_hp,
        #  player_level, enemy_level, move1_power, move2_power,
        #  move3_power, move4_power]
        self.observation_space = spaces.Box(
            low=0,
            high=255,
            shape=(10,),
            dtype=np.float32
        )

        self.player_hp = 0
        self.player_max_hp = 0
        self.enemy_hp = 0
        self.enemy_max_hp = 0
        self.player_level = 0
        self.enemy_level = 0
        self.moves = [40, 65, 60, 80]
        self.turn_count = 0
        self.max_turns = 50

    def _read_live_state(self):
        # reads from the json file rl_bridge.lua writes every 30 frames
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

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        if self.use_live_memory:
            # wait until mgba is in a battle
            if not self._read_live_state():
                print("waiting for battle in mgba...")
                while not self._read_live_state():
                    pass
                print("battle found, starting episode")
        else:
            # randomized fallback for testing without mgba
            self.player_level  = np.random.randint(5, 50)
            self.enemy_level   = np.random.randint(5, 50)
            self.player_max_hp = self.player_level * 3 + 10
            self.enemy_max_hp  = self.enemy_level * 3 + 10
            self.player_hp     = self.player_max_hp
            self.enemy_hp      = self.enemy_max_hp

        self.moves = [40, 65, 60, 80]
        self.turn_count = 0

        return self._get_observation(), {}

    def step(self, action):
        self.turn_count += 1
        reward = 0
        terminated = False
        truncated = False

        if self.use_live_memory:
            # agent picks an action but the game decides the actual damage
            # we just read what changed and reward based on that
            prev_enemy_hp  = self.enemy_hp
            prev_player_hp = self.player_hp

            self._read_live_state()

            damage_dealt = max(0, prev_enemy_hp - self.enemy_hp)
            damage_taken = max(0, prev_player_hp - self.player_hp)

            reward += damage_dealt / max(self.enemy_max_hp, 1) * 2
            reward -= damage_taken / max(self.player_max_hp, 1) * 1.5

        else:
            # simulated combat, same reward function logic
            if action < 4:
                move_power    = self.moves[action]
                damage_dealt  = max(1, int(move_power * self.player_level / (self.enemy_level * 2)))
                self.enemy_hp = max(0, self.enemy_hp - damage_dealt)
                reward += damage_dealt / self.enemy_max_hp * 2
            elif action == 4:
                # item use, heals a little but costs a turn
                heal = min(20, self.player_max_hp - self.player_hp)
                self.player_hp += heal
                reward -= 0.1
            elif action == 5:
                # switching costs a turn with no benefit here
                reward -= 0.2

            enemy_damage   = max(1, int(40 * self.enemy_level / (self.player_level * 2)))
            self.player_hp = max(0, self.player_hp - enemy_damage)
            reward -= enemy_damage / self.player_max_hp * 1.5

        if self.enemy_hp <= 0:
            reward += 10.0
            terminated = True
        elif self.player_hp <= 0:
            reward -= 10.0
            terminated = True
        elif self.turn_count >= self.max_turns:
            # penalty for dragging it out
            reward -= 2.0
            truncated = True

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
            self.moves[3]
        ], dtype=np.float32)

    def render(self):
        print(f"turn {self.turn_count}")
        print(f"player hp: {self.player_hp}/{self.player_max_hp} lv{self.player_level}")
        print(f"enemy hp:  {self.enemy_hp}/{self.enemy_max_hp} lv{self.enemy_level}")
        print("---")