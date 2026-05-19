"""
Phase 1 runner for Ant Colony Optimization (ACO).

This script scans representative cases from results/phase1, runs ACO with
default hyperparameters on the matching files in data/val_set, and writes
results/phase1/<testcase>/aco.json.
"""

from __future__ import annotations
import json
import os
import sys

# Add project root to sys.path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.settings import TIME_LIMIT_TESTING

# Import bộ ACO (Tùy chỉnh lại đường dẫn import nếu bạn đặt thư mục khác)
# Giả sử bạn đặt aco.py tại src/solvers/ant_colony/aco.py
from src.solvers.ant_colony.aco import (
    DEFAULT_NUM_ANTS,
    DEFAULT_ALPHA,
    DEFAULT_BETA,
    DEFAULT_RHO,
    aco_solver,
)
from src.solvers.utils import read_input

REPRESENTATIVE_ROOT = os.path.join(project_root, "results", "phase1")
VAL_SET_ROOT = os.path.join(project_root, "data", "val_set")

def classify_testcase_size(m: int) -> str:
    """Classify testcase's size into small, medium, and large."""
    if m <= 20:
        return "small"
    if 50 <= m <= 400:
        return "medium"
    if m >= 500:
        return "large"
    raise ValueError(f"Cannot classify testcase with M={m}.")

def get_representative_testcases() -> list[str]:
    """Get all representative testcases used for determine TIME_LIMIT from results/phase1."""
    if not os.path.isdir(REPRESENTATIVE_ROOT):
        raise FileNotFoundError(f"Representative root not found: {REPRESENTATIVE_ROOT}")

    testcases = []
    for name in sorted(os.listdir(REPRESENTATIVE_ROOT)):
        testcase_dir = os.path.join(REPRESENTATIVE_ROOT, name)
        if os.path.isdir(testcase_dir):
            testcases.append(name)

    if not testcases:
        raise RuntimeError("No representative Phase 1 testcases found in results/phase1.")
    return testcases

def get_testcase_info(testcase_name: str) -> tuple[str, str, float]:
    """From a testcase's name, return its path, classified size, and time limit used for running."""
    input_path = os.path.join(VAL_SET_ROOT, f"{testcase_name}.in")
    if not os.path.isfile(input_path):
        raise FileNotFoundError(
            f"Missing matching val_set file for representative testcase: {input_path}"
        )

    with open(input_path, encoding="utf-8") as stream:
        _, m, _, _, _ = read_input(stream)

    size_bucket = classify_testcase_size(m)
    time_limit = TIME_LIMIT_TESTING[size_bucket]
    return input_path, size_bucket, time_limit

def build_result_payload(route: list[int], total_distance: int, t_best: float, time_limit: float) -> dict:
    """Build payload to save running's result as a JSON files."""
    return {
        "route": route,
        "total_distance": total_distance,
        "t_best": t_best,
        "time_limit": time_limit,
        "hyperparameters": {
            "num_ants": DEFAULT_NUM_ANTS,
            "alpha": DEFAULT_ALPHA,
            "beta": DEFAULT_BETA,
            "rho": DEFAULT_RHO,
        },
    }

def run_single_testcase(testcase_name: str) -> dict:
    """Run a testcase and save result into 'results/phase1/testcase_name'."""
    input_path, _, time_limit = get_testcase_info(testcase_name)

    with open(input_path, encoding="utf-8") as stream:
        original_stdin = sys.stdin
        try:
            # Điều hướng luồng stdin thành file input
            sys.stdin = stream
            # Chạy hàm thuật toán ACO
            route, total_distance, t_best = aco_solver(
                time_limit=time_limit,
                num_ants=DEFAULT_NUM_ANTS,
                alpha=DEFAULT_ALPHA,
                beta=DEFAULT_BETA,
                rho=DEFAULT_RHO,
            )
        finally:
            # Phục hồi stdin
            sys.stdin = original_stdin

    result = build_result_payload(route, total_distance, t_best, time_limit)
    
    # Lưu dưới tên aco.json
    output_path = os.path.join(REPRESENTATIVE_ROOT, testcase_name, "aco.json")
    with open(output_path, "w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=4)
    return result

def main() -> None:
    testcases = get_representative_testcases()
    total = len(testcases)
    print(f"🚀 TÌM THẤY {total} TEST CASES. BẮT ĐẦU CHẠY PHASE 1 CHO ACO...")
    print("=" * 60)

    for idx, testcase_name in enumerate(testcases, 1):
        print(f"[{idx}/{total}] Đang xử lý: {testcase_name} ... ", end="", flush=True)
        run_single_testcase(testcase_name)
        print("✅ Hoàn thành!")

if __name__ == "__main__":
    main()