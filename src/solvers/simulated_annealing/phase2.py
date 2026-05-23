"""
Phase 2 detail runner for Adaptive Simulated Annealing.

This script scans all val_set testcases, skips small instances, runs the ASA
hyperparameter grid on medium/large instances, repeats each configuration on
all configured seeds, and writes one detail row per seed to
results/phase2/asa_detail.csv.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product

# Add project root to sys.path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.settings import SEEDS, TIME_LIMITS
from src.solvers.simulated_annealing.adaptive_simulated_annealing import asa_solver
from src.solvers.utils import read_input


VAL_SET_ROOT = os.path.join(project_root, "data", "val_set")
PHASE2_ROOT = os.path.join(project_root, "results", "phase2")
DEFAULT_OUTPUT_PATH = os.path.join(PHASE2_ROOT, "asa_detail.csv")

ALPHA_GRID = (0.99, 0.995, 0.999)
MAX_NO_IMPROVE_GRID = (1000, 2000)
REHEAT_RATIO_GRID = (0.2, 0.3, 0.5)

FIELDNAMES = [
    "testcase",
    "alpha",
    "max_no_improve",
    "reheat_ratio",
    "k",
    "cost",
]


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


def build_phase2_tasks(
    selected_testcases: set[str] | None = None,
) -> list[tuple[str, str, float, float, int, float, int]]:
    """Build independent Phase 2 tasks at testcase/config/seed granularity."""
    tasks = []
    hyperparameter_grid = iter_hyperparameter_grid()

    for testcase_name, input_path, _, time_limit in discover_val_testcases(selected_testcases):
        for alpha, max_no_improve, reheat_ratio in hyperparameter_grid:
            for seed in SEEDS:
                tasks.append(
                    (
                        testcase_name,
                        input_path,
                        time_limit,
                        alpha,
                        max_no_improve,
                        reheat_ratio,
                        seed,
                    )
                )

    return tasks


def run_phase2_task(task: tuple[str, str, float, float, int, float, int]) -> dict[str, object]:
    """Run one independent testcase/config/seed task."""
    testcase_name, input_path, time_limit, alpha, max_no_improve, reheat_ratio, seed = task
    cost = run_single_seed(
        input_path=input_path,
        time_limit=time_limit,
        alpha=alpha,
        max_no_improve=max_no_improve,
        reheat_ratio=reheat_ratio,
        seed=seed,
    )
    return {
        "testcase": testcase_name,
        "alpha": alpha,
        "max_no_improve": max_no_improve,
        "reheat_ratio": reheat_ratio,
        "k": seed,
        "cost": cost,
    }


def write_csv_header(output_path: str) -> None:
    """Create or overwrite CSV and write header once."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES)
        writer.writeheader()
        stream.flush()


def append_csv_row(output_path: str, row: dict[str, object]) -> None:
    """Append one finished row immediately and flush it."""
    with open(output_path, "a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES)
        writer.writerow(row)
        stream.flush()


def execute_phase2(
    selected_testcases: set[str] | None = None,
    output_path: str = DEFAULT_OUTPUT_PATH,
    workers: int = 1,
) -> int:
    """Execute Phase 2 and append detail rows immediately as tasks finish."""
    tasks = build_phase2_tasks(selected_testcases)
    write_csv_header(output_path)

    total_tasks = len(tasks)
    completed = 0

    if workers <= 1:
        for task in tasks:
            row = run_phase2_task(task)
            append_csv_row(output_path, row)
            completed += 1
            print(
                f"[{completed}/{total_tasks}] Appended {row['testcase']} | "
                f"alpha={row['alpha']} | max_no_improve={row['max_no_improve']} | "
                f"reheat_ratio={row['reheat_ratio']} | k={row['k']} | cost={row['cost']}"
            )
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(run_phase2_task, task) for task in tasks]
            for future in as_completed(futures):
                row = future.result()
                append_csv_row(output_path, row)
                completed += 1
                print(
                    f"[{completed}/{total_tasks}] Appended {row['testcase']} | "
                    f"alpha={row['alpha']} | max_no_improve={row['max_no_improve']} | "
                    f"reheat_ratio={row['reheat_ratio']} | k={row['k']} | cost={row['cost']}"
                )

    return total_tasks


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for optional targeted runs."""
    parser = argparse.ArgumentParser(description="Phase 2 detail runner for Adaptive Simulated Annealing")
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
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel worker processes. Use 1 to run sequentially.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    selected_testcases = set(args.testcase) if args.testcase else None
    total_rows = execute_phase2(
        selected_testcases=selected_testcases,
        output_path=args.output,
        workers=max(1, args.workers),
    )
    print(f"Wrote {total_rows} detail rows to {args.output}")


if __name__ == "__main__":
    main()
