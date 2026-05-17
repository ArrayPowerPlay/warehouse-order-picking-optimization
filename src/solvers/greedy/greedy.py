import os
import sys
import time

# Thêm đường dẫn gốc
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.solvers.utils import read_input, compute_route_distance

def greedy_solver(time_limit: float):
    """Run Greedy solver and return route, total_distance, and t_best."""
    N, M, Q, d, q = read_input()
    start_time = time.perf_counter()

    if sum(q) == 0:
        return [], 0, 0.0

    for item_idx in range(1, N + 1):
        if sum(Q[item_idx][shelf_idx] for shelf_idx in range(1, M + 1)) < q[item_idx]:
            return [], -1, -1.0
    
    current_collected = [0] * (N + 1)
    visited = set()
    current_node = 0
    route = []

    while any(current_collected[p] < q[p] for p in range(1, N + 1)):
        best_next = -1
        best_score = float('inf')
        
        for j in range(1, M + 1):
            if j not in visited:
                useful_amount = 0
                for p in range(1, N + 1):
                    if current_collected[p] < q[p]:
                        useful_amount += min(Q[p][j], q[p] - current_collected[p])
                
                if useful_amount > 0:
                    score = d[current_node][j] / (useful_amount + 1e-6)
                    if score < best_score:
                        best_score = score
                        best_next = j
                        
        if best_next == -1:
            break

        visited.add(best_next)
        route.append(best_next)
        current_node = best_next
        
        for p in range(1, N + 1):
            current_collected[p] += Q[p][best_next]

    total_distance = compute_route_distance(route, d)

    t_best = time.perf_counter() - start_time
    
    return route, total_distance, round(t_best, 4)