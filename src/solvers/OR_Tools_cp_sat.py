import sys
from ortools.sat.python import cp_model

def solve_or_tools_cp_sat(input_file, time_limit):
    with open(input_file, 'r') as f:
        input_data = f.read().split()
    
    if not input_data: return None
    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))

    #Tạo ma trận (N+1) x (M+1) và bỏ trống hàng 0, cột 0
    Q = [[0] * (M + 1) for _ in range(N + 1)]
    for i in range(1, N + 1):
        for j in range(1, M + 1):
            Q[i][j] = int(next(iterator))

    distances = []
    for _ in range(M + 1):
        row = [int(next(iterator)) for _ in range(M + 1)]
        distances.append(row)

    #Tạo mảng N+1 phần tử và bỏ trống index 0
    q = [0] * (N + 1)
    for i in range(1, N + 1):
        q[i] = int(next(iterator))

    model = cp_model.CpModel()

    # Nếu đến kệ j thì x[j] = 1, không đến thì x[j] = 0
    x = [model.new_bool_var(f'x_{j}') for j in range(M + 1)] 
    # Xuất phát từ điểm 0
    model.Add(x[0] == 1)

    arcs = [] #List
    arc_vars = {} #Dictionary
    for i in range(M + 1):
        for j in range(M + 1):
            if i == j: continue
            var = model.new_bool_var(f'arc_{i}_{j}')
            arc_vars[(i, j)] = var
            arcs.append((i, j, var)) #cần đủ 3 biến để dùng cho AddCircuit

    # Ràng buộc về số lượng hàng
    for i in range(1, N + 1):
        model.Add(sum(Q[i][j] * x[j] for j in range(1, M + 1)) >= q[i])

    # Ràng buộc về lộ trình, sử dụng AddCircuit
    for i in range(M + 1):
        self_loop = model.new_bool_var(f'loop_{i}')
        arcs.append((i, i, self_loop)) #Tạo chu trình từ i đến i
        #Addcruit: các node không được chọn cần phải có cung tự nối 
        model.Add(self_loop == x[i].Not()) #Nếu kệ i được chọn thì self_loop = 0 => bỏ qua tạo chu trình từ i đến i

        #Mỗi node được chọn cần có đúng 1 cung vào 1 cung ra 
        model.Add(sum(arc_vars[(i, j)] for j in range(M + 1) if i != j) == x[i]) #Từ kệ i đi ra
        model.Add(sum(arc_vars[(j, i)] for j in range(M + 1) if i != j) == x[i]) #Xét các kệ khác đến i

    model.AddCircuit(arcs)

    # Hàm mục tiêu: Tối thiểu quãng đường 
    total_distance = sum(arc_vars[(i, j)] * distances[i][j] for i, j in arc_vars)
    model.Minimize(total_distance)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        current_node = 0
        route = []
        visited = set()

        while True:
            found = False
            for j in range(M + 1):
                if current_node != j and solver.Value(arc_vars[(current_node, j)]) == 1:
                    current_node = j
                    found = True
                    break
            if not found or current_node == 0 or current_node in visited:
                break
            visited.add(current_node)
            route.append(current_node) #Chỉ lưu các kệ

        route_representation = [f"{len(route)}", " ".join(map(str, route))]

        return {
            'total_distance': solver.ObjectiveValue(),
            'route_representation': route_representation
        }
    
    return None

if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        time_limit = 2.0
        if len(sys.argv) > 2:
            time_limit = float(sys.argv[2].strip())
        solution = solve_or_tools_cp_sat(file_location, time_limit)
        if solution:
            print(f"Distance: {solution['total_distance']}")
            for line in solution['route_representation']:
                print(line)
    else:
        print("Usage: python OR_Tools_cp_sat.py <file_location> [time_limit]")
