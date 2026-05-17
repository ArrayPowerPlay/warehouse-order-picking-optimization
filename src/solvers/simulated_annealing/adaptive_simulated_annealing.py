"""
Adaptive Simulated Annealing (ASA) for Warehouse Order Picking Optimization.

The solver stops by time limit and returns:
    route, total_distance, t_best
"""

import argparse
import math
import os
import random
import sys
import time

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.solvers.utils import compute_route_distance, read_input


DEFAULT_TIME_LIMIT = 5.0
DEFAULT_ALPHA = 0.995
DEFAULT_MAX_NO_IMPROVE = 1000
DEFAULT_REHEAT_RATIO = 0.3
DEFAULT_SEED = 42


def asa_solver(
    time_limit: float,
    alpha: float = DEFAULT_ALPHA,
    max_no_improve: int = DEFAULT_MAX_NO_IMPROVE,
    reheat_ratio: float = DEFAULT_REHEAT_RATIO,
    seed: int = DEFAULT_SEED,
):
    """Run ASA and return route, total distance, and t_best."""
    random.seed(seed)
    N, M, Q, d, q = read_input()

    if sum(q) == 0:
        return [], 0, 0.0

    for item_idx in range(1, N + 1):
        if sum(Q[item_idx][shelf_idx] for shelf_idx in range(1, M + 1)) < q[item_idx]:
            return [], -1, -1

    algorithm_start = time.perf_counter()
    deadline = algorithm_start + max(0.0, time_limit)

    def evaluate_route(permutation_of_shelves: list[int]) -> tuple[int, list[int]]:
        """From the permutation of shelves, return the cost and the actual route needed
        to complete orders from customers."""
        remaining_order = q[:]
        fulfilled_count = 0

        for item_idx in range(1, N + 1):
            if remaining_order[item_idx] <= 0:
                fulfilled_count += 1

        if fulfilled_count == N:
            return 0, []

        route = []
        for shelf_idx in permutation_of_shelves:
            route.append(shelf_idx)
            for item_idx in range(1, N + 1):
                if remaining_order[item_idx] > 0:
                    fulfilled_amount = min(remaining_order[item_idx], Q[item_idx][shelf_idx])
                    remaining_order[item_idx] -= fulfilled_amount
                    if remaining_order[item_idx] <= 0:
                        fulfilled_count += 1
            if fulfilled_count == N:
                break

        return compute_route_distance(route, d), route

    ### Implement some ALNS operators
    def op_swap(state: list[int]) -> list[int]:
        """Swap 2 elements in a route."""
        neighbor = state[:]
        if M < 2:
            return neighbor
        pos1, pos2 = random.sample(range(M), 2)
        neighbor[pos1], neighbor[pos2] = neighbor[pos2], neighbor[pos1]
        return neighbor

    def op_insert(state: list[int]) -> list[int]:
        """Insert the first element right immediately before the second element."""
        neighbor = state[:]
        if M < 2:
            return neighbor
        pos1, pos2 = random.sample(range(M), 2)
        value = neighbor.pop(pos1)
        neighbor.insert(pos2, value)
        return neighbor

    def op_2opt(state: list[int]) -> list[int]:
        """Reverse a sub route."""
        neighbor = state[:]
        if M < 2:
            return neighbor
        pos1, pos2 = sorted(random.sample(range(M), 2))
        neighbor[pos1:pos2] = reversed(neighbor[pos1:pos2])
        return neighbor

    operators = [op_swap, op_2opt, op_insert]
    weights = [1.0, 1.0, 1.0]

    w_min = 0.1
    rho = 0.2
    epoch_length = 100
    grace_period_epochs = 2

    ### Initialize initial state
    current_state = list(range(1, M + 1))
    random.shuffle(current_state)
    current_cost, current_route = evaluate_route(current_state)

    best_state = current_state[:]
    best_cost = current_cost
    best_route = current_route[:]
    t_best = time.perf_counter() - algorithm_start

    ### Find t_start
    deltas = []
    while len(deltas) < 100 and time.perf_counter() < deadline:
        operator = random.choice(operators)
        neighbor_state = operator(current_state)
        neighbor_cost, _ = evaluate_route(neighbor_state)
        if neighbor_cost > current_cost:
            deltas.append(neighbor_cost - current_cost)

    delta_avg = (sum(deltas) / len(deltas)) if deltas else 10.0

    t_start = -delta_avg / math.log(0.8)
    if t_start <= 0:
        t_start = 100.0
    temperature = t_start

    no_improve_cnt = 0      # Number of iterations that the state does not change
    grace_period = 0
    epoch_iter = 0          # Track epoch
    epoch_accepted = 0
    op_scores = [0, 0, 0]   # Scores per ALNS operators
    op_counts = [0, 0, 0]   # Number of times an operators being used in an epoch

    while time.perf_counter() < deadline:
        total_weight = sum(weights)
        roulette = random.uniform(0, total_weight)
        cumulative_weight = 0.0
        op_idx = len(operators) - 1
        for idx in range(len(operators)):
            cumulative_weight += weights[idx]
            if roulette < cumulative_weight:
                op_idx = idx
                break

        neighbor_state = operators[op_idx](current_state)
        neighbor_cost, neighbor_route = evaluate_route(neighbor_state)

        delta_e = neighbor_cost - current_cost
        accepted = False
        score_for_op = 0

        if delta_e < 0:
            accepted = True
            score_for_op = 5 if neighbor_cost < best_cost else 2
        else:
            acceptance_prob = math.exp(-delta_e / temperature) if temperature > 0.0001 else 0.0
            if random.random() < acceptance_prob:
                accepted = True
                score_for_op = 1

        op_counts[op_idx] += 1
        op_scores[op_idx] += score_for_op

        if accepted:
            current_state = neighbor_state
            current_cost = neighbor_cost
            current_route = neighbor_route
            epoch_accepted += 1

            if current_cost < best_cost:
                best_cost = current_cost
                best_route = current_route[:]
                best_state = current_state[:]
                t_best = time.perf_counter() - algorithm_start
                no_improve_cnt = 0
            else:
                no_improve_cnt += 1
        else:
            no_improve_cnt += 1

        epoch_iter += 1

        if epoch_iter == epoch_length:
            for idx in range(len(operators)):
                new_weight = (1 - rho) * weights[idx] + rho * (op_scores[idx] / max(1, op_counts[idx]))
                weights[idx] = max(new_weight, w_min)

            acceptance_rate = epoch_accepted / epoch_length
            if grace_period > 0:
                grace_period -= 1
                temperature *= alpha
            else:
                if acceptance_rate > 0.5:
                    temperature *= 0.9
                elif acceptance_rate < 0.05:
                    temperature *= 1.1
                else:
                    temperature *= alpha

            epoch_iter = 0
            epoch_accepted = 0
            op_scores = [0, 0, 0]
            op_counts = [0, 0, 0]

        if no_improve_cnt >= max_no_improve:
            no_improve_cnt = 0
            temperature = t_start * reheat_ratio  # Stucked -> Warm up to increase temperature
            grace_period = grace_period_epochs

            # Break best_state to jump out of local optimum
            current_state = best_state[:]
            num_swaps = max(1, M // 10)  # Randomly mix 10% of current state
            for _ in range(num_swaps):
                if M < 2:
                    break
                pos1, pos2 = random.sample(range(M), 2)
                current_state[pos1], current_state[pos2] = current_state[pos2], current_state[pos1]

            current_cost, current_route = evaluate_route(current_state)

    return best_route, best_cost, t_best


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adaptive Simulated Annealing Solver")
    parser.add_argument(
        "--time_limit",
        type=float,
        default=DEFAULT_TIME_LIMIT,
        help="Time limit for the solver in seconds",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=DEFAULT_ALPHA,
        help="Base cooling rate",
    )
    parser.add_argument(
        "--max_no_improve",
        type=int,
        default=DEFAULT_MAX_NO_IMPROVE,
        help="Number of iterations without improvement before re-annealing",
    )
    parser.add_argument(
        "--reheat_ratio",
        type=float,
        default=DEFAULT_REHEAT_RATIO,
        help="Ratio of T_start to reheat to",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed for reproducibility",
    )
    args = parser.parse_args()

    best_route, best_distance, t_best = asa_solver(
        time_limit=args.time_limit,
        alpha=args.alpha,
        max_no_improve=args.max_no_improve,
        reheat_ratio=args.reheat_ratio,
        seed=args.seed,
    )

    print(best_route)
    print(best_distance)
    print(t_best)
