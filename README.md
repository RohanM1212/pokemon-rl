# Pokemon RL

Teaching a reinforcement learning agent to play Pokemon Emerald using real game memory.

---

## What is this?

A reinforcement learning project where an agent learns to play Pokemon Emerald battles by reading live game memory through mGBA and making decisions using a reward function I designed from scratch.

The interesting part is not the Pokemon. It is the reward function design. Designing a reward function that produces smart, intentional behavior is the same core problem you face when programming autonomous robots to navigate, make decisions, and complete tasks in the real world. This project is practice for that.

---

## How it works

The agent uses a Gym environment I built that wraps Pokemon Emerald battle state. It reads player HP, enemy HP, levels, and move powers directly from game memory every frame. The agent picks from 6 actions each turn: 4 moves, use item, or switch. It gets rewarded for dealing damage, penalized for taking damage, and heavily rewarded or penalized for winning or losing.

Training uses PPO from stable-baselines3, which is the standard starting point for this type of problem.

---

## Files

**environment.py** defines the Gym environment. This is where the reward function lives and where every design decision about what the agent should optimize for gets made. It also holds the type effectiveness chart pulled directly from the game data, which the agent uses starting in reward version 3.

**train.py** creates the agent, runs training, saves the model, and tests it. Change the REWARD_VERSION variable at the top to switch between reward functions without touching anything else.

**bridge.lua** runs inside mGBA. It reads live battle state from memory every 30 frames, writes it to a JSON file, and translates the agent's action choices into actual button presses in the game.

---

## Reward Function Design

The reward function is the most important part of this project and the hardest part to get right.

I built three versions. The first was a naive baseline that taught the agent to fight but gave it no concept of time. A win in 3 turns looked identical to a win in 49 turns. The second added a speed bonus and made the agent aggressive, but it became reckless, tanking hits it should have avoided just to end fights faster. The third added type effectiveness from the actual game data and is where the agent finally started making context-dependent decisions instead of just spamming the highest power move.

Every version is documented in the devlog folder. The failed versions are as useful as the working ones because they show exactly what the agent optimizes for when you are not careful enough about what you are asking it to do.

---

## Robotics Connection

Reward function design is reward function design regardless of whether you are training an agent to play Pokemon or training a robot to navigate a warehouse. In both cases you are answering the same question: what does good behavior look like, and how do you express that mathematically so a learning algorithm can figure it out on its own?

See ROBOTICS.md for the full writeup on how this connects to autonomous systems research.

---

## Status

Environment, training pipeline, and mGBA memory bridge are working. Three reward function versions complete and documented. Demo video coming.

---

## Built with

Python, stable-baselines3, Gymnasium, mGBA scripting bridge

---

## Related

- [pokemon-emerald-accessibility](https://github.com/RohanM1212/pokemon-emerald-accessibility) — Accessibility scripts for the same game built with the same memory reading approach
- [arduino-junior-certification-journey](https://github.com/RohanM1212/arduino-junior-certification-journey) — The embedded systems learning that led here