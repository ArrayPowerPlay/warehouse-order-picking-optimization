import json
import os
import sys
import re

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.settings import TIME_LIMIT_TESTING
from src.solvers.greedy.greedy import greedy_solver
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
        "hyperparameters": {} 
    }

def run_single_testcase(testcase_name: str) -> dict:
    input_path, _, time_limit = get_testcase_info(testcase_name)
    with open(input_path, encoding="utf-8") as stream:
        original_stdin = sys.stdin
        try:
            sys.stdin = stream
            route, total_distance, t_best = greedy_solver(time_limit=time_limit)
        finally:
            sys.stdin = original_stdin

    result = build_result_payload(route, total_distance, t_best, time_limit)
    output_path = os.path.join(REPRESENTATIVE_ROOT, testcase_name, "greedy.json")
    
    json_str = json.dumps(result, indent=4)
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
    for testcase_name in get_representative_testcases():
        run_single_testcase(testcase_name)
        print(f" Wrote results/phase1/{testcase_name}/greedy.json\n")

if __name__ == "__main__":
    main()