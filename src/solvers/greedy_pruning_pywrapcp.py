import sys
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def solve():
    input_data = sys.stdin.read().split()
    if not input_data: return
    it = iter(input_data)
    N = int(next(it))
    M = int(next(it))
    
    Q = [[0] * (M + 1) for _ in range(N + 1)]
    for i in range(1, N + 1):
        for j in range(1, M + 1):
            Q[i][j] = int(next(it))
            
    dist = [[int(next(it)) for _ in range(M + 1)] for _ in range(M + 1)]
    
    q_req = [0] * (N + 1)
    for i in range(1, N + 1):
        q_req[i] = int(next(it))

    manager = pywrapcp.RoutingIndexManager(M + 1, 1, 0) #Tổng số địa điểm(M kệ + 1 cửa kho), 1 chu trình, điểm xuất phát từ 0
    routing = pywrapcp.RoutingModel(manager)

    #Hàm tìm khoảng cách giữa 2 điểm 
    def distance_callback(from_index, to_index): #OR-Tools sử dụng số thứ tự của nó(index), không dùng điểm thực tế(node)
        return dist[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)] #chuyển từ index sang node để tìm khoảng cách trong ma trận dist 

    transit_cb = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)

    for p in range(1, N + 1):
        def demand_callback(from_index, p=p): #Tránh đếm sản phẩm cuối N lần, p(tham số truyền vào) = p(giá trị của vòng lặp)
            node = manager.IndexToNode(from_index)
            if node == 0:
                return 0
            return Q[p][node]

        demand_id = routing.RegisterUnaryTransitCallback(demand_callback)
        total = sum(Q[p][j] for j in range(1, M + 1))
        
        # Khởi tạo Dimension tích lũy hàng từ 0
        routing.AddDimension(demand_id, 0, total, True, f"Prod_{p}")
        dim = routing.GetDimensionOrDie(f"Prod_{p}")
        
        # Ép buộc khi về kho (Node 0) phải đạt số lượng tối thiểu
        dim.CumulVar(routing.End(0)).SetRange(q_req[p], total)

    #Phạt = 0 cho việc bỏ qua kệ để có thể bỏ qua nếu đã đủ hàng 
    for node in range(1, M + 1):
        routing.AddDisjunction([manager.NodeToIndex(node)], 0)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH) #Tránh bị kẹt ở tối ưu địa phương
    search_parameters.time_limit.seconds = 2

    current_collected = [0] * (N + 1) #Mảng N + 1 số 0 để đếm lượng hàng mỗi loại(bỏ trống ngăn 0) 
    visited = set() #Ghi lại những kệ đã đi qua 
    current_node = 0
    initial_route_nodes = [] #Ghi lại lộ trình 
    
    #Greedy 
    while any(current_collected[p] < q_req[p] for p in range(1, N + 1)):
        best_next = -1
        best_score = float('inf')
        
        for j in range(1, M + 1):
            if j not in visited:
                # Tính tổng số lượng hàng cần thiết mà kệ j mang lại
                useful_amount = 0
                for p in range(1, N + 1):
                    if current_collected[p] < q_req[p]:
                        # Chỉ tính những món hàng mình còn thiếu, thừa không tính
                        useful_amount += min(Q[p][j], q_req[p] - current_collected[p])
                
                if useful_amount > 0:
                    # Điểm đánh giá = Quãng đường / Lượng hàng hữu ích
                    # Càng gần và càng nhiều hàng thì điểm càng nhỏ (càng tốt)
                    score = dist[current_node][j] / (useful_amount + 1e-6)
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

    # Đi ngược từ cuối lộ trình lên, rút thử từng kệ ra xem có bị thiếu hàng không
    pruned_route = []
    for i in range(len(initial_route_nodes) - 1, -1, -1):
        node_to_test = initial_route_nodes[i]
        
        # Giả vờ trừ đi số hàng của kệ này
        can_remove = True
        for p in range(1, N + 1):
            if current_collected[p] - Q[p][node_to_test] < q_req[p]:
                can_remove = False # Không thể bỏ vì sẽ làm thiếu hàng
                break
        
        if can_remove:
            #Trừ số lượng hàng và bỏ qua kệ này 
            for p in range(1, N + 1):
                current_collected[p] -= Q[p][node_to_test]
        else:
            # Không bỏ được thì giữ lại
            pruned_route.append(node_to_test)
            
    # Vì duyệt ngược nên mảng bị ngược, cần lật lại cho đúng
    pruned_route.reverse()

    #Đưa các kệ được chọn cho thư viện để nó tìm thứ tự đi tốt nhất 
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
        print(len(route))
        print(" ".join(map(str, route)))

if __name__ == "__main__":
    solve()

