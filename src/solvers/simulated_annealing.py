"""
Implement simulated annealing for the warehouse order picking problem
"""
import random
import math
from utils import read_input
import sys


def simulated_annealing_solver(T_start, alpha, max_num_improves):
    N, M, Q, d, q = read_input()

    def evaluate_route(permutation_of_shelves):
        """
        Given a permutation of shelves, calculate the distance and the actual route needed
        to collect all items, following the path in the permutation of shelves 
        """
        remaining_order = q[:]
        # Number of items that have been fulfilled through the route
        fulfilled_count = 0

        for i in range(1, N + 1):
            if remaining_order[i] <= 0:
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

        total_dist = 0
        current_point = 0

        for next_shelf in route:
            total_dist += d[current_point][next_shelf]
            current_point = next_shelf

        total_dist += d[current_point][0]
        return total_dist, route
    
    def generate_neighbor(current_permutation):
        """
        Generate neighbor of a given solution (permutation of shelves)
        """
        neighbor = current_permutation[:]
        idx1, idx2 = random.sample(range(M), 2)
        neighbor[idx1], neighbor[idx2] = neighbor[idx2], neighbor[idx1]
        return neighbor
    
    # Initialize initial state (permutation of sheves)
    shelve_idxs = list(range(1, M + 1))
    current_state = shelve_idxs[:]
    random.shuffle(current_state)

    current_cost, current_route = evaluate_route(current_state)
    best_cost = current_cost
    best_route = current_route[:]

    temp = T_start
    T_min = 0.001
    no_improve_cnt = 0

    while temp > T_min:
        neighbor_state = generate_neighbor(current_state)
        neighbor_cost, neighbor_route = evaluate_route(neighbor_state)

        delta_e = neighbor_cost - current_cost
        accepted = False
        if delta_e < 0:
            accepted = True
        else:
            p = math.exp(-delta_e / temp)
            if random.random() < p:
                accepted = True

        # Move to neighbor solution
        if accepted:
            current_state = neighbor_state
            current_cost = neighbor_cost
            current_route = neighbor_route

            if current_cost < best_cost:
                best_cost = current_cost
                best_route = current_route[:]
                no_improve_cnt = 0
            else:
                no_improve_cnt += 1

        if no_improve_cnt == max_num_improves:
            break

        temp = temp * alpha

    return best_cost, best_route


if __name__ == "__main__":
    T0 = 1000.0
    alpha = 0.9995
    max_num_improve = 5000
    best_cost, best_route = simulated_annealing_solver(T0, alpha, max_num_improve)
    print(len(best_route))
    print(*best_route)