import json
import os
import sys
import re

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.settings import TIME_LIMIT_TESTING
from src.solvers.greedy_prunning_pywrapcp.greedy_prunning_pywrapcp import pywrapcp_solver
from src.solvers.utils import read_input

REPRESENTATIVE_ROOT = os.path.join(project_root, "results", "phase1")
VAL_SET_ROOT = os.path.join(project_root, "data", "val_set")

def classify_testcase_size(m: int) -> str:
    if m <= 20: return "small"
    if 50 <= m <= 400: return "medium"
    if m >= 500: return "large"
    raise ValueError(f"Cannot classify testcase with M={m}.")

def get_representative_testcases() -> list[str]:
    testcases = []
    for name in sorted(os.listdir(REPRESENTATIVE_ROOT)):
        if os.path.isdir(os.path.join(REPRESENTATIVE_ROOT, name)):
            testcases.append(name)
    return testcases

def get_testcase_info(testcase_name: str) -> tuple[str, str, float]:
    input_path = os.path.join(VAL_SET_ROOT, f"{testcase_name}.in")
    with open(input_path, encoding="utf-8") as stream:
        _, m, _, _, _ = read_input(stream)
    size_bucket = classify_testcase_size(m)
    return input_path, size_bucket, TIME_LIMIT_TESTING[size_bucket]

def build_result_payload(route: list[int], total_distance: int, t_best: float, time_limit: float) -> dict:
    return {
        "route": route,
        "total_distance": total_distance,
        "t_best": t_best,
        "time_limit": time_limit,
        "hyperparameters": {
            "metaheuristic": "GUIDED_LOCAL_SEARCH"
        }
    }

def run_single_testcase(testcase_name: str) -> dict:
    input_path, size_bucket, time_limit_full = get_testcase_info(testcase_name)
    
    # =========================================================
    # LOGIC TIME SWEEP 
    # =========================================================
    time_checkpoints = [10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 900.0]
    valid_checkpoints = [t for t in time_checkpoints if t < time_limit_full]
    if time_limit_full not in valid_checkpoints:
        valid_checkpoints.append(float(time_limit_full))

    best_distance = float('inf')
    best_route = []
    t_best = -1.0

    print(f"{size_bucket.upper()}: {testcase_name}")
    
    for t_limit in valid_checkpoints:
        # PHẢI MỞ LẠI FILE Ở MỖI VÒNG LẶP vì sys.stdin bị consume sau mỗi lần chạy
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
            best_route = route
            t_best = float(t_limit)
            
    # Trường hợp thuật toán vô nghiệm hoàn toàn ở mọi mốc
    if best_distance == float('inf'):
        best_distance = -1
        best_route = []
        t_best = -1.0

    # Đóng gói và ghi JSON
    result = build_result_payload(best_route, best_distance, t_best, time_limit_full)
    output_path = os.path.join(REPRESENTATIVE_ROOT, testcase_name, "pywrapcp.json")
    
    json_str = json.dumps(result, indent=4)
    # Regex ép mảng "route" nằm ngang cho đẹp
    json_str = re.sub(
        r'("route": \[\s*)(.*?)(\s*\])', 
        lambda m: '"route": [' + re.sub(r'\s+', ' ', m.group(2)).strip() + ']', 
        json_str, 
        flags=re.DOTALL
    )
    
    with open(output_path, "w", encoding="utf-8") as stream:
        stream.write(json_str)
        
    return result

def main() -> None:
    print("BẮT ĐẦU CHẠY PHASE 1: TIME SWEEP CHO PYWRAPCP")
    for testcase_name in get_representative_testcases():
        run_single_testcase(testcase_name)
        print(f"Đã ghi kết quả vào results/phase1/{testcase_name}/pywrapcp.json\n")

if __name__ == "__main__":
    main()