from environment import PokemonBattleEnv
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
import os

# Create the environment
env = PokemonBattleEnv()

# Check that the environment follows gymnasium rules correctly
print("Checking environment...")
check_env(env)
print("Environment check passed.")

# Create the PPO agent
# This is the AI that will learn to play Pokemon battles
model = PPO(
    "MlpPolicy",    # Multi-layer perceptron - standard neural network
    env,
    verbose=1,      # Print training progress
    tensorboard_log="./logs/"  # Save training data for visualization
)

# Train the agent
# 100,000 timesteps is a quick test run - real training uses 1,000,000+
print("Starting training...")
model.learn(total_timesteps=100_000)

# Save the trained model
os.makedirs("models", exist_ok=True)
model.save("models/pokemon_battle_agent")
print("Training complete. Model saved.")

# Test the trained agent
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