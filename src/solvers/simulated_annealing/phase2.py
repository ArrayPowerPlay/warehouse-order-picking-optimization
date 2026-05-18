"""
Phase 2 runner for Adaptive Simulated Annealing.

This script scans all val_set testcases, skips small instances, runs the ASA
hyperparameter grid on medium/large instances, repeats each configuration on
all configured seeds, and writes results/phase2/asa.csv.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from itertools import product   # Create a Descartes product among groups of values.

# Add project root to sys.path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.settings import SEEDS, TIME_LIMITS
from src.solvers.simulated_annealing.adaptive_simulated_annealing import asa_solver
from src.solvers.utils import read_input


VAL_SET_ROOT = os.path.join(project_root, "data", "val_set")
PHASE2_ROOT = os.path.join(project_root, "results", "phase2")
DEFAULT_OUTPUT_PATH = os.path.join(PHASE2_ROOT, "asa.csv")

ALPHA_GRID = (0.99, 0.995, 0.999)
MAX_NO_IMPROVE_GRID = (1000, 2000)
REHEAT_RATIO_GRID = (0.2, 0.3, 0.5)


def classify_testcase_size(m: int) -> str:
    """Classify testcase size bucket from M."""
    if m <= 20:
        return "small"
    if 50 <= m <= 400:
        return "medium"
    if m >= 500:
        return "large"
    raise ValueError(f"Cannot classify testcase with M={m}.")


def iter_hyperparameter_grid() -> list[tuple[float, int, float]]:
    """Return the fixed ASA grid used for Phase 2 / 3."""
    return list(product(ALPHA_GRID, MAX_NO_IMPROVE_GRID, REHEAT_RATIO_GRID))


def discover_val_testcases(selected_testcases: set[str] | None = None) -> list[tuple[str, str, str, float]]:
    """Discover medium/large val_set testcases and their time limits."""
    testcases = []

    for filename in sorted(os.listdir(VAL_SET_ROOT)):
        if not filename.endswith(".in"):
            continue

        testcase_name, _ = os.path.splitext(filename)
        if selected_testcases is not None and testcase_name not in selected_testcases:
            continue

        input_path = os.path.join(VAL_SET_ROOT, filename)
        with open(input_path, encoding="utf-8") as stream:
            _, m, _, _, _ = read_input(stream)

        size_bucket = classify_testcase_size(m)
        if size_bucket == "small":
            continue

        testcases.append((testcase_name, input_path, size_bucket, TIME_LIMITS[size_bucket]))

    return testcases


def run_single_seed(
    input_path: str,
    time_limit: float,
    alpha: float,
    max_no_improve: int,
    reheat_ratio: float,
    seed: int,
) -> int:
    """Run one ASA configuration on one seed and return total_distance."""
    with open(input_path, encoding="utf-8") as stream:
        original_stdin = sys.stdin
        try:
            sys.stdin = stream
            _, total_distance, _ = asa_solver(
                time_limit=time_limit,
                alpha=alpha,
                max_no_improve=max_no_improve,
                reheat_ratio=reheat_ratio,
                seed=seed,
            )
        finally:
            sys.stdin = original_stdin

    return total_distance


def select_best_seed(run_results: list[tuple[int, int]]) -> tuple[int, int | None]:
    """
    Select the best seed result for one configuration.

    Each item in run_results is (seed, total_distance).
    If at least one feasible result exists, choose the minimum feasible cost and
    its seed. If all results are infeasible, return (-1, None).
    """
    feasible_results = [(seed, cost) for seed, cost in run_results if cost >= 0]
    if not feasible_results:
        return -1, None

    best_seed, best_cost = min(feasible_results, key=lambda item: (item[1], item[0]))
    return best_cost, best_seed


def run_single_configuration(
    testcase_name: str,
    input_path: str,
    time_limit: float,
    alpha: float,
    max_no_improve: int,
    reheat_ratio: float,
) -> dict[str, object]:
    """Run one testcase/configuration across all seeds and summarize it."""
    run_results = []
    for seed in SEEDS:
        total_distance = run_single_seed(
            input_path=input_path,
            time_limit=time_limit,
            alpha=alpha,
            max_no_improve=max_no_improve,
            reheat_ratio=reheat_ratio,
            seed=seed,
        )
        run_results.append((seed, total_distance))

    cost_min, best_seed = select_best_seed(run_results)
    return {
        "testcase": testcase_name,
        "alpha": alpha,
        "max_no_improve": max_no_improve,
        "reheat_ratio": reheat_ratio,
        "cost_min": cost_min,
        "best_seed": "" if best_seed is None else best_seed,
    }


def collect_phase2_rows(selected_testcases: set[str] | None = None) -> list[dict[str, object]]:
    """Collect all Phase 2 rows for ASA on medium/large val_set testcases."""
    rows = []
    hyperparameter_grid = iter_hyperparameter_grid()

    for testcase_name, input_path, _, time_limit in discover_val_testcases(selected_testcases):
        for alpha, max_no_improve, reheat_ratio in hyperparameter_grid:
            row = run_single_configuration(
                testcase_name=testcase_name,
                input_path=input_path,
                time_limit=time_limit,
                alpha=alpha,
                max_no_improve=max_no_improve,
                reheat_ratio=reheat_ratio,
            )
            rows.append(row)

    return rows


def write_phase2_csv(rows: list[dict[str, object]], output_path: str = DEFAULT_OUTPUT_PATH) -> None:
    """Write Phase 2 ASA results to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        "testcase",
        "alpha",
        "max_no_improve",
        "reheat_ratio",
        "cost_min",
        "best_seed",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for optional targeted runs."""
    parser = argparse.ArgumentParser(description="Phase 2 runner for Adaptive Simulated Annealing")
    parser.add_argument(
        "--testcase",
        action="append",
        help="Specific testcase name without .in. Can be used multiple times.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_PATH,
        help="Output CSV path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    selected_testcases = set(args.testcase) if args.testcase else None
    rows = collect_phase2_rows(selected_testcases)
    write_phase2_csv(rows, args.output)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
