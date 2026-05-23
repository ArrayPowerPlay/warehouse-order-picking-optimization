"""
Phase 4 runner for Adaptive Simulated Annealing.

This script scans all test_set testcases, skips small instances, runs the ASA
hyperparameter grid on medium/large instances, repeats each configuration on
all configured seeds, and writes results/phase4/asa.csv.

Rows are appended immediately after each finished (testcase, configuration) so
progress is visible during long runs.
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


TEST_SET_ROOT = os.path.join(project_root, "data", "test_set")
PHASE4_ROOT = os.path.join(project_root, "results", "phase4")
DEFAULT_OUTPUT_PATH = os.path.join(PHASE4_ROOT, "asa.csv")

ALPHA_GRID = (0.99, 0.995, 0.999)
MAX_NO_IMPROVE_GRID = (1000, 2000)
REHEAT_RATIO_GRID = (0.2, 0.3, 0.5)

FIELDNAMES = [
    "testcase",
    "alpha",
    "max_no_improve",
    "reheat_ratio",
    "cost_min",
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
    """Return the fixed ASA grid used for Phase 4."""
    return list(product(ALPHA_GRID, MAX_NO_IMPROVE_GRID, REHEAT_RATIO_GRID))


def discover_test_testcases(selected_testcases: set[str] | None = None) -> list[tuple[str, str, str, float]]:
    """Discover medium/large test_set testcases and their time limits."""
    testcases = []

    for filename in sorted(os.listdir(TEST_SET_ROOT)):
        if not filename.endswith(".in"):
            continue

        testcase_name, _ = os.path.splitext(filename)
        if selected_testcases is not None and testcase_name not in selected_testcases:
            continue

        input_path = os.path.join(TEST_SET_ROOT, filename)
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

    cost_min, _ = select_best_seed(run_results)
    return {
        "testcase": testcase_name,
        "alpha": alpha,
        "max_no_improve": max_no_improve,
        "reheat_ratio": reheat_ratio,
        "cost_min": cost_min,
    }


def build_phase4_tasks(
    selected_testcases: set[str] | None = None,
) -> list[tuple[str, str, float, float, int, float]]:
    """Build independent Phase 4 tasks at testcase/config granularity."""
    tasks = []
    hyperparameter_grid = iter_hyperparameter_grid()

    for testcase_name, input_path, _, time_limit in discover_test_testcases(selected_testcases):
        for alpha, max_no_improve, reheat_ratio in hyperparameter_grid:
            tasks.append(
                (
                    testcase_name,
                    input_path,
                    time_limit,
                    alpha,
                    max_no_improve,
                    reheat_ratio,
                )
            )

    return tasks


def run_phase4_task(task: tuple[str, str, float, float, int, float]) -> dict[str, object]:
    """Run one independent testcase/config task. Kept top-level for multiprocessing."""
    testcase_name, input_path, time_limit, alpha, max_no_improve, reheat_ratio = task
    return run_single_configuration(
        testcase_name=testcase_name,
        input_path=input_path,
        time_limit=time_limit,
        alpha=alpha,
        max_no_improve=max_no_improve,
        reheat_ratio=reheat_ratio,
    )


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


def execute_phase4(
    selected_testcases: set[str] | None = None,
    output_path: str = DEFAULT_OUTPUT_PATH,
    workers: int = 1,
) -> int:
    """Execute Phase 4 and append rows immediately as tasks finish."""
    tasks = build_phase4_tasks(selected_testcases)
    write_csv_header(output_path)

    total_tasks = len(tasks)
    completed = 0

    if workers <= 1:
        for task in tasks:
            row = run_phase4_task(task)
            append_csv_row(output_path, row)
            completed += 1
            print(
                f"[{completed}/{total_tasks}] Appended {row['testcase']} | "
                f"alpha={row['alpha']} | max_no_improve={row['max_no_improve']} | "
                f"reheat_ratio={row['reheat_ratio']} | cost_min={row['cost_min']}"
            )
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(run_phase4_task, task) for task in tasks]
            for future in as_completed(futures):
                row = future.result()
                append_csv_row(output_path, row)
                completed += 1
                print(
                    f"[{completed}/{total_tasks}] Appended {row['testcase']} | "
                    f"alpha={row['alpha']} | max_no_improve={row['max_no_improve']} | "
                    f"reheat_ratio={row['reheat_ratio']} | cost_min={row['cost_min']}"
                )

    return total_tasks


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for optional targeted runs."""
    parser = argparse.ArgumentParser(description="Phase 4 runner for Adaptive Simulated Annealing")
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
    total_rows = execute_phase4(
        selected_testcases=selected_testcases,
        output_path=args.output,
        workers=max(1, args.workers),
    )
    print(f"Wrote {total_rows} rows to {args.output}")


if __name__ == "__main__":
    main()
