import json
import os
import re
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.settings import TIME_LIMIT_TESTING
from src.solvers.cp_sat.cp_sat import cpsat_solver
from src.solvers.greedy_prunning_pywrapcp.greedy_prunning_pywrapcp import pywrapcp_solver
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


def get_large_testcases() -> list[str]:
    if not os.path.isdir(REPRESENTATIVE_ROOT):
        raise FileNotFoundError(f"Representative root not found: {REPRESENTATIVE_ROOT}")

    testcases = []
    for name in sorted(os.listdir(REPRESENTATIVE_ROOT)):
        testcase_dir = os.path.join(REPRESENTATIVE_ROOT, name)
        if os.path.isdir(testcase_dir) and name.startswith("large_"):
            testcases.append(name)

    if not testcases:
        raise RuntimeError("No large Phase 1 testcases found in results/phase1.")

    return testcases


def get_testcase_info(testcase_name: str) -> tuple[str, float]:
    input_path = os.path.join(VAL_SET_ROOT, f"{testcase_name}.in")
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Missing matching val_set file: {input_path}")

    with open(input_path, encoding="utf-8") as stream:
        _, m, _, _, _ = read_input(stream)

    size_bucket = classify_testcase_size(m)
    time_limit = TIME_LIMIT_TESTING[size_bucket]
    return input_path, time_limit


def build_result_payload(
    algorithm: str,
    route: list[int],
    total_distance: int,
    t_best: float,
    time_limit: float,
) -> dict:
    if algorithm == "cpsat":
        hyperparameters = {"num_search_workers": 4}
    elif algorithm == "pywrapcp":
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


def write_result_json(output_path: str, result: dict) -> None:
    json_str = json.dumps(result, indent=4)
    json_str = re.sub(
        r'("route": \[\s*)(.*?)(\s*\])',
        lambda m: '"route": [' + re.sub(r"\s+", " ", m.group(2)).strip() + "]",
        json_str,
        flags=re.DOTALL,
    )
    with open(output_path, "w", encoding="utf-8") as stream:
        stream.write(json_str)


def run_cpsat(testcase_name: str) -> None:
    input_path, time_limit = get_testcase_info(testcase_name)

    with open(input_path, encoding="utf-8") as stream:
        original_stdin = sys.stdin
        try:
            sys.stdin = stream
            route, total_distance, t_best = cpsat_solver(
                time_limit=time_limit,
                num_search_workers=4,
                log_search_progress=False,
            )
        finally:
            sys.stdin = original_stdin

    result = build_result_payload("cpsat", route, total_distance, t_best, time_limit)
    output_path = os.path.join(REPRESENTATIVE_ROOT, testcase_name, "cpsat.json")
    write_result_json(output_path, result)
    print(f"Wrote results/phase1/{testcase_name}/cpsat.json")


def run_pywrapcp(testcase_name: str) -> None:
    input_path, time_limit = get_testcase_info(testcase_name)

    with open(input_path, encoding="utf-8") as stream:
        original_stdin = sys.stdin
        try:
            sys.stdin = stream
            route, total_distance, t_best = pywrapcp_solver(time_limit=time_limit)
        finally:
            sys.stdin = original_stdin

    result = build_result_payload("pywrapcp", route, total_distance, t_best, time_limit)
    output_path = os.path.join(REPRESENTATIVE_ROOT, testcase_name, "pywrapcp.json")
    write_result_json(output_path, result)
    print(f"Wrote results/phase1/{testcase_name}/pywrapcp.json")


def main() -> None:
    testcases = get_large_testcases()
    for testcase_name in testcases:
        print(f"Running large Phase 1 testcase: {testcase_name}")
        print("CP-SAT is forced to 1 worker to reduce memory pressure on large instances.")
        run_cpsat(testcase_name)
        run_pywrapcp(testcase_name)


if __name__ == "__main__":
    main()
