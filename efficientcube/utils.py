import numpy as np
from .environments import *

def convert_4x4_to_3x3(cube4):
    index_map = {0:2, 1:5, 3:8, 4:1, 5:4, 7:7, 12:0, 13:3, 15:6, 16:20, 17:23, 19:26, 20:19, 21:22, 23:25, 28:18, 29:21, 31:24, 32:47, 33:50, 35:53, 36:46, 37:49, 39:52, 44:45, 45:48,
                  47:51, 48:29, 49:32, 51:35, 52:28, 53:31, 55:34, 60:27, 61:30, 63:33, 64:38, 65:41, 67:44, 68:37, 69:40, 71:43, 76:36, 77:39, 79:42, 80:11, 81:14, 83:17, 84:10, 85:13,
                  87:16, 92:9, 93:12, 95:15}
    
    color_map = {0:0, 1:2, 2:5, 3:3, 4:4, 5:1}

    cube3 = Cube3()

    old_state = cube4.state
    new_state = np.zeros(6*9)
    for i in index_map.keys():
        new_state[index_map[i]] = color_map[old_state[i]]
    cube3.state = new_state

    return cube3

def generate_simulator_link(scramble, solution):
    url = "https://alg.cubing.net/?puzzle=4x4x4"

    url += "&setup="
    scramble_str = '_'.join(scramble)
    scramble_str = scramble_str.replace("'", "-")
    url += scramble_str

    url += "&alg="
    solution_str = '_'.join(solution)
    solution_str = solution_str.replace("'", "-")
    url += solution_str

    return url