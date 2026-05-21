import os
import sys
import time
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# Thêm đường dẫn gốc
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.solvers.utils import read_input, compute_route_distance

def pywrapcp_solver(time_limit: float):
    """Run Greedy Pruning + Pywrapcp solver for a single given time_limit."""
    # 1. ĐỌC DỮ LIỆU
    N, M, Q, d, q = read_input()

    if sum(q) == 0:
        return [], 0

    for item_idx in range(1, N + 1):
        if sum(Q[item_idx][shelf_idx] for shelf_idx in range(1, M + 1)) < q[item_idx]:
            return [], -1

    # 2. CHẠY GREEDY KHỞI TẠO & PRUNING 
    current_collected = [0] * (N + 1)
    visited = set()
    current_node = 0
    initial_route_nodes = []
    
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
        initial_route_nodes.append(best_next)
        current_node = best_next
        
        for p in range(1, N + 1):
            current_collected[p] += Q[p][best_next]

    pruned_route = []
    for i in range(len(initial_route_nodes) - 1, -1, -1):
        node_to_test = initial_route_nodes[i]
        can_remove = True
        for p in range(1, N + 1):
            if current_collected[p] - Q[p][node_to_test] < q[p]:
                can_remove = False
                break
        
        if can_remove:
            for p in range(1, N + 1):
                current_collected[p] -= Q[p][node_to_test]
        else:
            pruned_route.append(node_to_test)
            
    pruned_route.reverse()

    # 3. CHẠY OR-TOOLS (Chạy 1 lần duy nhất theo time_limit)
    manager = pywrapcp.RoutingIndexManager(M + 1, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        return d[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit_cb = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)

    for p in range(1, N + 1):
        def demand_callback(from_index, p=p):
            node = manager.IndexToNode(from_index)
            if node == 0:
                return 0
            return Q[p][node]

        demand_id = routing.RegisterUnaryTransitCallback(demand_callback)
        total = sum(Q[p][j] for j in range(1, M + 1))
        
        routing.AddDimension(demand_id, 0, total, True, f"Prod_{p}")
        dim = routing.GetDimensionOrDie(f"Prod_{p}")
        dim.CumulVar(routing.End(0)).SetRange(q[p], total)

    for node in range(1, M + 1):
        routing.AddDisjunction([manager.NodeToIndex(node)], 0)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    
    # Thiết lập thời gian (Ép kiểu int để tránh lỗi phẩy động)
    search_parameters.time_limit.seconds = max(1, int(time_limit))

    initial_assignment = routing.ReadAssignmentFromRoutes([pruned_route], True)
    assignment = routing.SolveFromAssignmentWithParameters(initial_assignment, search_parameters)

    # 4. TRẢ VỀ KẾT QUẢ
    if assignment:
        route = []
        index = routing.Start(0)
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:
                route.append(node)
            index = assignment.Value(routing.NextVar(index))

        current_distance = compute_route_distance(route, d)
        return route, current_distance

    return [], -1