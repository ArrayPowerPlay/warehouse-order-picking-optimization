"""
Phase 1 runner for Adaptive Simulated Annealing.

This script scans representative cases from results/phase1, runs ASA with
default hyperparameters on the matching files in data/val_set, and writes
results/phase1/<testcase>/asa.json.
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
from src.solvers.simulated_annealing.adaptive_simulated_annealing import (
    DEFAULT_ALPHA,
    DEFAULT_MAX_NO_IMPROVE,
    DEFAULT_REHEAT_RATIO,
    DEFAULT_SEED,
    asa_solver,
)
from src.solvers.utils import read_input


REPRESENTATIVE_ROOT = os.path.join(project_root, "results", "phase1")
VAL_SET_ROOT = os.path.join(project_root, "data", "val_set")


def classify_testcase_size(m: int) -> str:
    if m <= 20:
        return "small"
    if 50 <= m <= 400:
        return "medium"
    if m >= 500:
        return "large"
    raise ValueError(f"Cannot classify testcase with M={m}.")


def get_representative_testcases() -> list[str]:
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
    return {
        "route": route,
        "total_distance": total_distance,
        "t_best": t_best,
        "time_limit": time_limit,
        "hyperparameters": {
            "alpha": DEFAULT_ALPHA,
            "max_no_improve": DEFAULT_MAX_NO_IMPROVE,
            "reheat_ratio": DEFAULT_REHEAT_RATIO,
        },
    }


def run_single_testcase(testcase_name: str) -> dict:
    input_path, _, time_limit = get_testcase_info(testcase_name)

    with open(input_path, encoding="utf-8") as stream:
        original_stdin = sys.stdin
        try:
            sys.stdin = stream
            route, total_distance, t_best = asa_solver(
                time_limit=time_limit,
                alpha=DEFAULT_ALPHA,
                max_no_improve=DEFAULT_MAX_NO_IMPROVE,
                reheat_ratio=DEFAULT_REHEAT_RATIO,
                seed=DEFAULT_SEED,
            )
        finally:
            sys.stdin = original_stdin

    result = build_result_payload(route, total_distance, t_best, time_limit)
    output_path = os.path.join(REPRESENTATIVE_ROOT, testcase_name, "asa.json")
    with open(output_path, "w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=4)
    return result


def main() -> None:
    for testcase_name in get_representative_testcases():
        run_single_testcase(testcase_name)
        print(f"Wrote results/phase1/{testcase_name}/asa.json")


if __name__ == "__main__":
    main()
