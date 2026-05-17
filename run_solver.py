
import os
import sys
import time

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from solvers.OR_Tools_cp_sat import solve_or_tools_cp_sat

def run_experiment():
    input_file = os.path.join('data', 'val_set', 'small_02_N3_M10.in')
    time_limits = [50, 100]
    output_dir = 'outputs'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for time_limit in time_limits:
        print(f"Running solver with time limit: {time_limit}s")
        
        solution = solve_or_tools_cp_sat(input_file, time_limit)
        
        if solution:
            output_file_path = os.path.join(output_dir, f'small_02_N3_M10_{time_limit}s_output.txt')
            with open(output_file_path, 'w') as f:
                f.write(f"Distance: {solution['total_distance']}\n")
                f.write("Route:\n")
                for line in solution['route_representation']:
                    f.write(f"{line}\n")
            print(f"Results saved to {output_file_path}")
        else:
            print(f"No solution found for time limit {time_limit}s")

if __name__ == '__main__':
    run_experiment()
