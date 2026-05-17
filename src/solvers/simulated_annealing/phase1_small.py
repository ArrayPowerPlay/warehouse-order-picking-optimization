"""
Time-limit sweep runner for the small representative testcase.

This script only runs:
    data/val_set/small_04_N5_M20.in

It evaluates a list of time limits and appends one JSON record per run to:
    results/phase1/small_04_N5_M20/asa_time_limit_sweep.jsonl
"""

from __future__ import annotations

import argparse
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


SMALL_TESTCASE = "small_04_N5_M20"
INPUT_PATH = os.path.join(project_root, "data", "val_set", f"{SMALL_TESTCASE}.in")
OUTPUT_PATH = os.path.join(
    project_root,
    "results",
    "phase1",
    SMALL_TESTCASE,
    "asa_time_limit_sweep.jsonl",
)

# Edit this list directly if you want a fixed sweep in code.
TIME_LIMIT_CANDIDATES = [100, 200, 300]


def build_result_payload(route: list[int], total_distance: int, t_best: float, time_limit: float) -> dict:
    return {
        "testcase": SMALL_TESTCASE,
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


def run_with_time_limit(time_limit: float) -> dict:
    if not os.path.isfile(INPUT_PATH):
        raise FileNotFoundError(f"Missing testcase file: {INPUT_PATH}")

    with open(INPUT_PATH, encoding="utf-8") as stream:
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

    return build_result_payload(route, total_distance, t_best, time_limit)


def append_result(result: dict) -> None:
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "a", encoding="utf-8") as stream:
        stream.write(json.dumps(result, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a time-limit sweep for small_04_N5_M20.")
    parser.add_argument(
        "--time_limits",
        nargs="+",
        type=float,
        default=TIME_LIMIT_CANDIDATES,
        help="List of time limits to run sequentially.",
    )
    args = parser.parse_args()

    for time_limit in args.time_limits:
        result = run_with_time_limit(time_limit)
        append_result(result)
        print(
            f"Appended result for {SMALL_TESTCASE} with time_limit={time_limit} "
            f"to results/phase1/{SMALL_TESTCASE}/asa_time_limit_sweep.jsonl"
        )


if __name__ == "__main__":
    main()
