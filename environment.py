import gymnasium as gym
import numpy as np
from gymnasium import spaces

class PokemonBattleEnv(gym.Env):
    """
    A simplified Pokemon battle environment for reinforcement learning.
    
    The agent learns to win Pokemon battles by selecting moves strategically.
    This connects directly to robotics: the same reward function design principles
    apply to teaching robots to navigate, grasp objects, and make decisions.
    """
    
    def __init__(self):
        super().__init__()
        
        # Action space: 4 moves + switch + item = 6 possible actions
        # This is like telling a robot: you can move forward, back, left, right, grab, release
        self.action_space = spaces.Discrete(6)
        
        # Observation space: what the agent sees each turn
        # [player_hp, player_max_hp, enemy_hp, enemy_max_hp, 
        #  player_level, enemy_level, move1_power, move2_power, 
        #  move3_power, move4_power]
        self.observation_space = spaces.Box(
            low=0,
            high=255,
            shape=(10,),
            dtype=np.float32
        )
        
        # Battle state
        self.player_hp = 0
        self.player_max_hp = 0
        self.enemy_hp = 0
        self.enemy_max_hp = 0
        self.player_level = 0
        self.enemy_level = 0
        self.moves = [0, 0, 0, 0]  # power of each move
        self.turn_count = 0
        self.max_turns = 50  # battles cant go forever
        
    def reset(self, seed=None, options=None):
        """
        Start a new battle. Returns the initial observation.
        Called at the beginning of every episode.
        """
        super().reset(seed=seed)
        
        # Initialize a random battle scenario
        # Later this will read from actual Pokemon Emerald memory
        self.player_level = np.random.randint(5, 50)
        self.enemy_level = np.random.randint(5, 50)
        self.player_max_hp = self.player_level * 3 + 10
        self.enemy_max_hp = self.enemy_level * 3 + 10
        self.player_hp = self.player_max_hp
        self.enemy_hp = self.enemy_max_hp
        self.moves = [40, 65, 60, 80]  # typical move powers
        self.turn_count = 0
        
        return self._get_observation(), {}
    
    def step(self, action):
        """
        Take one action in the battle.
        Returns: observation, reward, terminated, truncated, info
        """
        self.turn_count += 1
        reward = 0
        terminated = False
        truncated = False
        
        # Agent selects a move (actions 0-3)
        if action < 4:
            move_power = self.moves[action]
            
            # Calculate damage dealt to enemy
            damage_dealt = max(1, int(move_power * self.player_level / (self.enemy_level * 2)))
            self.enemy_hp = max(0, self.enemy_hp - damage_dealt)
            
            # Small reward for dealing damage
            reward += damage_dealt / self.enemy_max_hp * 2
            
        # Agent tries to use item (action 4) - simplified, just heals a little
        elif action == 4:
            heal = min(20, self.player_max_hp - self.player_hp)
            self.player_hp += heal
            reward -= 0.1  # slight penalty for using items instead of attacking
            
        # Agent tries to switch (action 5) - simplified, costs a turn
        elif action == 5:
            reward -= 0.2  # penalty for switching when not necessary
        
        # Enemy attacks back with random damage
        enemy_damage = max(1, int(40 * self.enemy_level / (self.player_level * 2)))
        self.player_hp = max(0, self.player_hp - enemy_damage)
        
        # Give reward for taking less damage
        reward -= enemy_damage / self.player_max_hp * 1.5
        
        # Check win condition
        if self.enemy_hp <= 0:
            reward += 10.0  # big reward for winning
            terminated = True
            
        # Check loss condition
        elif self.player_hp <= 0:
            reward -= 10.0  # big penalty for losing
            terminated = True
            
        # Check turn limit
        elif self.turn_count >= self.max_turns:
            reward -= 2.0  # penalty for dragging out the battle
            truncated = True
            
        return self._get_observation(), reward, terminated, truncated, {}
    
    def _get_observation(self):
        """
        Returns the current game state as a numpy array.
        This is everything the agent gets to see when making decisions.
        """
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
        """
        Prints current battle state to console.
        Useful for watching the agent play.
        """
        print(f"Turn {self.turn_count}")
        print(f"Player HP: {self.player_hp}/{self.player_max_hp}")
        print(f"Enemy HP:  {self.enemy_hp}/{self.enemy_max_hp}")
        print("---")