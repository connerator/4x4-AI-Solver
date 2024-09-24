from efficientcube import EfficientCube, utils


if __name__ == '__main__':

    """ Specify scramble & search parameter """
    scramble = input("\nPaste scramble here:\n").split(' ')
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