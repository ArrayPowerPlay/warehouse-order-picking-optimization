import os
import sys
import csv

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Lấy TIME_LIMITS
from config.settings import TIME_LIMITS
from src.solvers.cp_sat.cp_sat import cpsat_solver
from src.solvers.utils import read_input

TEST_SET_ROOT = os.path.join(project_root, "data", "test_set")
PHASE4_ROOT = os.path.join(project_root, "results", "phase4")

def classify_testcase_size(m: int) -> str:
    """Classify testcase's size into small, medium, and large."""
    if m <= 20: return "small"
    if 50 <= m <= 400: return "medium"
    if m >= 500: return "large"
    raise ValueError(f"Cannot classify testcase with M={m}.")

def main() -> None:
    print("BẮT ĐẦU CHẠY PHASE 4: CP-SAT")
    
    # Tạo thư mục results/phase4
    os.makedirs(PHASE4_ROOT, exist_ok=True)
    csv_path = os.path.join(PHASE4_ROOT, "cpsat.csv")
    
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["testcase", "num_search_workers", "cost_min", "cost_max", "cost_avg", "cost_std", "t_best_avg"])
        
    # Quét trực tiếp toàn bộ file trong data/test_set
    for filename in sorted(os.listdir(TEST_SET_ROOT)):
        if not filename.endswith(".in"):
            continue
            
        testcase_name = filename.replace(".in", "")
        input_path = os.path.join(TEST_SET_ROOT, filename)
        
        # Đọc nháp để lấy M phân loại size
        with open(input_path, encoding="utf-8") as stream:
            _, m, _, _, _ = read_input(stream)
            
        size_bucket = classify_testcase_size(m)
        
        if size_bucket == "large":
            print(f"Bỏ qua {testcase_name} (Size: {size_bucket})")
            continue
            
        # Lấy time_limit chính thức
        time_limit = TIME_LIMITS[size_bucket]
        print(f"\n{size_bucket.upper()}: {testcase_name} ")
        
        # Chạy thuật toán
        with open(input_path, encoding="utf-8") as stream:
            original_stdin = sys.stdin
            try:
                sys.stdin = stream
                num_workers = 0 
                # Nhận cả t_best từ hàm giải
                route, total_distance, t_best = cpsat_solver(time_limit=time_limit, num_search_workers=num_workers)
            finally:
                sys.stdin = original_stdin

        with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if total_distance != -1:
                # Vì là thuật toán tất định (chạy 1 lần), nên min=max=avg, std=0
                writer.writerow([
                    testcase_name, 
                    num_workers, 
                    total_distance, # cost_min
                    total_distance, # cost_max
                    total_distance, # cost_avg
                    0.0,            # cost_std
                    t_best          # t_best_avg
                ])
            else:
                # Trường hợp vô nghiệm
                writer.writerow([testcase_name, num_workers, -1, -1, -1, 0.0, -1.0])
            
        # Log terminal
        if total_distance != -1:
            print(f"BFS_Cost = {total_distance} (t_best: {t_best}s)")
        else:
            print(f"Không tìm được nghiệm cho {testcase_name}")
            
    print(f"\nHOÀN THÀNH !")

if __name__ == "__main__":
    main()