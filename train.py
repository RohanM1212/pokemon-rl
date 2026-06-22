from environment import PokemonBattleEnv
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
import os

# check with simulation so mgba doesn't need to be open
check_env_instance = PokemonBattleEnv(use_live_memory=False)
print("Checking environment...")
check_env(check_env_instance)
print("Environment check passed.")

env = PokemonBattleEnv(use_live_memory=True)

model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    tensorboard_log="./logs/"
)

print("Starting training...")
model.learn(total_timesteps=100_000)

os.makedirs("models", exist_ok=True)
model.save("models/pokemon_battle_agent")
print("Training complete. Model saved.")

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