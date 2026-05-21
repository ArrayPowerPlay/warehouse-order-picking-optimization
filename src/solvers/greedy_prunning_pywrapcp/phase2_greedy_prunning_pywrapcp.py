import os
import sys
import csv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.settings import TIME_LIMITS
from src.solvers.greedy_prunning_pywrapcp.greedy_prunning_pywrapcp import pywrapcp_solver
from src.solvers.utils import read_input

VAL_SET_ROOT = os.path.join(project_root, "data", "val_set")
PHASE2_ROOT = os.path.join(project_root, "results", "phase2")

def classify_testcase_size(m: int) -> str:
    if m <= 20: return "small"
    if 50 <= m <= 400: return "medium"
    if m >= 500: return "large"
    raise ValueError(f"Cannot classify testcase with M={m}.")

def main() -> None:
    print("BẮT ĐẦU CHẠY PHASE 2: PYWRAPCP")
    
    os.makedirs(PHASE2_ROOT, exist_ok=True)
    csv_path = os.path.join(PHASE2_ROOT, "pywrapcp.csv")
    
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["testcase", "metaheuristic", "cost_min"])
        
    for filename in sorted(os.listdir(VAL_SET_ROOT)):
        if not filename.endswith(".in"):
            continue
            
        testcase_name = filename.replace(".in", "")
        input_path = os.path.join(VAL_SET_ROOT, filename)
        
        with open(input_path, encoding="utf-8") as stream:
            _, m, _, _, _ = read_input(stream)
            
        size_bucket = classify_testcase_size(m)
        
        # =========================================================
        # BỎ QUA TESTCASE SMALL 
        # =========================================================
        if size_bucket == "small":
            print(f"Bỏ qua SMALL: {testcase_name}")
            continue
            
        time_limit = TIME_LIMITS[size_bucket]
        
        print(f"{size_bucket.upper()}: {testcase_name} ")
        
        with open(input_path, encoding="utf-8") as stream:
            original_stdin = sys.stdin
            try:
                sys.stdin = stream
                route, total_distance = pywrapcp_solver(time_limit=time_limit)
            finally:
                sys.stdin = original_stdin

        if total_distance != -1:
            with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([testcase_name, "GUIDED_LOCAL_SEARCH", total_distance])
            print(f"Cost_min = {total_distance} ")
        else:
            print(f"Không tìm được nghiệm cho {testcase_name}")
            
    print(f"HOÀN THÀNH!")

if __name__ == "__main__":
    main()