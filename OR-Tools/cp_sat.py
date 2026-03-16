import sys
from ortools.sat.python import cp_model

def solve():
    input_data = sys.stdin.read().split()
    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))

    Q = []
    for _ in range(N):
        row = [int(next(iterator)) for _ in range(M)]
        Q.append(row)

    distances = []
    for _ in range(M + 1):
        row = [int(next(iterator)) for _ in range(M + 1)]
        distances.append(row)

    q = [int(next(iterator)) for _ in range(N)]

    model = cp_model.CpModel()

    #Nếu đến kệ j thì x[j] = 1, không đến thì x[j] = 0
    x = [model.NewBoolVar(f'x_{j}') for j in range(M + 1)] 
    #Xuất phát từ điểm 0
    model.Add(x[0] == 1)

    arcs = [] #List
    arc_vars = {} #Dictionary
    for i in range(M + 1):
        for j in range(M + 1):
            if i == j: continue
            var = model.NewBoolVar(f'arc_{i}_{j}')
            arc_vars[(i, j)] = var
            arcs.append((i, j, var)) #cần đủ 3 biến để dùng cho AddCircuit

        #Ràng buộc về số lượng hàng
    for i in range(N):
        model.Add(sum(Q[i][j-1] * x[j] for j in range(1, M + 1)) >= q[i])

    #Ràng buộc về lộ trình, sử dụng AddCircuit
    for i in range(M + 1):
        self_loop = model.NewBoolVar(f'loop_{i}')
        arcs.append((i, i, self_loop)) #Tạo chu trình từ i đến i
        #Addcruit: các node không được chọn cần phải có cung tự nối 
        model.Add(self_loop == x[i].Not()) #Nếu kệ i được chọn thì self_loop = 0 => bỏ qua tạo chu trình từ i đến i

        #Mỗi node được chọn cần có đúng 1 cung vào 1 cung ra 
        model.Add(sum(arc_vars[(i, j)] for j in range(M + 1) if i != j) == x[i]) #Từ kệ i đi ra
        model.Add(sum(arc_vars[(j, i)] for j in range(M + 1) if i != j) == x[i]) #Xét các kệ khác đến i

    model.AddCircuit(arcs)

    #Hàm mục tiêu: Tối thiểu quãng đường 
    total_distance = sum(arc_vars[(i, j)] * distances[i][j] for i, j in arc_vars)
    model.Minimize(total_distance)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 2.0
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        current_node = 0
        route = []

        while True:
            for j in range(M + 1):
                if current_node != j and solver.Value(arc_vars[(current_node, j)]):
                    current_node = j
                    break
            if current_node == 0:
                break
            route.append(current_node) #Chỉ lưu các kệ

        print(len(route))
        print(" ".join(map(str,route)))

if __name__ == '__main__':
    solve()
                                                    
                
