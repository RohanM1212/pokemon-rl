# What is environment.py?

This is where the heart of the project lives. This class is what connects the PPO to the battle. It defines what the agent can see (the observation space), what it can do (the action space), and calculates the rewards after each turn is over.

## The turn-sync bug

Originally, the step function read the result, which bridge.lua writes to the file, immediately after sending the action to the file that bridge.lua reads. The issue is, bridge.lua actually takes a couple of seconds to input the action and play the turn, because there is dialogue between moves and because the inputs to get to the actions aren't instant. This way, the Python script would read 0 damage, as if nothing had changed, but the truth is that the Lua script just isn't done yet. To fix this, I decided to have it repeatedly check for a change in HP for a certain number of tries, and if there's no change in HP in the allotted time, the code assumes no damage was done. The allotted time is long enough for the Lua to write the change to the file. This also works for non-damaging moves, because we aren't tracking status conditions yet.

## Bugs

I changed the action space from 6 to 4 because we don't have switch Pokémon and bag programmed yet. I had also previously limited the HP to 255, but in Pokémon HP can go much higher than 255, so I increased the limit to 1000. Also, instead of having reset check every frame whether it's in battle or not, I changed it to sleep for small amounts of time between checks to be kinder to the CPU.

## Known Limitations

The enemy type is hardcoded as normal because I haven't found the memory address that corresponds to the typing of the opponent yet. Right now, the typing bonus in reward v3/v4 is useless because of this. I will try to fix it in the future. I also haven't created a way to handle dialogue during battles yet, which is something I am working on.

## Robotics

In reinforcement learning, simulations are necessary because training with real-life data, so real battles in this case, would take much too long. This is why most of the training of the agent is done with sims and the fine-tuning comes from actual battles and experience. The same thing happens when training real-life robots. They are trained on simulations first and the fine-tuning comes from real-life training. One caveat that comes with training in simulations is that the conditions of the simulation are almost never identical to real life, so we have to add some random elements to try and make up for that limitation. Another thing in real robot training is that it takes much longer, even in simulations, for a real robot to train compared to an agent training on Pokémon battles. This means they also need to maximize the learning that comes from every mistake and massively speed up the simulations. How to bridge this gap and do this more efficiently is still being researched.