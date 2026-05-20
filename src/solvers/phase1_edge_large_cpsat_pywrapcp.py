"""
Phase 1 runner for:
- CP-SAT on representative edge and large cases
- pywrapcp on representative edge cases

Input files are read from data/val_set and outputs overwrite:
results/phase1/<testcase>/cpsat.json
results/phase1/<testcase>/pywrapcp.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
import traceback


project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import TIME_LIMIT_TESTING
from src.solvers.cp_sat.cp_sat import cpsat_solver
from src.solvers.greedy_prunning_pywrapcp.greedy_prunning_pywrapcp import (
    pywrapcp_solver,
)
from src.solvers.utils import read_input


RESULTS_ROOT = project_root / "results" / "phase1"
VAL_SET_ROOT = project_root / "data" / "val_set"

CP_SAT = "cpsat"
PYWRAPCP = "pywrapcp"


def classify_testcase_size(m: int) -> str:
    """Classify testcase size based on number of shelves."""
    if m <= 20:
        return "small"
    if 50 <= m <= 400:
        return "medium"
    if m >= 500:
        return "large"
    raise ValueError(f"Cannot classify testcase with M={m}.")


def get_phase1_target_testcases() -> list[str]:
    """Return representative Phase 1 cases to run for this script."""
    if not RESULTS_ROOT.is_dir():
        raise FileNotFoundError(f"Missing results directory: {RESULTS_ROOT}")

    testcase_names = []
    for path in sorted(RESULTS_ROOT.iterdir()):
        if not path.is_dir():
            continue
        if path.name.startswith("edge_") or path.name.startswith("large_"):
            testcase_names.append(path.name)

    if not testcase_names:
        raise RuntimeError("No edge/large representative testcases found in results/phase1.")

    return testcase_names


def get_algorithms_for_testcase(testcase_name: str) -> list[str]:
    """Return algorithms required for a representative testcase."""
    if testcase_name.startswith("edge_"):
        return [CP_SAT, PYWRAPCP]
    if testcase_name.startswith("large_"):
        return [CP_SAT]
    raise ValueError(f"Unsupported testcase group for script: {testcase_name}")


def get_testcase_info(testcase_name: str) -> tuple[Path, float]:
    """Resolve matching val_set input and testing time limit."""
    input_path = VAL_SET_ROOT / f"{testcase_name}.in"
    if not input_path.is_file():
        raise FileNotFoundError(f"Missing matching val_set file: {input_path}")

    with input_path.open(encoding="utf-8") as stream:
        _, m, _, _, _ = read_input(stream)

    size_bucket = classify_testcase_size(m)
    time_limit = TIME_LIMIT_TESTING[size_bucket]
    return input_path, time_limit


def run_solver_on_input(input_path: Path, algorithm: str, time_limit: float) -> tuple[list[int], int, float]:
    """Run one solver against one input file through stdin-compatible interface."""
    with input_path.open(encoding="utf-8") as stream:
        original_stdin = sys.stdin
        try:
            sys.stdin = stream
            if algorithm == CP_SAT:
                return cpsat_solver(time_limit=time_limit, num_search_workers=0)
            if algorithm == PYWRAPCP:
                return pywrapcp_solver(time_limit=time_limit)
        finally:
            sys.stdin = original_stdin

    raise ValueError(f"Unsupported algorithm: {algorithm}")


def build_result_payload(
    algorithm: str,
    route: list[int],
    total_distance: int,
    t_best: float,
    time_limit: float,
) -> dict:
    """Build result payload compatible with existing Phase 1 JSON files."""
    hyperparameters: dict[str, str | int]
    if algorithm == CP_SAT:
        hyperparameters = {"num_search_workers": 0}
    elif algorithm == PYWRAPCP:
        hyperparameters = {"local_search_metaheuristic": "GUIDED_LOCAL_SEARCH"}
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    return {
        "route": route,
        "total_distance": total_distance,
        "t_best": t_best,
        "time_limit": time_limit,
        "hyperparameters": hyperparameters,
    }


def write_result_json(output_path: Path, payload: dict) -> None:
    """Write JSON and keep route on one line like current Phase 1 outputs."""
    json_str = json.dumps(payload, indent=4)
    json_str = re.sub(
        r'("route": \[\s*)(.*?)(\s*\])',
        lambda match: '"route": [' + re.sub(r"\s+", " ", match.group(2)).strip() + "]",
        json_str,
        flags=re.DOTALL,
    )
    output_path.write_text(json_str, encoding="utf-8")


def run_single_testcase(testcase_name: str) -> list[Path]:
    """Run all required algorithms for one testcase and overwrite result files."""
    print(f"Running testcase: {testcase_name}")
    input_path, time_limit = get_testcase_info(testcase_name)
    output_dir = RESULTS_ROOT / testcase_name
    output_dir.mkdir(parents=True, exist_ok=True)

    written_files = []
    algorithms = get_algorithms_for_testcase(testcase_name)
    print(f"  Algorithms to run: {', '.join(algorithms)}")
    for algorithm in algorithms:
        print(f"    Running solver: {algorithm}")
        try:
            route, total_distance, t_best = run_solver_on_input(input_path, algorithm, time_limit)
            payload = build_result_payload(algorithm, route, total_distance, t_best, time_limit)
            output_path = output_dir / f"{algorithm}.json"
            write_result_json(output_path, payload)
            written_files.append(output_path)
            print(f"    Successfully finished solver: {algorithm}")
        except SystemExit as e:
            print(f"    ERROR: Solver {algorithm} for {testcase_name} called sys.exit({e.code}).")
            print(traceback.format_exc())
        except Exception as e:
            print(f"    ERROR running solver {algorithm} for {testcase_name}:")
            print(traceback.format_exc())
            # Continue to next algorithm/testcase
    return written_files


def main() -> None:
    for testcase_name in get_phase1_target_testcases():
        written_files = run_single_testcase(testcase_name)
        for output_path in written_files:
            relative_path = output_path.relative_to(project_root).as_posix()
            print(f"Wrote {relative_path}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("An error occurred:")
        print(traceback.format_exc())