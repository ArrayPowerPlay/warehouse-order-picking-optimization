import os
import sys
import csv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.settings import TIME_LIMITS
from src.solvers.greedy_prunning_pywrapcp.greedy_prunning_pywrapcp import pywrapcp_solver
from src.solvers.utils import read_input

TEST_SET_ROOT = os.path.join(project_root, "data", "test_set")
PHASE4_ROOT = os.path.join(project_root, "results", "phase4")

def classify_testcase_size(m: int) -> str:
    if m <= 20: return "small"
    if 50 <= m <= 400: return "medium"
    if m >= 500: return "large"
    raise ValueError(f"Cannot classify testcase with M={m}.")

def main() -> None:
    print("BẮT ĐẦU CHẠY PHASE 4: PYWRAPCP ")
    
    os.makedirs(PHASE4_ROOT, exist_ok=True)
    csv_path = os.path.join(PHASE4_ROOT, "pywrapcp.csv")
    
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["testcase", "metaheuristic", "cost_min", "cost_max", "cost_avg", "cost_std", "t_best_avg"])
        
    for filename in sorted(os.listdir(TEST_SET_ROOT)):
        if not filename.endswith(".in"):
            continue
            
        testcase_name = filename.replace(".in", "")
        input_path = os.path.join(TEST_SET_ROOT, filename)
        
        with open(input_path, encoding="utf-8") as stream:
            _, m, _, _, _ = read_input(stream)
            
        size_bucket = classify_testcase_size(m)
            
        time_limit_full = TIME_LIMITS[size_bucket]
        print(f"\n{size_bucket.upper()}: {testcase_name} (Max time: {time_limit_full}s)")
        
        # =========================================================
        # LOGIC TIME SWEEP 
        # =========================================================
        time_checkpoints = [10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 900.0]
        valid_checkpoints = [t for t in time_checkpoints if t < time_limit_full]
        if time_limit_full not in valid_checkpoints:
            valid_checkpoints.append(float(time_limit_full))

        best_distance = float('inf')
        t_best = -1.0

        for t_limit in valid_checkpoints:
            with open(input_path, encoding="utf-8") as stream:
                original_stdin = sys.stdin
                try:
                    sys.stdin = stream
                    # Gọi hàm lõi với time_limit bị ép xuống t_limit
                    route, current_distance = pywrapcp_solver(time_limit=t_limit)
                finally:
                    sys.stdin = original_stdin

            # So sánh và cập nhật kỷ lục
            if current_distance != -1 and current_distance < best_distance:
                best_distance = current_distance
                t_best = float(t_limit)
                
        # Xử lý trường hợp hoàn toàn vô nghiệm sau khi quét hết các mốc
        if best_distance == float('inf'):
            best_distance = -1
            t_best = -1.0

        with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if best_distance != -1:
                writer.writerow([
                    testcase_name, 
                    "GUIDED_LOCAL_SEARCH",
                    best_distance, # cost_min
                    best_distance, # cost_max
                    best_distance, # cost_avg
                    0.0,           # cost_std
                    t_best         # t_best_avg
                ])
            else:
                writer.writerow([testcase_name, "GUIDED_LOCAL_SEARCH", -1, -1, -1, 0.0, -1.0])
            
        # Log terminal
        if best_distance != -1:
            print(f"Cost_min = {best_distance} (t_best: {t_best}s)")
        else:
            print(f"Không tìm được nghiệm cho {testcase_name} (Đã ghi -1)")
            
    print(f"\nHOÀN THÀNH!")

if __name__ == "__main__":
    main()