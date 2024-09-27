# 4x4 Rubik's Cube Solver (README in-progress)
This project applies the methodologies in [_Self-Supervision is All You Need for Solving Rubik's Cube_](https://arxiv.org/abs/2106.03157) to solve a harder challenge: the 4x4 Rubik's Cube.
## Usage
Run [main.py](main.py), or see the following example usage:
```python
from efficientcube import EfficientCube, utils

""" Specify scramble & search parameter """
scramble = "R2 F' R B D' B' U F2 B U2 B' U2 R2 L2 U2 F2 R2 B' U2 D Fw2 U' R Rw2 D F2 U2 L2 Fw2 L' Fw R2 F R U2 F' Uw2 B2 Rw Fw L2 Rw' Fw'"
beam_width = 2**13 # This parameter controls the trade-off between speed and quality

""" Set up solver, apply scramble, & solve """
solver = EfficientCube(
    env ="4x4",    # "3x3" or "4x4"
    model_path="auto",      # Automatically finds by `env` name
)
solver.apply_moves_to_env(scramble)
result = solver.solve(beam_width)

""" Verify the result """
if result is not None:
    print('\nSolution:', ' '.join(result['solutions']))
    print('\nLength:', len(result['solutions']))
    solver.reset_env()
    solver.apply_moves_to_env(scramble)

solver.apply_moves_to_env(result['solutions'])
assert solver.env_is_solved()

print("\nSimulator URL:", utils.generate_simulator_link(scramble, result['solutions']))
print()

else:
    print('Failed — try a longer beam width.')
```
## How It Works
### Terminology
| Term | Definition |
| --- | --- |
| Turn Metric | Defines the set of turns which count as a single turn.
| Quarter Turn Metric (QTM) | Any 90° turn of a single **_outer_** layer counts as one turn.
| Quarter Slice Turn Metric (QSTM) | Any 90° turn of any single layer (including inner layers) counts as one turn. This is the metric we use in our solution. |
| Outer Block Turn Metric (OBTM) | Any turn (90° or 180°) of an outer layer and adjacent inner layers counts as one turn. This is the official metric of the World Cubing Association, and is the usual metric we receive scrambles with. |
| God's Number | The minimum number of turns required to solve any cube state. God's Number for the 3x3 is 26 in QTM, but it is unknown for the 4x4. |
### The 3x3
In the original paper, the author uses a self-supervised learning approach to solve the 3x3 cube. In training, solved cubes are randomly scrambled with God's Number turns. The model is then trained on each intermediate state, labeled by the _turn applied to reach it_. This effectively teaches the model to recognize moves which bring the cube closer to the solved state. 

At first glance, this approach seems hopeful at best. After all, scrambling a cube by 1 turn doesn't uniformly take it to a state 1 turn further from the solution. Making a random turn could very well bring us closer to the solved state by any number of moves. However, _on average_, it takes us 1 move further. Therefore, if we run a large enough search from a scrambled cube, making the turns suggested by our model will yield states closer and closer to the solved state. Though this is quite informal logic, in practice we can observe that it works extremely well. In the paper, every tested scramble was successfully solved.
### The 4x4
Unfortunately, copying the above approach does not work on the 4x4. This is for two reasons.

First, the 4x4 is massively more complex than the 3x3. It has over $10^{49}$ permutations, compared to the 3x3's mere $10^{19}$. Further, each state is itself more complex; the 4x4 has 56 pieces, compared to 26 on the 3x3. Given these facts, I found that my model was unable to differentiate between states at the end of a training scramble. It could not reliably predict the right move to convert a state that is, for example, 54 moves away to a state 53 moves away.

Second, God's Number for the 4x4 is (likely) too large for an effective beam search. Current upper bounds are around 55 turns in OBTM, but a depth of 55 in a beam search will, without doubt, fail. This is because, while our search gradually uncovers positions closer and closer to the solved state, this is only possible with a large enough 
### My Solution
Instead of trying to solve the entire 4x4 all at once, we transform it into an intermediate state that we **_know_** is closer to solved. There are many ways to do this, but out of everything I tested, the best way is to reduce it into a 3x3—which we know is only 26 turns from solved! 
![4x4 -> 3x3](https://www.speedcube.com.au/cdn/shop/articles/4x4_reduction_blogimage_280ef415-0606-48fc-8c44-52f1741d26a9.png?v=1723097078)
In particular, we need to group all the center pieces and pair all the edges. In my initial tests, training models for the two steps separately (centers first, then edges) turned out to be an easy task. Next, I tried a single model on the entire reduction task. With correct hyperparameters, this yielded results after ~10,000 training scrambles. However, when running inference, I noticed something strange. The model seemed to be working, and .  As I eventually figured out, that's because I had missed a crucial detail: parity.
### Parity
As it turns out, simply solving centers and pairing edges does not correctly reduce a 4x4 to a 3x3. This is because our reduction has essentially generated a random 3x3 state. Unfortunately, most states are not solvable! There are 3 invariants that every solvable cube satisfies: corner, edge, and permutation parity. These invariants invalidate 2/3, 1/2, and 1/2 of states respectively. As a result of this, most reduced cubes my model was finding were actually unsolvable. 

Since the original 3x3 model worked out-of-the-box on the reduction task, fixing parity issues became the main challenge of this project. I wrote methods to check each parity type, and also methods to directly scramble centers, edges, and corners separately. These allowed me to generate any type of scramble (fully scrambled, reduced form, only centers solved, etc.) in O(1) time, which sped up many tests.
## Results
This model successfully solves nearly every scramble it is given. While it fails on occassion given very long scrambles (1000+ turns), it has a 100% success rate on the standard 40-move scrambles used for human competitions.

The following chart displays the result of trials with 100 solves, each scrambled for 1000 turns.
| Beam Width | Success Rate | Average Solution Length |
| :---: | :---: | :---: |
| $2^{11}$ | 69% | 61.6 turns |
| $2^{13}$ | 98% | 57.4 turns |
| $2^{15}$ | 100% | 53.4 turns |
