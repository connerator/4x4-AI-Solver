# 4x4 Rubik's Cube Solver (README in-progress)
This project applies the methodologies in ___ to solve a harder challenge: the 4x4 Rubik's Cube.
## Usage
Run [main.py](main.py)
## How It Works
### The 3x3
In the original paper, the author uses a self-supervised learning approach to solve the 3x3 cube. In training, solved cubes are randomly scrambled until reaching a uniformly random state (in practice, this takes ~40 turns, twice God's Number). The model is then trained on each intermediate state, labeled by the _turn applied to reach it_. This effectively teaches the model to recognize moves which bring the cube closer to the solved state. 

At first glance, this approach seems hopeful at best. After all, scrambling a cube by 1 turn doesn't uniformly take it to a state 1 turn further from the solution. Making a random turn could very well bring us closer to the solved state by any number of moves. However, _on average_, it takes us 1 move further. Therefore, if we run a large enough search from a scrambled cube, making the turns suggested by our model will yield states closer and closer to the solved state. Though this is quite informal logic, in practice we can observe that it works extremely well. On the 3x3, every tested state was solved.
### The 4x4
Unfortunately, copying the above approach does not work on the 4x4. This is for two reasons.

First, the 4x4 is massively more complex than the 3x3. It has over $10^{49}$ permutations, compared to the 3x3's mere $10^{19}$. Further, each state is itself more complex; the 4x4 has 56 pieces, compared to 26 on the 3x3. Given these facts, I found that my model was unable to differentiate between states at the end of a training scramble. It could not reliably predict the right move to convert a state that is, for example, 54 moves away to a state 53 moves away.

Second, God's Number is too large for an effective beam search. ____

