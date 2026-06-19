# Pokemon RL

Teaching a reinforcement learning agent to play Pokemon Emerald using real game memory.

---

## What is this?

A reinforcement learning project where an AI agent learns to play Pokemon Emerald battles by reading live game memory through mGBA and making decisions using a reward function I designed from scratch.

The interesting part is not the Pokemon. It is the reward function design. Designing a reward function that produces smart, intentional behavior is the same core problem you face when programming autonomous robots to navigate, make decisions, and complete tasks in the real world. This project is practice for that.

---

## How it works

The agent uses a Gym environment I built that wraps Pokemon Emerald battle state. It reads player HP, enemy HP, levels, and move powers directly from game memory every frame. The agent picks from 6 actions each turn: 4 moves, use item, or switch. It gets rewarded for dealing damage, penalized for taking damage, and heavily rewarded or penalized for winning or losing.

Training uses PPO from stable-baselines3, which is the standard starting point for this type of problem.

---

## Files

**environment.py** defines the Gym environment. This is where the reward function lives. Every design decision about what the agent should optimize for is in here.

**train.py** creates the agent, runs training, saves the model, and tests it.

---

## Reward Function Design

The reward function is the most important part of this project and the hardest part to get right.

Current design:
- Dealing damage: positive reward scaled by percentage of enemy HP removed
- Taking damage: negative reward scaled by percentage of player HP lost
- Winning the battle: +10
- Losing the battle: -10
- Using items instead of attacking: small penalty
- Switching when not needed: small penalty
- Battle going too long: penalty for dragging it out

Every version of the reward function that failed is documented in the devlog folder. Failed reward functions are as useful as successful ones because they show exactly what the agent optimizes for when you are not careful enough.

---

## Robotics Connection

The reason this connects to robotics is that reward function design is reward function design regardless of whether you are training an agent to play Pokemon or training a robot to navigate a warehouse.

In both cases you are answering the same question: what does good behavior look like, and how do you express that mathematically so a learning algorithm can figure it out on its own?

This project is my way of getting real experience with that problem before I get to work on physical systems.

---

## Status

Environment and training pipeline are working. Currently connecting to live mGBA memory so the agent trains on real game state instead of a simulated environment. Robotics writeup in progress.

---

## Built with

Python, stable-baselines3, Gymnasium, mGBA scripting bridge

---

## Related

- [pokemon-emerald-accessibility](https://github.com/RohanM1212/pokemon-emerald-accessibility) — Accessibility scripts for the same game built with the same memory reading approach
- [arduino-junior-certification-journey](https://github.com/RohanM1212/arduino-junior-certification-journey) — The embedded systems learning that led here