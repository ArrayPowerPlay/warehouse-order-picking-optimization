"""
Phase 2 runner for Ant Colony Optimization (ACO).

This script scans all val_set testcases, skips small instances, runs the ACO
hyperparameter grid on medium/large instances, repeats each configuration on
all configured seeds, and writes results/phase2/aco.csv.

Rows are appended immediately after each finished (testcase, configuration) 
so progress is visible during long runs.
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

# --- SỬA Ở ĐÂY: Import SEEDS từ cấu hình hệ thống ---
from config.settings import SEEDS, TIME_LIMITS

# LƯU Ý: Đảm bảo đường dẫn import này khớp với thư mục dự án của bạn
from src.solvers.ant_colony.aco import aco_solver
from src.solvers.utils import read_input


VAL_SET_ROOT = os.path.join(project_root, "data", "val_set")
PHASE2_ROOT = os.path.join(project_root, "results", "phase2")
DEFAULT_OUTPUT_PATH = os.path.join(PHASE2_ROOT, "aco.csv")

# Lưới siêu tham số mẫu cho ACO (điều chỉnh tùy bài toán thực tế)
NUM_ANTS_GRID = (50, 100)
ALPHA_GRID = (1.0, 2.0)
BETA_GRID = (2.0, 3.0, 4.0)
RHO_GRID = (0.1,)

FIELDNAMES = [
    "testcase",
    "num_ants",
    "alpha",
    "beta",
    "rho",
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


def iter_hyperparameter_grid() -> list[tuple[int, float, float, float]]:
    """Return the fixed ACO grid used for Phase 2."""
    return list(product(NUM_ANTS_GRID, ALPHA_GRID, BETA_GRID, RHO_GRID))


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


# --- SỬA Ở ĐÂY: Thêm thuộc tính seed và đặt tên giống GA ---
def run_single_seed(
    input_path: str,
    time_limit: float,
    num_ants: int,
    alpha: float,
    beta: float,
    rho: float,
    seed: int,
) -> int:
    """Run one ACO configuration on one seed and return total_distance."""
    with open(input_path, encoding="utf-8") as stream:
        original_stdin = sys.stdin
        try:
            sys.stdin = stream
            _, total_distance, _ = aco_solver(
                time_limit=time_limit,
                num_ants=num_ants,
                alpha=alpha,
                beta=beta,
                rho=rho,
                seed=seed, # Truyền seed qua aco_solver
            )
        finally:
            sys.stdin = original_stdin

    return total_distance


# --- SỬA Ở ĐÂY: Thêm hàm chọn best seed giống hệt GA ---
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
    num_ants: int,
    alpha: float,
    beta: float,
    rho: float,
) -> dict[str, object]:
    """Run one testcase/configuration across all seeds and summarize it."""
    
    # --- SỬA Ở ĐÂY: Chạy đúng logic của GA với mảng SEEDS ---
    run_results = []
    for seed in SEEDS:
        total_distance = run_single_seed(
            input_path=input_path,
            time_limit=time_limit,
            num_ants=num_ants,
            alpha=alpha,
            beta=beta,
            rho=rho,
            seed=seed,
        )
        run_results.append((seed, total_distance))

    cost_min, _ = select_best_seed(run_results)
    
    return {
        "testcase": testcase_name,
        "num_ants": num_ants,
        "alpha": alpha,
        "beta": beta,
        "rho": rho,
        "cost_min": cost_min,
    }


def build_phase2_tasks(
    selected_testcases: set[str] | None = None,
) -> list[tuple[str, str, float, int, float, float, float]]:
    """Build independent Phase 2 tasks at testcase/config granularity."""
    tasks = []
    hyperparameter_grid = iter_hyperparameter_grid()

    for testcase_name, input_path, _, time_limit in discover_val_testcases(selected_testcases):
        for num_ants, alpha, beta, rho in hyperparameter_grid:
            tasks.append(
                (
                    testcase_name,
                    input_path,
                    time_limit,
                    num_ants,
                    alpha,
                    beta,
                    rho,
                )
            )

    return tasks


def run_phase2_task(task: tuple[str, str, float, int, float, float, float]) -> dict[str, object]:
    """Run one independent testcase/config task. Kept top-level for multiprocessing."""
    testcase_name, input_path, time_limit, num_ants, alpha, beta, rho = task
    return run_single_configuration(
        testcase_name=testcase_name,
        input_path=input_path,
        time_limit=time_limit,
        num_ants=num_ants,
        alpha=alpha,
        beta=beta,
        rho=rho,
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


def execute_phase2(
    selected_testcases: set[str] | None = None,
    output_path: str = DEFAULT_OUTPUT_PATH,
    workers: int = 8,
) -> int:
    """Execute Phase 2 and append rows immediately as tasks finish."""
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
                f"num_ants={row['num_ants']} | alpha={row['alpha']} | "
                f"beta={row['beta']} | rho={row['rho']} | cost_min={row['cost_min']}"
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
                    f"num_ants={row['num_ants']} | alpha={row['alpha']} | "
                    f"beta={row['beta']} | rho={row['rho']} | cost_min={row['cost_min']}"
                )

    return total_tasks


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for optional targeted runs."""
    parser = argparse.ArgumentParser(description="Phase 2 runner for Ant Colony Optimization")
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
    # --- SỬA Ở ĐÂY: Thêm tham số --workers để điều khiển số lượng worker parallel ---
    parser.add_argument(
        "--workers",
        type=int,
        default=1, # --- SỬA Ở ĐÂY: Mặc định là 1 để chạy tuần tự, tránh lỗi multiprocessing trên Windows ---
        help="Number of parallel worker processes. Default = 8.",
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
    print(f"Wrote {total_rows} rows to {args.output}")


if __name__ == "__main__":
    main()