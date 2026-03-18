import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data: return
    it = iter(input_data)
    N = int(next(it))
    M = int(next(it))
    Q = [[int(next(it)) for _ in range(M)] for _ in range(N)]
    dist = [[int(next(it)) for _ in range(M + 1)] for _ in range(M + 1)]
    q_req = [int(next(it)) for _ in range(N)]

    current_collected = [0] * N
    visited = set()
    current_node = 0
    route = []

    while any(current_collected[p] < q_req[p] for p in range(N)):
        best_next = -1
        best_score = float('inf')
        
        for j in range(1, M + 1):
            if j not in visited:
                useful_amount = 0
                for p in range(N):
                    if current_collected[p] < q_req[p]:
                        useful_amount += min(Q[p][j-1], q_req[p] - current_collected[p])
                
                if useful_amount > 0:
                    score = dist[current_node][j] / (useful_amount + 1e-6)
                    if score < best_score:
                        best_score = score
                        best_next = j
                        
        if best_next == -1:
            break

        visited.add(best_next)
        route.append(best_next)
        current_node = best_next
        
        for p in range(N):
            current_collected[p] += Q[p][best_next-1]

    if route:
        print(len(route))
        print(" ".join(map(str, route)))

if __name__ == "__main__":
    solve()
