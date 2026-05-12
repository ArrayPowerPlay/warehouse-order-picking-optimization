"""
Adaptive Simulated Annealing (ASA) cho bài toán Warehouse Order Picking Optimization.
Nâng cấp từ SA gốc với ALNS operators, Adaptive Cooling và Re-annealing.
Đánh giá điểm dừng dựa trên time_limit thay vì vòng lặp tĩnh.
"""

import sys
import os
import time
import math
import random
import argparse

# Thêm thư mục gốc vào sys.path để import được config và utils
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.settings import TIME_LIMITS
from src.solvers.utils import read_input, compute_route_distance


def asa_solver(
    time_limit: float,
    alpha: float,
    max_no_improve: int,
    reheat_ratio: float,
    seed: int = 42
):
    """
    Hàm giải chính bằng thuật toán Adaptive Simulated Annealing.
    """
    random.seed(seed)
    
    # read_input() tự động đọc từ stdin
    N, M, Q, d, q = read_input()

    # Nếu bài toán rỗng từ đầu (không yêu cầu sản phẩm nào)
    if sum(q) == 0:
        return 0, []

    # Kiểm tra feasibility (chỉ để loại sớm infeasible instances, tuy nhiên evaluator cũng làm điều này)
    # Vì project cho phép trả về số kệ rất dài cho infeasible instance hoặc xử lý ngoài, ta chạy tiếp.
    is_infeasible = False
    for i in range(1, N + 1):
        if sum(Q[i][j] for j in range(1, M + 1)) < q[i]:
            is_infeasible = True
            break
            
    if is_infeasible:
        # Tùy thuộc pipeline đánh giá của project, trả về cost = inf và route rỗng
        return float('inf'), []

    def evaluate_route(permutation_of_shelves: list[int]) -> tuple[int, list[int]]:
        """
        Dịch mã từ hoán vị M kệ -> Lộ trình thực tế. Dừng lại ngay khi thu đủ hàng.
        Tính khoảng cách bằng hàm compute_route_distance trong utils.
        """
        remaining_order = q[:]
        fulfilled_count = 0
        
        # Đếm số mặt hàng không cần mua (q[i] = 0)
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
                
        cost = compute_route_distance(route, d)
        return cost, route

    # =========================================================================
    # CÁC TOÁN TỬ ALNS LÂN CẬN (NEIGHBORHOOD OPERATORS)
    # =========================================================================
    def op_swap(state: list[int]) -> list[int]:
        neighbor = state[:]
        idx1, idx2 = random.sample(range(M), 2)
        neighbor[idx1], neighbor[idx2] = neighbor[idx2], neighbor[idx1]
        return neighbor

    def op_insert(state: list[int]) -> list[int]:
        neighbor = state[:]
        idx1, idx2 = random.sample(range(M), 2)
        val = neighbor.pop(idx1)
        neighbor.insert(idx2, val)
        return neighbor

    def op_2opt(state: list[int]) -> list[int]:
        neighbor = state[:]
        idx1, idx2 = sorted(random.sample(range(M + 1), 2))
        neighbor[idx1:idx2] = reversed(neighbor[idx1:idx2])
        return neighbor

    operators = [op_swap, op_insert, op_2opt]
    w = [1.0, 1.0, 1.0] # Khởi tạo trọng số
    
    # Hằng số ALNS và Adaptive Cooling
    w_min = 0.1
    rho = 0.2
    epoch_length = 100
    grace_period_epochs = 2

    # =========================================================================
    # KHỞI TẠO TRẠNG THÁI (INITIALIZATION)
    # =========================================================================
    current_state = list(range(1, M + 1))
    random.shuffle(current_state)
    current_cost, current_route = evaluate_route(current_state)
    
    best_state = current_state[:]
    best_cost = current_cost
    best_route = current_route[:]

    # =========================================================================
    # TỰ ĐỘNG TÍNH T_START (WARM-UP)
    # =========================================================================
    deltas = []
    for _ in range(100):
        op = random.choice(operators)
        neighbor_state = op(current_state)
        neighbor_cost, _ = evaluate_route(neighbor_state)
        if neighbor_cost > current_cost:
            deltas.append(neighbor_cost - current_cost)
            
    if deltas:
        delta_avg = sum(deltas) / len(deltas)
    else:
        delta_avg = 10.0 # Giá trị dự phòng nếu các lân cận ngẫu nhiên đều bằng/nhỏ hơn

    T_start = -delta_avg / math.log(0.8)
    if T_start <= 0: T_start = 100.0
    T = T_start

    # =========================================================================
    # VÒNG LẶP CHÍNH CỦA ASA
    # =========================================================================
    start_time = time.time()
    
    no_improve_cnt = 0
    grace_period = 0
    
    epoch_iter = 0
    epoch_accepted = 0
    op_scores = [0, 0, 0]
    op_counts = [0, 0, 0]

    while time.time() - start_time < time_limit:
        # Chọn toán tử theo cơ chế Roulette Wheel Selection dựa trên trọng số w
        total_w = sum(w)
        r = random.uniform(0, total_w)
        cum_w = 0.0
        op_idx = 2
        for i in range(3):
            cum_w += w[i]
            if r <= cum_w:
                op_idx = i
                break
                
        neighbor_state = operators[op_idx](current_state)
        neighbor_cost, neighbor_route = evaluate_route(neighbor_state)
        
        delta_e = neighbor_cost - current_cost
        accepted = False
        score_for_op = 0
        
        # Tiêu chí chấp nhận SA
        if delta_e < 0:
            accepted = True
            if neighbor_cost < best_cost:
                score_for_op = 5 # Điểm 5 cho New Best
            else:
                score_for_op = 2 # Điểm 2 cho Improvement
        else:
            p = math.exp(-delta_e / T) if T > 0.0001 else 0
            if random.random() < p:
                accepted = True
                score_for_op = 1 # Điểm 1 cho việc chấp nhận nghiệm kém hơn (Exploration)
            else:
                score_for_op = 0 # Điểm 0 khi bị từ chối

        # Cập nhật số liệu cho toán tử
        op_counts[op_idx] += 1
        op_scores[op_idx] += score_for_op

        # Di chuyển trạng thái
        if accepted:
            current_state = neighbor_state
            current_cost = neighbor_cost
            current_route = neighbor_route
            epoch_accepted += 1
            
            if current_cost < best_cost:
                best_cost = current_cost
                best_route = current_route[:]
                best_state = current_state[:]
                no_improve_cnt = 0
            else:
                no_improve_cnt += 1
        else:
            no_improve_cnt += 1

        epoch_iter += 1
        
        # =====================================================================
        # HẾT 1 EPOCH: CẬP NHẬT TRỌNG SỐ VÀ ADAPTIVE COOLING
        # =====================================================================
        if epoch_iter == epoch_length:
            # 1. Cập nhật ALNS weights
            for i in range(3):
                new_w = (1 - rho) * w[i] + rho * (op_scores[i] / max(1, op_counts[i]))
                w[i] = max(new_w, w_min) # Weight floor
                
            # 2. Adaptive Cooling
            R_a = epoch_accepted / epoch_length
            if grace_period > 0:
                grace_period -= 1
                T = T * alpha # Hạ nhiệt bình thường trong grace_period
            else:
                if R_a > 0.5:
                    T = T * 0.9 # Chấp nhận quá dễ -> Hạ nhiệt nhanh
                elif R_a < 0.05:
                    T = T * 1.1 # Bị kẹt -> Ủ ấm tăng nhiệt
                else:
                    T = T * alpha # Bình thường
                    
            # Reset biến đếm Epoch
            epoch_iter = 0
            epoch_accepted = 0
            op_scores = [0, 0, 0]
            op_counts = [0, 0, 0]

        # =====================================================================
        # RE-ANNEALING KHI BỊ KẸT DÀI HẠN
        # =====================================================================
        if no_improve_cnt >= max_no_improve:
            no_improve_cnt = 0
            T = T_start * reheat_ratio
            grace_period = grace_period_epochs
            
            # Phá vỡ best_state để nhảy ra khỏi local optimum (Perturbation)
            current_state = best_state[:]
            # Swap ngẫu nhiên 10% số kệ
            num_swaps = max(1, M // 10)
            for _ in range(num_swaps):
                idx1, idx2 = random.sample(range(M), 2)
                current_state[idx1], current_state[idx2] = current_state[idx2], current_state[idx1]
                
            current_cost, current_route = evaluate_route(current_state)

    return best_cost, best_route

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adaptive Simulated Annealing Solver")
    parser.add_argument("--time_limit", type=float, default=TIME_LIMITS.get("small", 2.0),
                        help="Time limit for the solver in seconds")
    parser.add_argument("--alpha", type=float, default=0.995,
                        help="Base cooling rate")
    parser.add_argument("--max_no_improve", type=int, default=1000,
                        help="Number of iterations without improvement before re-annealing")
    parser.add_argument("--reheat_ratio", type=float, default=0.3,
                        help="Ratio of T_start to reheat to")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    best_cost, best_route = asa_solver(
        time_limit=args.time_limit,
        alpha=args.alpha,
        max_no_improve=args.max_no_improve,
        reheat_ratio=args.reheat_ratio,
        seed=args.seed
    )
    
    # Chỉ in ra độ dài route và nội dung route theo chuẩn output
    print(len(best_route))
    print(*best_route)