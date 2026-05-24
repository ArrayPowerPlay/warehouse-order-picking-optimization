import os
import sys
import csv

# Thêm đường dẫn gốc
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.settings import TIME_LIMITS
from src.solvers.greedy.greedy import greedy_solver
from src.solvers.utils import read_input

TEST_SET_ROOT = os.path.join(project_root, "data", "test_set")
PHASE4_ROOT = os.path.join(project_root, "results", "phase4")

def classify_testcase_size(m: int) -> str:
    if m <= 20: return "small"
    if 50 <= m <= 400: return "medium"
    if m >= 500: return "large"
    raise ValueError(f"Cannot classify testcase with M={m}.")

def main() -> None:
    print("BẮT ĐẦU CHẠY PHASE 4: GREEDY")
    
    os.makedirs(PHASE4_ROOT, exist_ok=True)
    csv_path = os.path.join(PHASE4_ROOT, "greedy.csv")
    
    # Khởi tạo CSV 
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["testcase", "cost_min"])
        
    # Đọc từ TEST_SET_ROOT
    for filename in sorted(os.listdir(TEST_SET_ROOT)):
        if not filename.endswith(".in"):
            continue
            
        testcase_name = filename.replace(".in", "")
        input_path = os.path.join(TEST_SET_ROOT, filename)
        
        with open(input_path, encoding="utf-8") as stream:
            _, m, _, _, _ = read_input(stream)
            
        size_bucket = classify_testcase_size(m)
        
        # =========================================================
        # BỎ QUA TESTCASE SMALL 
        # =========================================================
        if size_bucket == "small":
            print(f"Bỏ qua SMALL: {testcase_name} ")
            continue
            
        time_limit = TIME_LIMITS[size_bucket]
        print(f"\n{size_bucket.upper()}: {testcase_name}")
        
        with open(input_path, encoding="utf-8") as stream:
            original_stdin = sys.stdin
            try:
                sys.stdin = stream
                route, total_distance, t_best = greedy_solver(time_limit=time_limit)
            finally:
                sys.stdin = original_stdin

        with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([testcase_name, total_distance])
            
        # Log terminal
        if total_distance != -1:
            print(f"Cost_min = {total_distance}")
        else:
            print(f"Không tìm được nghiệm cho {testcase_name}")
            
    print(f"\nHOÀN THÀNH!")

if __name__ == "__main__":
    main()