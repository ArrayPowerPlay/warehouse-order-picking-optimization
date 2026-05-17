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
    """Run Greedy Pruning + Pywrapcp solver with Time Sweep to find t_best."""
    # 1. ĐỌC DỮ LIỆU
    N, M, Q, d, q = read_input()

    if sum(q) == 0:
        return [], 0, 0.0

    for item_idx in range(1, N + 1):
        if sum(Q[item_idx][shelf_idx] for shelf_idx in range(1, M + 1)) < q[item_idx]:
            return [], -1, -1.0

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

    time_checkpoints = [10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 900.0]
    
    # Chỉ lấy những mốc nằm trong giới hạn time_limit của file config
    valid_checkpoints = [t for t in time_checkpoints if t < time_limit]
    if time_limit not in valid_checkpoints:
        valid_checkpoints.append(float(time_limit))

    best_distance = float('inf')
    best_route = []
    t_best_saturation = -1.0

    # Lặp qua từng mốc thời gian để dò điểm bão hòa
    for t_limit in valid_checkpoints:
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
        
        # Thiết lập thời gian theo mốc hiện tại của vòng lặp Sweep
        search_parameters.time_limit.seconds = max(1, int(t_limit))

        initial_assignment = routing.ReadAssignmentFromRoutes([pruned_route], True)
        assignment = routing.SolveFromAssignmentWithParameters(initial_assignment, search_parameters)

        if assignment:
            route = []
            index = routing.Start(0)
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                if node != 0:
                    route.append(node)
                index = assignment.Value(routing.NextVar(index))

            current_distance = compute_route_distance(route, d)
            
            # Nếu kết quả tốt hơn, cập nhật kỷ lục và ghi nhận mốc thời gian t_best
            if current_distance < best_distance:
                best_distance = current_distance
                best_route = route
                t_best_saturation = float(t_limit)

    if best_distance == float('inf'):
        return [], -1, -1.0
        
    return best_route, best_distance, t_best_saturation