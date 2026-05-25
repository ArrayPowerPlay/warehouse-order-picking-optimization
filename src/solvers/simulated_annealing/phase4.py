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

# =========================================================================
# --- THÊM VÀO: Đường dẫn tới file config tốt nhất từ Phase 3 và file detail ---
PHASE3_CONFIG_PATH = os.path.join(project_root, "results", "phase3", "asa.csv")
DETAIL_OUTPUT_PATH = os.path.join(PHASE4_ROOT, "asa_detail.csv")
# =========================================================================

# =========================================================================
# --- SỬA Ở ĐÂY: Vô hiệu hoá lưới siêu tham số tĩnh vì sẽ lấy từ Phase 3 ---
# ALPHA_GRID = (0.99, 0.995, 0.999)
# MAX_NO_IMPROVE_GRID = (1000, 2000)
# REHEAT_RATIO_GRID = (0.1, 0.2, 0.3)
# =========================================================================

# =========================================================================
# --- SỬA Ở ĐÂY: Cập nhật FIELDNAMES theo yêu cầu và thêm DETAIL_FIELDNAMES ---
FIELDNAMES = [
    "testcase",
    "alpha",
    "max_no_improve",
    "reheat_ratio",
    "cost_min",
    "cost_avg", # THÊM VÀO: Thêm cột cost_avg
]

DETAIL_FIELDNAMES = [
    "testcase",
    "alpha",
    "max_no_improve",
    "reheat_ratio",
    "k",          # THÊM VÀO: Tham số k
    "cost",       # THÊM VÀO: Cost chi tiết từng lần chạy
]
# =========================================================================


def classify_testcase_size(m: int) -> str:
    """Classify testcase size bucket from M."""
    if m <= 20:
        return "small"
    if 50 <= m <= 400:
        return "medium"
    if m >= 500:
        return "large"
    raise ValueError(f"Cannot classify testcase with M={m}.")


# =========================================================================
# --- THÊM VÀO: Hàm đọc kết quả Phase 3 để lấy cấu hình tốt nhất ---
def load_best_configs() -> dict[str, tuple[float, int, float]]:
    """Đọc file kết quả phase3 và trả về dict map group -> config tốt nhất."""
    configs = {}
    if not os.path.exists(PHASE3_CONFIG_PATH):
        raise FileNotFoundError(f"Không tìm thấy file cấu hình {PHASE3_CONFIG_PATH}. Vui lòng chạy Phase 3 trước.")
    
    with open(PHASE3_CONFIG_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            group = row["group"]
            alpha = float(row["alpha"])
            max_no_improve = int(row["max_no_improve"])
            reheat_ratio = float(row["reheat_ratio"])
            configs[group] = (alpha, max_no_improve, reheat_ratio)
    return configs
# =========================================================================


# =========================================================================
# --- SỬA Ở ĐÂY: Vô hiệu hoá hàm tạo lưới cũ ---
# def iter_hyperparameter_grid() -> list[tuple[float, int, float]]:
#     """Return the fixed ASA grid used for Phase 4."""
#     return list(product(ALPHA_GRID, MAX_NO_IMPROVE_GRID, REHEAT_RATIO_GRID))
# =========================================================================


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
        
        # =========================================================================
        # --- SỬA Ở ĐÂY: Bỏ qua lệnh skip testcase small ---
        # if size_bucket == "small":
        #     continue
        # =========================================================================

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


# =========================================================================
# --- SỬA Ở ĐÂY: Hàm này không dùng nữa, logic tính toán được gộp vào bên dưới ---
# def select_best_seed(run_results: list[tuple[int, int]]) -> tuple[int, int | None]:
#     ...
# =========================================================================


def run_single_configuration(
    testcase_name: str,
    input_path: str,
    time_limit: float,
    alpha: float,
    max_no_improve: int,
    reheat_ratio: float,
) -> tuple[dict[str, object], list[dict[str, object]]]: # --- SỬA Ở ĐÂY: Trả về đồng thời kết quả tổng hợp và chi tiết
    """Run one testcase/configuration across all seeds and summarize it."""
    run_results = []
    detail_rows = []

    # =========================================================================
    # --- SỬA Ở ĐÂY: Dùng enumerate lấy tham số k đếm từ 0 ---
    for k, seed in enumerate(SEEDS):
        total_distance = run_single_seed(
            input_path=input_path,
            time_limit=time_limit,
            alpha=alpha,
            max_no_improve=max_no_improve,
            reheat_ratio=reheat_ratio,
            seed=seed,
        )
        run_results.append(total_distance)
        
        # --- THÊM VÀO: Đóng gói kết quả cho file asa_detail.csv ---
        detail_rows.append({
            "testcase": testcase_name,
            "alpha": alpha,
            "max_no_improve": max_no_improve,
            "reheat_ratio": reheat_ratio,
            "k": k,
            "cost": total_distance,
        })
    # =========================================================================

    # =========================================================================
    # --- SỬA Ở ĐÂY: Tính toán đồng thời cả cost_min và cost_avg ---
    feasible_results = [cost for cost in run_results if cost >= 0]
    if not feasible_results:
        cost_min = -1
        cost_avg = -1.0
    else:
        cost_min = min(feasible_results)
        cost_avg = round(sum(feasible_results) / len(feasible_results), 2)
    # =========================================================================

    main_row = {
        "testcase": testcase_name,
        "alpha": alpha,
        "max_no_improve": max_no_improve,
        "reheat_ratio": reheat_ratio,
        "cost_min": cost_min,
        "cost_avg": cost_avg, # --- THÊM VÀO: Trường mới ---
    }
    
    return main_row, detail_rows


def build_phase4_tasks(
    selected_testcases: set[str] | None = None,
) -> list[tuple[str, str, float, float, int, float]]:
    """Build independent Phase 4 tasks at testcase/config granularity."""
    tasks = []
    
    # =========================================================================
    # --- SỬA Ở ĐÂY: Sử dụng list cấu hình tốt nhất thay vì hyperparameter_grid ---
    best_configs = load_best_configs()
    # =========================================================================

    for testcase_name, input_path, size_bucket, time_limit in discover_testcases(selected_testcases):
        # =========================================================================
        # --- SỬA Ở ĐÂY: Map testcase bucket vào config chuẩn của nó ---
        if size_bucket not in best_configs:
            print(f"Warning: Không có cấu hình cho {size_bucket}. Bỏ qua testcase {testcase_name}.")
            continue
            
        alpha, max_no_improve, reheat_ratio = best_configs[size_bucket]

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
        # =========================================================================

    return tasks


def run_phase4_task(task: tuple[str, str, float, float, int, float]) -> tuple[dict[str, object], list[dict[str, object]]]:
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


# =========================================================================
# --- SỬA Ở ĐÂY: Viết lại hàm hỗ trợ write header và append song song 2 file ---
def write_csv_headers(main_output_path: str, detail_output_path: str) -> None:
    """Create or overwrite CSV and write header once for both files."""
    os.makedirs(os.path.dirname(main_output_path), exist_ok=True)
    with open(main_output_path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES)
        writer.writeheader()
        stream.flush()

    os.makedirs(os.path.dirname(detail_output_path), exist_ok=True)
    with open(detail_output_path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=DETAIL_FIELDNAMES)
        writer.writeheader()
        stream.flush()


def append_csv_rows(main_output_path: str, detail_output_path: str, main_row: dict, detail_rows: list) -> None:
    """Append one finished row to main file and multiple rows to detail file immediately."""
    with open(main_output_path, "a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES)
        writer.writerow(main_row)
        stream.flush()

    with open(detail_output_path, "a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=DETAIL_FIELDNAMES)
        writer.writerows(detail_rows)
        stream.flush()
# =========================================================================


def execute_phase4(
    selected_testcases: set[str] | None = None,
    output_path: str = DEFAULT_OUTPUT_PATH,
    workers: int = 1,
) -> int:
    """Execute Phase 4 and append rows immediately as tasks finish."""
    tasks = build_phase4_tasks(selected_testcases)
    
    # =========================================================================
    # --- SỬA Ở ĐÂY: Truyền đường dẫn file chi tiết vào hàm ---
    detail_output_path = DETAIL_OUTPUT_PATH
    write_csv_headers(output_path, detail_output_path)
    # =========================================================================

    total_tasks = len(tasks)
    completed = 0

    if workers <= 1:
        for task in tasks:
            main_row, detail_rows = run_phase4_task(task)
            append_csv_rows(output_path, detail_output_path, main_row, detail_rows)
            completed += 1
            print(
                f"[{completed}/{total_tasks}] Appended {main_row['testcase']} | "
                f"alpha={main_row['alpha']} | max_no_improve={main_row['max_no_improve']} | "
                f"reheat_ratio={main_row['reheat_ratio']} | cost_min={main_row['cost_min']} | cost_avg={main_row['cost_avg']}"
            )
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(run_phase4_task, task) for task in tasks]
            for future in as_completed(futures):
                main_row, detail_rows = future.result()
                append_csv_rows(output_path, detail_output_path, main_row, detail_rows)
                completed += 1
                print(
                    f"[{completed}/{total_tasks}] Appended {main_row['testcase']} | "
                    f"alpha={main_row['alpha']} | max_no_improve={main_row['max_no_improve']} | "
                    f"reheat_ratio={main_row['reheat_ratio']} | cost_min={main_row['cost_min']} | cost_avg={main_row['cost_avg']}"
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
    print(f"Wrote {total_rows} rows to {args.output} and detailed results to {DETAIL_OUTPUT_PATH}")


if __name__ == "__main__":
    main()