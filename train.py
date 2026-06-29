from environment import PokemonBattleEnv
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
import os

# check with simulation so mgba doesn't need to be open
check_env_instance = PokemonBattleEnv(use_live_memory=False)
print("Checking environment...")
check_env(check_env_instance)
print("Environment check passed.")

# change reward_version here to test different reward functions
# v1 = original, v2 = speed bonus, v3 = type effectiveness
# document what happens with each version in devlog/
REWARD_VERSION = 4

env = PokemonBattleEnv(use_live_memory=True, reward_version=REWARD_VERSION)

model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    tensorboard_log="./logs/"
)

print(f"Starting training with reward version {REWARD_VERSION}...")
model.learn(total_timesteps=100_000)

os.makedirs("models", exist_ok=True)
model.save(f"models/pokemon_battle_agent_v{REWARD_VERSION}")
print(f"Training complete. Model saved as pokemon_battle_agent_v{REWARD_VERSION}.")

print("\nTesting trained agent...")
obs, _ = env.reset()
total_reward = 0
for i in range(200):
    action, _ = model.predict(obs)
    obs, reward, terminated, truncated, _ = env.step(action)
    total_reward += reward
    env.render()
    if terminated or truncated:
        print(f"Battle ended. Total reward: {total_reward:.2f}")
        obs, _ = env.reset()
        total_reward = 0