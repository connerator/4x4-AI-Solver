"""
This module contains class implementations for three environments:
- Rubik's Cube: Cube3
- 15 Puzzle: Puzzle15
- Lights Out: LightsOut7

Please note that we prioritize readability and reproducibility over speed optimization in this repository.
"""

import random
import numpy as np


class Cube4:

    def __init__(self):
        self.DTYPE = np.int64
        self.reset()
        self.goal = np.arange(0, 16 * 6, dtype=self.DTYPE) // 16

        faces = ["U", "D", "L", "R", "B", "F"]
        degrees = ["", "'"]
        widths = ["1", "2"]
        degrees_inference = degrees[::-1]
        self.moves = [f"{w}{f}{n}" for w in widths for f in faces for n in degrees]
        self.moves_inference = [f"{w}{f}{n}" for w in widths for f in faces for n in degrees_inference]

        self.pairing = {
            "R": "L",
            "L": "R",
            "F": "B",
            "B": "F",
            "U": "D",
            "D": "U",
        }
        self.rotations = {
            'x': "1R 2R 1L' 2L'",
            'y': "1U 2U 1D' 2D'",
            'z': "1F 2F 1B' 2B'"
        }
        self.rotation_scrambles = [i + " " + j for i in ["", "1L 2L 1R' 2R'", "1L 2L 1R' 2R' 1L 2L 1R' 2R'", "1L' 2L' 1R 2R", "1U 2U 1D' 2D'", "1U' 2U' 1D 2D"] for j in ["", "1F 2F 1B' 2B'", "1F 2F 1B' 2B' 1F 2F 1B' 2B'", "1F' 2F' 1B 2B"]]

        # Prohibit obviously redundant moves.
        self.moves_available_after = {
            m: [v for v in self.moves if v[1] != m[1]] + [m]
            for m in self.moves
        } # self-cancelling moves on the same face

        # [OPTIMIZATION] slicing by move string (e.g., R', U, F) => indices (e.g., 2, 6, 1)
        self.moves_ix = [self.moves.index(m) for m in self.moves]
        self.moves_ix_available_after = {
            self.moves.index(m): [self.moves.index(m) for m in available_moves]
            for m, available_moves in self.moves_available_after.items()
        }

        self.moves_ix_inference = [self.moves.index(m) for m in self.moves_inference]
        self.pairing_ix = {
            0: 1,
            1: 0,
            2: 3,
            3: 2,
            4: 5,
            5: 4,
        } # Points to the opposite face index

        # Vectorize the sticker group replacement operations
        self.__vectorize_moves()

    def __str__(self):
        """Returns a string representation of the cube."""
        a = ""
        for i in range(0, 4):
            a += "         "
            for j in range(0, 4):
                a += str(self.state[4*i + j]) + " "
            a += "\n"
        a += "\n"
        for b in range(0, 4):
            for i in range(1, 5):
                for j in range(0, 4):
                    a += str(self.state[16*i + 4*b + j]) + " "
                a += " "
            a += "\n"
        a += "\n"
        for i in range(0, 4):
            a += "         "
            for j in range(0, 4):
                a += str(self.state[80 + 4*i + j]) + " "
            a += "\n"


        return a

    def reset(self, train=False):
      """Resets the cube to the solved state. If train mode is on, then solved states are defined as reduced 3x3 states. """
      self.state = np.arange(0, 16 * 6, dtype=self.DTYPE) // 16
      if train:
        self.scramble_corners()
        self.scramble_edges(paired=True)
        self.rotate_randomly()

    def is_solved(self):
        """Checks if the cube is in the solved state."""
        return self.are_centers_solved() and self.are_edges_solved() and self.paired_edge_parity() == 0 and self.permutation_parity() == 0

    def are_centers_solved(self):
        """Checks if center pieces are matching each other on every side."""
        center_indices = np.array([5, 6, 9, 10, 21, 22, 25, 26, 37, 38, 41, 42, 53, 54, 57, 58, 69, 70, 73, 74, 85, 86, 89, 90])
        return np.all([np.all(self.state[center_indices[4*i:4*i+4]] == self.state[center_indices[4*i]]) for i in range(6)])

    def are_edges_solved(self):
        """Checks if edge pieces are matching each other in each slot."""
        edge_indices = np.array([[13, 33], [14, 34], [23, 36], [39, 52], [27, 40], [43, 56], [45, 81], [46, 82], [8, 18], [11, 49], [30, 84], [61, 87], [4, 17], [7, 50], [29, 88], [62, 91], [66, 1], [65, 2], [68, 55], [71, 20], [72, 59], [75, 24], [78, 93], [77, 94]])
        edge_pairs = np.array([[0, 1], [2, 4], [3, 5], [6, 7], [8, 12], [9, 13], [10, 14], [11, 15], [16, 17], [18, 20], [19, 21], [22, 23]])
        return np.all([self.state[edge_indices[pair[0]][0]] == self.state[edge_indices[pair[1]][0]] and self.state[edge_indices[pair[0]][1]] == self.state[edge_indices[pair[1]][1]] for pair in edge_pairs])

    def scramble_centers(self):
        """Scramble the center pieces."""
        indices = np.array([5, 6, 9, 10, 21, 22, 25, 26, 37, 38, 41, 42, 53, 54, 57, 58, 69, 70, 73, 74, 85, 86, 89, 90])
        colors = np.array([0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5])

        np.random.shuffle(colors)
        self.state[indices] = colors

    def scramble_edges(self, paired=False):
        """Scramble the edge pieces. If paired mode is on, edge pairs are kept intact and scrambled together, maintaining edge and permutation parity."""
        indices = np.array([[13, 33], [14, 34], [23, 36], [39, 52], [27, 40], [43, 56], [45, 81], [46, 82], [8, 18], [11, 49], [30, 84], [61, 87], [4, 17], [7, 50], [29, 88], [62, 91], [66, 1], [65, 2], [68, 55], [71, 20], [72, 59], [75, 24], [78, 93], [77, 94]])
        colors = np.array([[0, 1], [0, 2], [0, 3], [0, 4], [1, 0], [1, 2], [1, 4], [1, 5], [2, 0], [2, 1], [2, 3], [2, 5], [3, 0], [3, 2], [3, 4], [3, 5], [4, 0], [4, 1], [4, 3], [4, 5], [5, 1], [5, 2], [5, 3], [5, 4]])
        edge_pairs = np.array([[0, 1], [2, 4], [3, 5], [6, 7], [8, 12], [9, 13], [10, 14], [11, 15], [16, 17], [18, 20], [19, 21], [22, 23]])


        if paired:
          while True:
              indices2 = np.array([[13, 33], [23, 36], [39, 52], [45, 81], [8, 18], [11, 49], [30, 84], [61, 87], [66, 1], [68, 55], [71, 20], [78, 93]])
              colors2 = np.array([[0, 1], [0, 2], [0, 3], [0, 4], [1, 2], [1, 4], [1, 5], [2, 3], [2, 5], [3, 4], [3, 5], [4, 5]])
              [np.random.shuffle(i) for i in colors2]
              np.random.shuffle(colors2)
              self.state[indices2] = colors2
              for pair in edge_pairs:
                self.state[indices[pair[1]]] = self.state[indices[pair[0]]]

              if self.paired_edge_parity() == 1:
                rand_pair = edge_pairs[np.random.randint(12)]
                temp = self.state[indices[rand_pair[0]][0]]
                self.state[indices[rand_pair[0]][0]] = self.state[indices[rand_pair[0]][1]]
                self.state[indices[rand_pair[1]][0]] = self.state[indices[rand_pair[1]][1]]
                self.state[indices[rand_pair[0]][1]] = temp
                self.state[indices[rand_pair[1]][1]] = temp

              if self.permutation_parity() == 0:
                break
        else:
          [np.random.shuffle(i) for i in colors]
          np.random.shuffle(colors)
          self.state[indices] = colors


    def scramble_corners(self):
        """Scramble the corner pieces, maintaining the corner parity invariant."""
        #ccw order, white/yellow first. By ordering in ccw, the number of cw turns to orient each corner (the parity) is equal to the index of the white/yellow face in the colors array
        indices = np.array([[12, 19, 32], [15, 35, 48], [80, 44, 31], [83, 60, 47],
                            [0, 67, 16], [3, 51, 64], [92, 28, 79], [95, 76, 63]])
        colors = np.array([[0, 1, 2], [0, 2, 3], [5, 2, 1], [5, 3, 2],
                          [0, 4, 1], [0, 3, 4], [5, 1, 4], [5, 4, 3]])

        #randomly rotates each corner
        for i in range(8):
          colors[i] = np.roll(colors[i], np.random.randint(3))

        # permutes the corners
        np.random.shuffle(colors)

        #sums the indexes of the white/yellow faces in the colors array
        parity = sum([np.where(i%5==0)[0][0] for i in colors]) % 3 # i%5=0 is satisfied when i = 0,5

        #correct parity by rotating a random edge
        rand_edge = np.random.randint(8)
        colors[rand_edge] = np.roll(colors[rand_edge], parity*2%3) # parity*2%3 maps to {0:0, 1:2, 2:1}

        # parity = sum([np.where(i%5==0)[0][0] for i in colors]) % 3     <- the new parity should always equal 0

        self.state[indices] = colors

    def rotate_randomly(self):
        """Randomly rotates the cube."""
        i = np.random.randint(len(self.rotation_scrambles))
        self.apply_scramble(self.rotation_scrambles[i])

    def corner_parity(self):
        """Computes the corner parity of the cube."""
        indices = np.array([[12, 19, 32], [15, 35, 48], [80, 44, 31], [83, 60, 47],
                            [0, 67, 16], [3, 51, 64], [92, 28, 79], [95, 76, 63]])
        colors = self.state[indices]

        return sum([np.where(i%5==0)[0][0] for i in colors]) % 3


    def paired_edge_parity(self):
        """Computes the edge parity of the cube."""
        assert self.are_edges_solved() == True

        indices = np.array([[13, 33], [14, 34], [23, 36], [39, 52], [27, 40], [43, 56], [45, 81], [46, 82], [8, 18], [11, 49], [30, 84], [61, 87], [4, 17], [7, 50], [29, 88], [62, 91], [66, 1], [65, 2], [68, 55], [71, 20], [72, 59], [75, 24], [78, 93], [77, 94]])
        edge_pairs = np.array([[0, 1], [2, 4], [3, 5], [6, 7], [8, 12], [9, 13], [10, 14], [11, 15], [16, 17], [18, 20], [19, 21], [22, 23]])

        parity = 0

        for i in [0, 3, 4, 5, 6, 7, 8, 11]:
            edge = indices[edge_pairs[i][0]]
            if edge[0] <= 15 or edge[0] >= 80:
              X = edge[0]
              YZ = edge[1]
            else:
              X = edge[1]
              YZ = edge[0]

            if self.state[X] == 0 or self.state[X] == 5:
              parity += 1
            elif (self.state[X] == 1 or self.state[X] == 3) and (self.state[YZ] == 2 or self.state[YZ] == 4):
              parity += 1
        for i in [1, 2, 9, 10]:
            edge = indices[edge_pairs[i][0]]

            if (edge[0] >= 32 and edge[0] <= 47) or (edge[0] >= 64 and edge[0] <= 79):
              Y = edge[0]
              Z = edge[1]
            else:
              Y = edge[1]
              Z = edge[0]
            if self.state[Z] == 0 or self.state[Z] == 5:
              parity += 1
            elif self.state[Y] == 2 or self.state[Y] == 4:
              parity += 1

        return parity % 2

    def reset_rotation(self):
        """Resets the cube's rotation to the default orientation (white on top, green at front)"""
        rotations = []

        if self.state[5] == 2:
            [self.apply_scramble(self.rotations['x']) for _ in range(3)]
            rotations.append("x'")
        if self.state[21] == 2:
            [self.apply_scramble(self.rotations['y']) for _ in range(3)]
            rotations.append("y'")
        if self.state[53] == 2:
            self.apply_scramble(self.rotations['y'])
            rotations.append("y")
        if self.state[69] == 2:
            [self.apply_scramble(self.rotations['y']) for _ in range(2)]
            rotations.append("y2")
        if self.state[85] == 2:
            self.apply_scramble(self.rotations['x'])
            rotations.append("x")

        if self.state[21] == 0:
            self.apply_scramble(self.rotations['z'])
            rotations.append("z")
        if self.state[53] == 0:
            [self.apply_scramble(self.rotations['z']) for _ in range(3)]
            rotations.append("z'")
        if self.state[85] == 0:
            [self.apply_scramble(self.rotations['z']) for _ in range(2)]
            rotations.append("z2")
        

        return rotations

    def permutation_parity(self):
        """Computes the permutation parity of the cube."""
        temp_cube = Cube4()
        temp_cube.state = self.state
        temp_cube.reset_rotation()

        parity = 0

        indices = np.array([[12, 19, 32], [15, 35, 48], [80, 44, 31], [83, 60, 47],
                            [0, 67, 16], [3, 51, 64], [92, 28, 79], [95, 76, 63]])

        corner_index_from_colors = {
          (0, 1, 2): 0,
          (0, 2, 3): 1,
          (1, 2, 5): 2,
          (2, 3, 5): 3,
          (0, 1, 4): 4,
          (0, 3, 4): 5,
          (1, 4, 5): 6,
          (3, 4, 5): 7
        }

        g = []

        for i in range(8):
            piece_colors = tuple(sorted([temp_cube.state[indices[i][j]] for j in range(3)]))
            g.append(corner_index_from_colors[piece_colors])

        v = [False for _ in range(8)]
        stack = [i for i in reversed(range(8))]

        while stack:
          node = stack.pop()
          v[node] = True
          if not v[g[node]]:
            parity += 1
            stack.append(g[node])

        edge_pair_index_from_colors = {
          (0, 2): 0,
          (1, 2): 1,
          (2, 3): 2,
          (2, 5): 3,
          (0, 1): 4,
          (0, 3): 5,
          (1, 5): 6,
          (3, 5): 7,
          (0, 4): 8,
          (3, 4): 9,
          (1, 4): 10,
          (4, 5): 11,
        }

        indices = np.array([[13, 33], [14, 34], [23, 36], [39, 52], [27, 40], [43, 56], [45, 81], [46, 82], [8, 18], [11, 49], [30, 84], [61, 87], [4, 17], [7, 50], [29, 88], [62, 91], [66, 1], [65, 2], [68, 55], [71, 20], [72, 59], [75, 24], [78, 93], [77, 94]])
        edge_pairs = np.array([[0, 1], [2, 4], [3, 5], [6, 7], [8, 12], [9, 13], [10, 14], [11, 15], [16, 17], [18, 20], [19, 21], [22, 23]])

        g = []

        for i in range(12):
            piece_colors = tuple(sorted([temp_cube.state[indices[edge_pairs[i][0]][j]] for j in range(2)]))
            g.append(edge_pair_index_from_colors[piece_colors])

        v = [False for _ in range(12)]
        stack = [i for i in reversed(range(12))]

        while stack:
          node = stack.pop()
          v[node] = True
          if not v[g[node]]:
            parity += 1
            stack.append(g[node])

        return parity % 2

    def finger(self, move):
        """Applies a single move on the cube state using move string."""
        if move[0] in self.rotations:
            if move[-1] == "'":
                for _ in range(3):
                    self.apply_scramble(self.rotations[move[0]])
            else:
                self.apply_scramble(self.rotations[move])
            return
        self.state[self.sticker_target[move]] = self.state[self.sticker_source[move]]

    def finger_ix(self, ix):
        """The same `finger` method **but using indices of moves for faster execution"""
        self.state[self.sticker_target_ix[ix]] = self.state[self.sticker_source_ix[ix]]

    def apply_scramble(self, scramble):
        """Applies a sequence of moves (scramble) to the cube state."""
        if isinstance(scramble, str):
            scramble = scramble.split()

        scramble2 = []
        for i in range(len(scramble)):
            a = ""
            if scramble[i][0].isdigit() or scramble[i][0] in self.rotations:
              a += scramble[i]
              scramble2.append(a)
              continue
            if "w" in scramble[i]:
                a += "2"
            else:
                a += "1"
            a += scramble[i][0]
            if scramble[i][-1] == "'":
                a += "'"
            elif scramble[i][-1] == "2":
                a += "2"
            scramble2.append(a)
            if a[0] == "2":
                scramble2.append("1" + a[1:])
        for m in scramble2:
            if m[-1]=='2':
                for _ in range(2):
                    self.finger(m[:-1])
            else:
                    self.finger(m)

    def scrambler(self, scramble_length):
        """
        Generates a random scramble of given length and returns the cube state and scramble moves as a generator.
        Please note that index-based implementations (faster) follow commented lexical logics.
        """
        while True:
            # Reset the cube state, scramble, and return cube state and scramble moves
            self.reset()
            scramble = []

            for i in range(scramble_length):
                if i:
                    last_move = scramble[-1]
                    if i > 1:   # [3rd~ moves]
                        while True:
                            # move = random.choice(self.moves_available_after[last_move])
                            move = random.choice(self.moves_ix_available_after[last_move])

                            if scramble[-2] == last_move == move:
                                # Three subsequent moves on the same face, which could be one
                                continue
                            # elif (
                            #     scramble[-2][0] == move[0] and len(scramble[-2] + move) == 3
                            #     and last_move[0] == self.pairing[move[0]]
                            # ):
                            # elif (
                                # scramble[-2]//2 == move//2 and scramble[-2]%2 != move%2
                                # and last_move//2 == self.pairing_ix[move//2]
                            # ):
                                # Two mutually canceling moves sandwiching an opposite face move
                                # continue
                            else:
                                break
                    else:       # [2nd move]
                        # move = random.choice(self.moves_available_after[last_move])
                        move = random.choice(self.moves_ix_available_after[last_move])
                else:           # [1st move]
                    # move = random.choice(self.moves)
                    move = random.choice(self.moves_ix)

                # self.finger(move)
                self.finger_ix(move)
                scramble.append(move)

                yield self.state, move


    def __vectorize_moves(self):
        """
        Vectorizes the sticker group replacement operations for faster computation.
        This method defines ```self.sticker_target``` and ```self.sticker_source``` to manage sticker colors (target is replaced by source).
        They define indices of target and source stickers so that the moves can be vectorized.
        """
        self.sticker_target, self.sticker_source = dict(), dict()

        self.sticker_replacement = {
            # Sticker A is replaced by another sticker at index B -> A:B
            '1U':{0: 12, 1: 8, 2: 4, 3: 0, 4: 13, 5: 9, 6: 5, 7: 1, 8: 14, 9: 10, 10: 6, 11: 2, 12: 15, 13: 11, 14: 7, 15: 3, 16: 32, 17: 33, 18: 34, 19: 35, 32: 48, 33: 49, 34: 50, 35: 51, 48: 64, 49: 65, 50: 66, 51: 67, 64: 16, 65: 17, 66: 18, 67: 19},
            '1D':{83: 80, 87: 81, 91: 82, 95: 83, 82: 84, 86: 85, 90: 86, 94: 87, 81: 88, 85: 89, 89: 90, 93: 91, 80: 92, 84: 93, 88: 94, 92: 95, 44: 28, 45: 29, 46: 30, 47: 31, 60: 44, 61: 45, 62: 46, 63: 47, 76: 60, 77: 61, 78: 62, 79: 63, 28: 76, 29: 77, 30: 78, 31: 79},
            '1L':{16: 28, 17: 24, 18: 20, 19: 16, 20: 29, 21: 25, 22: 21, 23: 17, 24: 30, 25: 26, 26: 22, 27: 18, 28: 31, 29: 27, 30: 23, 31: 19, 0: 79, 4: 75, 8: 71, 12: 67, 32: 0, 36: 4, 40: 8, 44: 12, 80: 32, 84: 36, 88: 40, 92: 44, 67: 92, 71: 88, 75: 84, 79: 80},
            '1R':{48: 60, 49: 56, 50: 52, 51: 48, 52: 61, 53: 57, 54: 53, 55: 49, 56: 62, 57: 58, 58: 54, 59: 50, 60: 63, 61: 59, 62: 55, 63: 51, 3: 35, 7: 39, 11: 43, 15: 47, 35: 83, 39: 87, 43: 91, 47: 95, 83: 76, 87: 72, 91: 68, 95: 64, 64: 15, 68: 11, 72: 7, 76: 3},
            '1B':{64: 76, 65: 72, 66: 68, 67: 64, 68: 77, 69: 73, 70: 69, 71: 65, 72: 78, 73: 74, 74: 70, 75: 66, 76: 79, 77: 75, 78: 71, 79: 67, 0: 51, 1: 55, 2: 59, 3: 63, 51: 95, 55: 94, 59: 93, 63: 92, 92: 16, 93: 20, 94: 24, 95: 28, 16: 3, 20: 2, 24: 1, 28: 0},
            '1F':{32: 44, 33: 40, 34: 36, 35: 32, 36: 45, 37: 41, 38: 37, 39: 33, 40: 46, 41: 42, 42: 38, 43: 34, 44: 47, 45: 43, 46: 39, 47: 35, 12: 31, 13: 27, 14: 23, 15: 19, 48: 12, 52: 13, 56: 14, 60: 15,  80: 60, 81: 56, 82: 52, 83: 48, 19: 80, 23: 81, 27: 82, 31: 83},
            '2U':{20: 36, 21: 37, 22: 38, 23: 39, 36: 52, 37: 53, 38: 54, 39: 55, 52: 68, 53: 69, 54: 70, 55: 71, 68: 20, 69: 21, 70: 22, 71: 23} | {a: a for a in range(0, 16)},
            '2D':{24: 72, 25: 73, 26: 74, 27: 75, 40: 24, 41: 25, 42: 26, 43: 27, 56: 40, 57: 41, 58: 42, 59: 43, 72: 56, 73: 57, 74: 58, 75: 59} | {a: a for a in range(0, 16)},
            '2L':{1: 78, 5: 74, 9: 70, 13: 66, 33: 1, 37: 5, 41: 9, 45: 13, 81: 33, 85: 37, 89: 41, 93: 45, 66: 93, 70: 89, 74: 85, 78: 81} | {a: a for a in range(16, 32)},
            '2R':{2: 34, 6: 38, 10: 42, 14: 46, 34: 82, 38: 86, 42: 90, 46: 94, 82: 77, 86: 73, 90: 69, 94: 65, 65: 14, 69: 10, 73: 6, 77: 2} | {a: a for a in range(16, 32)},
            '2B':{4: 50, 5: 54, 6: 58, 7: 62, 50: 91, 54: 90, 58: 89, 62: 88, 88: 17, 89: 21, 90: 25, 91: 29, 17: 7, 21: 6, 25: 5, 29: 4} | {a: a for a in range(32, 48)},
            '2F':{8: 30, 9: 26, 10: 22, 11: 18, 18: 84, 22: 85, 26: 86, 30: 87, 84: 61, 85: 57, 86: 53, 87: 49, 49: 8, 53: 9, 57: 10, 61: 11} | {a: a for a in range(32, 48)}
        }
        for m in self.moves:
            if len(m) == 2:
                assert m in self.sticker_replacement
            else:
                if m[-1] == "'":
                    self.sticker_replacement[m] = {
                        v: k for k, v in self.sticker_replacement[m[:2]].items()
                    }
                elif m[-1] == "2":
                    self.sticker_replacement[m] = {
                        k: self.sticker_replacement[m[:2]][v]
                        for k, v in self.sticker_replacement[m[:2]].items()
                    }
                else:
                    raise

            self.sticker_target[m] = list(self.sticker_replacement[m].keys())
            self.sticker_source[m] = list(self.sticker_replacement[m].values())

            for i, idx in enumerate(self.sticker_target[m]):
                assert self.sticker_replacement[m][idx] == self.sticker_source[m][i]

        # For index slicing
        self.sticker_target_ix = np.array([np.array(self.sticker_target[m]) for m in self.moves])
        self.sticker_source_ix = np.array([np.array(self.sticker_source[m]) for m in self.moves])


class Cube3:
    """
    A class for 3x3x3 Rubik's Cube
    """
    def __init__(self):
        self.DTYPE = np.int64

        # Define initial and goal state
        self.reset()
        self.goal = np.arange(0, 9 * 6, dtype=self.DTYPE) // 9

        # Define moves
        ## faces and turns
        faces = ["U", "D", "L", "R", "B", "F"]
        ## [90 degrees clockwise, 90 degrees counter-clockwise]
        degrees = ["", "'"]
        degrees_inference = degrees[::-1]
        self.moves = [f"{f}{n}" for f in faces for n in degrees]
        self.moves_inference = [f"{f}{n}" for f in faces for n in degrees_inference]

        # Opposite faces
        self.pairing = {
            "R": "L",
            "L": "R",
            "F": "B",
            "B": "F",
            "U": "D",
            "D": "U",
        }
        # Prohibit obviously redundant moves.
        self.moves_available_after = {
            m: [v for v in self.moves if v[0] != m[0]] + [m] 
            for m in self.moves
        } # self-cancelling moves on the same face

        # [OPTIMIZATION] slicing by move string (e.g., R', U, F) => indices (e.g., 2, 6, 1)
        self.moves_ix = [self.moves.index(m) for m in self.moves]
        self.moves_ix_available_after = {
            self.moves.index(m): [self.moves.index(m) for m in available_moves]
            for m, available_moves in self.moves_available_after.items()
        }
        self.moves_ix_inference = [self.moves.index(m) for m in self.moves_inference]
        self.pairing_ix = {
            0: 1,
            1: 0,
            2: 3,
            3: 2,
            4: 5,
            5: 4,
        } # Points to the opposite face index

        # Vectorize the sticker group replacement operations
        self.__vectorize_moves()

    def reset(self):
        """Resets the cube state to the solved state."""
        self.state = np.arange(0, 9 * 6, dtype=self.DTYPE) // 9

    def is_solved(self):
        """Checks if the cube is in the solved state."""
        return np.all(self.state == self.goal)

    def finger(self, move):
        """Applies a single move on the cube state using move string."""
        self.state[self.sticker_target[move]] = self.state[self.sticker_source[move]]

    def finger_ix(self, ix):
        """The same `finger` method **but using indices of moves for faster execution"""
        self.state[self.sticker_target_ix[ix]] = self.state[self.sticker_source_ix[ix]]

    def apply_scramble(self, scramble):
        """Applies a sequence of moves (scramble) to the cube state."""
        if isinstance(scramble, str):
            scramble = scramble.split()
        for m in scramble:
            if m[-1]=='2':
                for _ in range(2):
                    self.finger(m[0])
            else:
                    self.finger(m)

    def scrambler(self, scramble_length):
        """
        Generates a random scramble of given length and returns the cube state and scramble moves as a generator.
        Please note that index-based implementations (faster) follow commented lexical logics.
        """
        while True:
            # Reset the cube state, scramble, and return cube state and scramble moves
            self.reset()
            scramble = []

            for i in range(scramble_length):
                if i:
                    last_move = scramble[-1]
                    if i > 1:   # [3rd~ moves]
                        while True:
                            # move = random.choice(self.moves_available_after[last_move])
                            move = random.choice(self.moves_ix_available_after[last_move])

                            if scramble[-2] == last_move == move:
                                # Three subsequent moves on the same face, which could be one
                                continue
                            # elif (
                            #     scramble[-2][0] == move[0] and len(scramble[-2] + move) == 3
                            #     and last_move[0] == self.pairing[move[0]]
                            # ):
                            elif (
                                scramble[-2]//2 == move//2 and scramble[-2]%2 != move%2
                                and last_move//2 == self.pairing_ix[move//2]
                            ):
                                # Two mutually canceling moves sandwiching an opposite face move
                                continue
                            else:
                                break
                    else:       # [2nd move]
                        # move = random.choice(self.moves_available_after[last_move])
                        move = random.choice(self.moves_ix_available_after[last_move])
                else:           # [1st move]
                    # move = random.choice(self.moves)
                    move = random.choice(self.moves_ix)

                # self.finger(move)
                self.finger_ix(move)
                scramble.append(move)

                yield self.state, move


    def __vectorize_moves(self):
        """
        Vectorizes the sticker group replacement operations for faster computation.
        This method defines ```self.sticker_target``` and ```self.sticker_source``` to manage sticker colors (target is replaced by source).
        They define indices of target and source stickers so that the moves can be vectorized.

        Colors:

                0 0 0
                0 0 0
                0 0 0
        2 2 2   5 5 5   3 3 3   4 4 4
        2 2 2   5 5 5   3 3 3   4 4 4
        2 2 2   5 5 5   3 3 3   4 4 4
                1 1 1
                1 1 1
                1 1 1

        Order of stickers on each face:

             2   5   8
             1   4   7
            [0]  3   6

        Indices of state (each starting with 9*(n-1)):

                         2   5   8
                         1   4   7
                        [0]  3   6
             20  23 26  47  50  53  29  32 35  38  41 44
             19  22 25  46  49  52  28  31 34  37  40 43
            [18] 21 24 [45] 48  51 [27] 30 33 [36] 39 42
                        11   14 17
                        10   13 16
                        [9]  12 15
        """
        self.sticker_target, self.sticker_source = dict(), dict()

        self.sticker_replacement = {
            # Sticker A is replaced by another sticker at index B -> A:B
            'U':{0: 6, 1: 3, 2: 0, 3: 7, 5: 1, 6: 8, 7: 5, 8: 2, 20: 47, 23: 50, 26: 53, 29: 38, 32: 41, 35: 44, 38: 20, 41: 23, 44: 26, 47: 29, 50: 32, 53: 35},
            'D':{9: 15, 10: 12, 11: 9, 12: 16, 14: 10, 15: 17, 16: 14, 17: 11, 18: 36, 21: 39, 24: 42, 27: 45, 30: 48, 33: 51, 36: 27, 39: 30, 42: 33, 45: 18, 48: 21, 51: 24},
            'L':{0: 44, 1: 43, 2: 42, 9: 45, 10: 46, 11: 47, 18: 24, 19: 21, 20: 18, 21: 25, 23: 19, 24: 26, 25: 23, 26: 20, 42: 11, 43: 10, 44: 9, 45: 0, 46: 1, 47: 2},
            'R':{6: 51, 7: 52, 8: 53, 15: 38, 16: 37, 17: 36, 27: 33, 28: 30, 29: 27, 30: 34, 32: 28, 33: 35, 34: 32, 35: 29, 36: 8, 37: 7, 38: 6, 51: 15, 52: 16, 53: 17},
            'B':{2: 35, 5: 34, 8: 33, 9: 20, 12: 19, 15: 18, 18: 2, 19: 5, 20: 8, 33: 9, 34: 12, 35: 15, 36: 42, 37: 39, 38: 36, 39: 43, 41: 37, 42: 44, 43: 41, 44: 38},
            'F':{0: 24, 3: 25, 6: 26, 11: 27, 14: 28, 17: 29, 24: 17, 25: 14, 26: 11, 27: 6, 28: 3, 29: 0, 45: 51, 46: 48, 47: 45, 48: 52, 50: 46, 51: 53, 52: 50, 53: 47}
        }
        for m in self.moves:
            if len(m) == 1:
                assert m in self.sticker_replacement
            else:
                if "'" in m:
                    self.sticker_replacement[m] = {
                        v: k for k, v in self.sticker_replacement[m[0]].items()
                    }
                elif "2" in m:
                    self.sticker_replacement[m] = {
                        k: self.sticker_replacement[m[0]][v]
                        for k, v in self.sticker_replacement[m[0]].items()
                    }
                else:
                    raise

            self.sticker_target[m] = list(self.sticker_replacement[m].keys())
            self.sticker_source[m] = list(self.sticker_replacement[m].values())

            for i, idx in enumerate(self.sticker_target[m]):
                assert self.sticker_replacement[m][idx] == self.sticker_source[m][i]

        # For index slicing
        self.sticker_target_ix = np.array([np.array(self.sticker_target[m]) for m in self.moves])
        self.sticker_source_ix = np.array([np.array(self.sticker_source[m]) for m in self.moves])


def load_environment(name: str, verbose=False):
    # Unify notation
    name = name.strip()
    name_unified = ''.join(name.lower().split())
    # Find the corresponding problem
    if name_unified in ["3x3", "rubik'scube", "rubixcube", "cube3", "cube3x3", "cube3x3x3"]:
        return Cube3()
    elif name_unified in ["4x4", "cube4x4", "cube4x4x4"]:
        return Cube4()
    else:
        # No correspondence.
        # Find & suggest the lexically nearest option
        # Code retrieved & modified from https://gist.github.com/kyo-takano/fa2b42fb4df20e2566c29c31f20f87ed
        import gzip
        query = name
        Q = gzip.compress(query.encode())
        distance_from_Q = {}
        for chunk in ["Rubik's Cube", "15 Puzzle", "Lights Out"]:
            C = gzip.compress(chunk.encode())
            query_chunk = query + " " + chunk
            Q_C = gzip.compress(query_chunk.encode())
            normalized_distance = (len(Q_C) - min(len(Q), len(C))) / max(len(Q), len(C))
            distance_from_Q[chunk] = normalized_distance
        nearest = sorted(distance_from_Q, key=distance_from_Q.get)[0]
        if verbose:
            print(f"Distance: {distance_from_Q[nearest]}")
        raise ValueError(f'Invalid environment name. Did you mean: "{nearest}"?')

if __name__=="__main__":
    env = Cube3()
    print(f"Goal:\n{env.state.reshape(6,9)}")
    env.apply_scramble("R R F U' B F D L D R'")
    print(f"Scrambled:\n{env.state.reshape(6,9)}")
