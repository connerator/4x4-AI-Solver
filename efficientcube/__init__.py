import os
import torch
from .environments import load_environment
from .model import Model
from . import search
from .utils import *

class EfficientCube:
    def __init__(
        self,
        env="4x4",
        model_path="auto",
        device=torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'),
    ):
        """
        Initialize EfficientCube object.

        Parameters:
            env (str): The name of the Rubik's Cube environment.
            model_path (str): Path to the trained model file, or "auto" to use default paths.
            device (torch.device): The device to run the model on (GPU if available, otherwise CPU).
        """

        # Set up Rubik's Cube environment
        self.env_name = env
        self.env = load_environment(env)
        
        # If model_path is set to "auto", use default paths based on the environment
        if model_path.lower().strip()=="auto":
            script_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = {
                "3x3": "./models/cube3.pth",
                "4x4": "./models/cube4.pth",
            }[env]
            model_path = os.path.normpath(os.path.join(script_dir, model_path))
        assert os.path.exists(model_path), f"Model file not found at `{model_path}`"

        # Load a trained model from the specified path
        if (self.env_name == '4x4'): # 4x4 model loads in the weights, whereas the 3x3 model loads everything
            try:
                self.model = Model(input_dim=576, output_dim=len(self.env.moves))
                self.model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
                self.model.to(device)
            except:
                raise ValueError(f"Model could not be loaded from `{model_path}`")
        else:
            try:
                self.model = torch.jit.load(model_path).to(device)
            except:
                try:
                    self.model = torch.load(model_path).to(device)
                except:
                    raise ValueError(f"Model could not be loaded from `{model_path}`")

        self.model.eval()  # Set the model to evaluation mode (no training)

    """ Methods defined below are mere routers """

    def solve(self, beam_width):
        # Execute a beam search to find the solution
        if self.env_name == '4x4':
            
            temp_env = Cube4()
            temp_env.state = self.env.state

            print("Reducing to 3x3...")
            result1 = search.beam_search(temp_env, self.model, beam_width)

            self.env.apply_scramble(result1['solutions'])

            rotations = self.env.reset_rotation()

            cube3_env = convert_4x4_to_3x3(self.env)
            cube3_solver = EfficientCube(env='3x3')
            cube3_solver.env = cube3_env
            print("Solving 3x3...")
            result2 = cube3_solver.solve(beam_width)
            result2['solutions'] = ["1"+move for move in result2['solutions']]

            result = result1
            result['solutions'] += rotations + result2['solutions']
            result['num_nodes'] += result2['num_nodes']
            result['times'] += result2['times']

            self.apply_moves_to_env(result['solutions'][0])

            return result
        elif self.env_name == '3x3':
            return search.beam_search(self.env, self.model, beam_width)

    def env_is_solved(self):
        return self.env.is_solved()
    
    def reset_env(self):
        self.env.reset()
    
    def apply_moves_to_env(self, moves):
        self.env.apply_scramble(moves)
