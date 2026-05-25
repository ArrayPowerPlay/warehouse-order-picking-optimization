"""
Phase 4 detail runner for Ant Colony Optimization.

This script scans all test_set testcases, selects the best Phase 3 ACO
configuration for each testcase size group, repeats that configuration on all
configured seeds, and writes one detail row per seed to
results/phase4/aco_detail.csv.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add project root to sys.path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.settings import SEEDS, TIME_LIMITS
from src.solvers.ant_colony.aco import aco_solver
from src.solvers.utils import read_input


TEST_SET_ROOT = os.path.join(project_root, "data", "test_set")
PHASE3_CONFIG_PATH = os.path.join(project_root, "results", "phase3", "aco.csv")
PHASE4_ROOT = os.path.join(project_root, "results", "phase4")
DEFAULT_OUTPUT_PATH = os.path.join(PHASE4_ROOT, "aco_detail.csv")

FIELDNAMES = [
    "testcase",
    "num_ants",
    "alpha",
    "beta",
    "rho",
    "k",
    "cost",
    "t_best",
]


def resolve_worker_count(requested_workers: int, total_tasks: int) -> int:
    """Resolve the effective worker count from CLI input and task count."""
    if total_tasks <= 0:
        return 1
    if requested_workers <= 0:
        cpu_count = os.cpu_count() or 1
        return max(1, min(cpu_count, total_tasks))
    return max(1, min(requested_workers, total_tasks))


def classify_testcase_size(m: int) -> str:
    """Classify testcase size bucket from M."""
    if m <= 20:
        return "small"
    if 50 <= m <= 400:
        return "medium"
    if m >= 500:
        return "large"
    raise ValueError(f"Cannot classify testcase with M={m}.")


def load_best_configs() -> dict[str, tuple[int, float, float, float]]:
    """Load best ACO configuration per size group from Phase 3 output."""
    if not os.path.isfile(PHASE3_CONFIG_PATH):
        raise FileNotFoundError(f"Missing Phase 3 ACO config file: {PHASE3_CONFIG_PATH}")

    best_configs = {}
    with open(PHASE3_CONFIG_PATH, encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            best_configs[row["group"]] = (
                int(row["num_ants"]),
                float(row["alpha"]),
                float(row["beta"]),
                float(row["rho"]),
            )

    if not best_configs:
        raise RuntimeError(f"No Phase 3 ACO configurations found in {PHASE3_CONFIG_PATH}")
    return best_configs


def discover_testcases(selected_testcases: set[str] | None = None) -> list[tuple[str, str, str, float]]:
    """Discover test_set testcases and their time limits."""
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
        testcases.append((testcase_name, input_path, size_bucket, TIME_LIMITS[size_bucket]))

    return testcases


def run_single_seed(
    input_path: str,
    time_limit: float,
    num_ants: int,
    alpha: float,
    beta: float,
    rho: float,
    seed: int,
) -> tuple[int, float]:
    """Run one ACO configuration on one seed and return total_distance and t_best."""
    with open(input_path, encoding="utf-8") as stream:
        original_stdin = sys.stdin
        try:
            sys.stdin = stream
            _, total_distance, t_best = aco_solver(
                time_limit=time_limit,
                num_ants=num_ants,
                alpha=alpha,
                beta=beta,
                rho=rho,
                seed=seed,
            )
        finally:
            sys.stdin = original_stdin

    return total_distance, float(t_best)


def build_phase4_tasks(
    selected_testcases: set[str] | None = None,
) -> list[tuple[str, str, float, int, float, float, float, int]]:
    """Build independent Phase 4 tasks at testcase/config/seed granularity."""
    tasks = []
    best_configs = load_best_configs()

    for testcase_name, input_path, size_bucket, time_limit in discover_testcases(selected_testcases):
        if size_bucket not in best_configs:
            print(f"[WARNING] Missing ACO config for group '{size_bucket}', skip testcase {testcase_name}")
            continue

        num_ants, alpha, beta, rho = best_configs[size_bucket]
        for seed in SEEDS:
            tasks.append(
                (
                    testcase_name,
                    input_path,
                    time_limit,
                    num_ants,
                    alpha,
                    beta,
                    rho,
                    seed,
                )
            )

    return tasks


def run_phase4_task(task: tuple[str, str, float, int, float, float, float, int]) -> dict[str, object]:
    """Run one independent testcase/config/seed task."""
    testcase_name, input_path, time_limit, num_ants, alpha, beta, rho, seed = task
    cost, t_best = run_single_seed(
        input_path=input_path,
        time_limit=time_limit,
        num_ants=num_ants,
        alpha=alpha,
        beta=beta,
        rho=rho,
        seed=seed,
    )
    return {
        "testcase": testcase_name,
        "num_ants": num_ants,
        "alpha": alpha,
        "beta": beta,
        "rho": rho,
        "k": seed,
        "cost": cost,
        "t_best": round(t_best, 6),
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


def execute_phase4(
    selected_testcases: set[str] | None = None,
    output_path: str = DEFAULT_OUTPUT_PATH,
    workers: int = 1,
) -> int:
    """Execute Phase 4 and append detail rows immediately as tasks finish."""
    tasks = build_phase4_tasks(selected_testcases)
    write_csv_header(output_path)

    total_tasks = len(tasks)
    effective_workers = resolve_worker_count(workers, total_tasks)
    completed = 0

    print(
        f"[*] Phase 4 ACO detail run: tasks={total_tasks}, requested_workers={workers}, "
        f"effective_workers={effective_workers}"
    )

    if effective_workers <= 1:
        for task in tasks:
            row = run_phase4_task(task)
            append_csv_row(output_path, row)
            completed += 1
            print(
                f"[{completed}/{total_tasks}] Appended {row['testcase']} | "
                f"num_ants={row['num_ants']} | alpha={row['alpha']} | beta={row['beta']} | "
                f"rho={row['rho']} | k={row['k']} | cost={row['cost']} | t_best={row['t_best']}"
            )
    else:
        with ProcessPoolExecutor(max_workers=effective_workers) as executor:
            futures = [executor.submit(run_phase4_task, task) for task in tasks]
            for future in as_completed(futures):
                row = future.result()
                append_csv_row(output_path, row)
                completed += 1
                print(
                    f"[{completed}/{total_tasks}] Appended {row['testcase']} | "
                    f"num_ants={row['num_ants']} | alpha={row['alpha']} | beta={row['beta']} | "
                    f"rho={row['rho']} | k={row['k']} | cost={row['cost']} | t_best={row['t_best']}"
                )

    return total_tasks


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for optional targeted runs."""
    parser = argparse.ArgumentParser(description="Phase 4 detail runner for Ant Colony Optimization")
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
        default=0,
        help="Number of parallel worker processes. Use 0 to auto-select, 1 to run sequentially.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    selected_testcases = set(args.testcase) if args.testcase else None
    total_rows = execute_phase4(
        selected_testcases=selected_testcases,
        output_path=args.output,
        workers=args.workers,
    )
    print(f"Wrote {total_rows} detail rows to {args.output}")


if __name__ == "__main__":
    main()
