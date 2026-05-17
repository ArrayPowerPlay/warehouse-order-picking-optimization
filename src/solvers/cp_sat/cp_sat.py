import os
import sys
import time
from ortools.sat.python import cp_model

# Thêm đường dẫn gốc để import thư viện của nhóm
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.solvers.utils import read_input

class SolutionTracker(cp_model.CpSolverSolutionCallback):
    def __init__(self, start_time):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.start_time = start_time
        self.t_best = -1.0

    def on_solution_callback(self):
        self.t_best = time.perf_counter() - self.start_time

def cpsat_solver(time_limit: float, num_search_workers: int = 0):
    """Run CP-SAT solver and return route, total_distance, and t_best."""
    # 1. ĐỌC DỮ LIỆU CHUNG THEO CHUẨN CỦA TEAM
    N, M, Q, d, q = read_input()

    if sum(q) == 0:
        return [], 0, 0.0

    for item_idx in range(1, N + 1):
        if sum(Q[item_idx][shelf_idx] for shelf_idx in range(1, M + 1)) < q[item_idx]:
            return [], -1, -1.0

    start_time = time.perf_counter()

    # 2. XÂY DỰNG MODEL CP-SAT
    model = cp_model.CpModel()
    x = [model.new_bool_var(f'x_{j}') for j in range(M + 1)] 
    model.Add(x[0] == 1)

    arcs = []; arc_vars = {} 
    for i in range(M + 1):
        for j in range(M + 1):
            if i == j: continue
            var = model.new_bool_var(f'arc_{i}_{j}')
            arc_vars[(i, j)] = var
            arcs.append((i, j, var)) 

    for i in range(1, N + 1):
        model.Add(sum(Q[i][j] * x[j] for j in range(1, M + 1)) >= q[i])

    for i in range(M + 1):
        self_loop = model.new_bool_var(f'loop_{i}')
        arcs.append((i, i, self_loop)) 
        model.Add(self_loop == x[i].Not()) 
        model.Add(sum(arc_vars[(i, j)] for j in range(M + 1) if i != j) == x[i]) 
        model.Add(sum(arc_vars[(j, i)] for j in range(M + 1) if i != j) == x[i]) 

    model.AddCircuit(arcs)
    model.Minimize(sum(arc_vars[(i, j)] * d[i][j] for i, j in arc_vars))

    # 3. GIẢI QUYẾT
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit)
    solver.parameters.num_search_workers = num_search_workers
    
    tracker = SolutionTracker(start_time)
    status = solver.Solve(model, tracker)

    # 4. TRẢ KẾT QUẢ
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        current_node = 0; route = []; visited = set()
        while True:
            found = False
            for j in range(M + 1):
                if current_node != j and solver.Value(arc_vars[(current_node, j)]) == 1:
                    current_node = j; found = True; break
            if not found or current_node == 0 or current_node in visited: break
            visited.add(current_node)
            route.append(current_node) 

        final_distance = int(solver.ObjectiveValue())
        return route, final_distance, round(tracker.t_best, 4)
    else:
        return [], -1, -1.0