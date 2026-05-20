"""
Run all 6 solvers on val_set/small_04_N5_M20.in.

The script:
1. Uses data/val_set/small_04_N5_M20.in by default.
2. Compiles ACO / GA C++ cores if the executables are missing.
3. Runs 6 solvers with one shared time limit.
4. Validates each returned route with evaluator().
5. Prints a compact summary and can optionally save a JSON report.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import subprocess
import sys
from typing import Any, Callable

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.settings import TIME_LIMIT_TESTING
from src.solvers.utils import evaluator, read_input


DEFAULT_INPUT_PATH = os.path.join(project_root, "data", "val_set", "small_04_N5_M20.in")
DEFAULT_OUTPUT_DIR = os.path.join(project_root, "results", "phase1", "small_04_N5_M20")


def load_module(module_name: str, relative_path: str):
    """Load a Python module directly from a file path."""
    module_path = os.path.join(project_root, relative_path)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


greedy_module = load_module("solver_greedy_pkg", os.path.join("src", "solvers", "greedy", "greedy.py"))
pywrapcp_module = load_module(
    "solver_pywrapcp_pkg",
    os.path.join("src", "solvers", "greedy_prunning_pywrapcp", "greedy_prunning_pywrapcp.py"),
)
cpsat_module = load_module("solver_cpsat_pkg", os.path.join("src", "solvers", "cp_sat", "cp_sat.py"))
asa_module = load_module(
    "solver_asa_pkg",
    os.path.join("src", "solvers", "simulated_annealing", "adaptive_simulated_annealing.py"),
)
aco_module = load_module("solver_aco_pkg", os.path.join("src", "solvers", "ant_colony", "aco.py"))
ga_module = load_module("solver_ga_pkg", os.path.join("src", "solvers", "genetic_algorithm", "ga.py"))

greedy_solver = greedy_module.greedy_solver
pywrapcp_solver = pywrapcp_module.pywrapcp_solver
cpsat_solver = cpsat_module.cpsat_solver
asa_solver = asa_module.asa_solver
aco_solver = aco_module.aco_solver
ga_solver = ga_module.ga_solver

ACO_DEFAULT_ALPHA = aco_module.DEFAULT_ALPHA
ACO_DEFAULT_BETA = aco_module.DEFAULT_BETA
ACO_DEFAULT_NUM_ANTS = aco_module.DEFAULT_NUM_ANTS
ACO_DEFAULT_RHO = aco_module.DEFAULT_RHO
GA_DEFAULT_CROSSOVER_RATE = ga_module.DEFAULT_CROSSOVER_RATE
GA_DEFAULT_MUTATION_RATE = ga_module.DEFAULT_MUTATION_RATE
GA_DEFAULT_POP_SIZE = ga_module.DEFAULT_POP_SIZE
ASA_DEFAULT_ALPHA = asa_module.DEFAULT_ALPHA
ASA_DEFAULT_MAX_NO_IMPROVE = asa_module.DEFAULT_MAX_NO_IMPROVE
ASA_DEFAULT_REHEAT_RATIO = asa_module.DEFAULT_REHEAT_RATIO
ASA_DEFAULT_SEED = asa_module.DEFAULT_SEED


def get_executable_path(base_dir: str, stem: str) -> str:
    """Return executable path based on the operating system."""
    if os.name == "nt":
        return os.path.join(base_dir, f"{stem}.exe")
    return os.path.join(base_dir, stem)


def ensure_cpp_binary(source_path: str, executable_stem: str) -> str:
    """Compile a C++ source file if its executable does not exist yet."""
    base_dir = os.path.dirname(source_path)
    executable_path = get_executable_path(base_dir, executable_stem)
    if os.path.exists(executable_path):
        return executable_path

    compile_cmd = [
        "g++",
        "-O2",
        "-std=c++17",
        source_path,
        "-o",
        executable_path,
    ]
    result = subprocess.run(compile_cmd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Failed to compile C++ core.\n"
            f"Command: {' '.join(compile_cmd)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    return executable_path


def ensure_external_binaries() -> None:
    """Compile external C++ binaries required by ACO and GA if needed."""
    ensure_cpp_binary(
        os.path.join(project_root, "src", "solvers", "ant_colony", "aco_core.cpp"),
        "aco_core",
    )
    ensure_cpp_binary(
        os.path.join(project_root, "src", "solvers", "genetic_algorithm", "ga_core.cpp"),
        "ga_core",
    )


def run_solver_with_stdin(
    solver_name: str,
    solver_fn: Callable[..., tuple[list[int], int, float]],
    input_text: str,
    dataset: tuple[int, int, list[list[int]], list[list[int]], list[int]],
    solver_kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Run one solver against the same in-memory input and validate its route."""
    original_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO(input_text)
        route, total_distance, t_best = solver_fn(**solver_kwargs)
    finally:
        sys.stdin = original_stdin

    route = [node for node in route if node != 0]

    n, m, q_matrix, dist_matrix, demand = dataset
    evaluation = evaluator(route, n, m, q_matrix, dist_matrix, demand)

    return {
        "solver": solver_name,
        "route": route,
        "total_distance": total_distance,
        "t_best": t_best,
        "evaluated_distance": evaluation["total_distance"],
        "is_valid": evaluation["is_valid"],
        "is_infeasible": evaluation["is_infeasible"],
        "num_shelves": evaluation["num_shelves"],
        "shortage": evaluation["shortage"][1:],
        "hyperparameters": solver_kwargs,
    }


def build_solver_specs(time_limit: float) -> list[tuple[str, Callable[..., tuple[list[int], int, float]], dict[str, Any]]]:
    """Build the 6 solver calls with their default hyperparameters."""
    return [
        ("greedy", greedy_solver, {"time_limit": time_limit}),
        ("pywrapcp", pywrapcp_solver, {"time_limit": time_limit}),
        ("cpsat", cpsat_solver, {"time_limit": time_limit, "num_search_workers": 0}),
        (
            "asa",
            asa_solver,
            {
                "time_limit": time_limit,
                "alpha": ASA_DEFAULT_ALPHA,
                "max_no_improve": ASA_DEFAULT_MAX_NO_IMPROVE,
                "reheat_ratio": ASA_DEFAULT_REHEAT_RATIO,
                "seed": ASA_DEFAULT_SEED,
            },
        ),
        (
            "aco",
            aco_solver,
            {
                "time_limit": time_limit,
                "num_ants": ACO_DEFAULT_NUM_ANTS,
                "alpha": ACO_DEFAULT_ALPHA,
                "beta": ACO_DEFAULT_BETA,
                "rho": ACO_DEFAULT_RHO,
            },
        ),
        (
            "ga",
            ga_solver,
            {
                "time_limit": time_limit,
                "pop_size": GA_DEFAULT_POP_SIZE,
                "crossover_rate": GA_DEFAULT_CROSSOVER_RATE,
                "mutation_rate": GA_DEFAULT_MUTATION_RATE,
            },
        ),
    ]


def parse_args() -> argparse.Namespace:
    """Parse CLI options."""
    parser = argparse.ArgumentParser(description="Run all 6 solvers on small_04_N5_M20")
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_PATH,
        help="Path to the input testcase. Defaults to data/val_set/small_04_N5_M20.in.",
    )
    parser.add_argument(
        "--time_limit",
        type=float,
        default=TIME_LIMIT_TESTING["small"],
        help="Time limit used for every solver call. Defaults to TIME_LIMIT_TESTING['small'].",
    )
    parser.add_argument(
        "--output_dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write per-solver JSON files.",
    )
    return parser.parse_args()


def print_summary(results: list[dict[str, Any]]) -> None:
    """Print a compact readable summary to stdout."""
    print("solver      cost    eval    valid  shelves  t_best")
    print("----------  ------  ------  -----  -------  --------")
    for item in results:
        print(
            f"{item['solver']:<10}  "
            f"{item['total_distance']:<6}  "
            f"{item['evaluated_distance']:<6}  "
            f"{str(item['is_valid']):<5}  "
            f"{item['num_shelves']:<7}  "
            f"{item['t_best']}"
        )


def build_phase1_payload(result: dict[str, Any], time_limit: float) -> dict[str, Any]:
    """Build payload compatible with current results/phase1 JSON files."""
    solver_name = result["solver"]
    if solver_name == "greedy":
        hyperparameters = {}
    elif solver_name == "pywrapcp":
        hyperparameters = {"local_search_metaheuristic": "GUIDED_LOCAL_SEARCH"}
    elif solver_name == "cpsat":
        hyperparameters = {"num_search_workers": 0}
    elif solver_name == "asa":
        hyperparameters = {
            "alpha": result["hyperparameters"]["alpha"],
            "max_no_improve": result["hyperparameters"]["max_no_improve"],
            "reheat_ratio": result["hyperparameters"]["reheat_ratio"],
        }
    elif solver_name == "aco":
        hyperparameters = {
            "num_ants": result["hyperparameters"]["num_ants"],
            "alpha": result["hyperparameters"]["alpha"],
            "beta": result["hyperparameters"]["beta"],
            "rho": result["hyperparameters"]["rho"],
        }
    elif solver_name == "ga":
        hyperparameters = {
            "pop_size": result["hyperparameters"]["pop_size"],
            "crossover_rate": result["hyperparameters"]["crossover_rate"],
            "mutation_rate": result["hyperparameters"]["mutation_rate"],
        }
    else:
        hyperparameters = result["hyperparameters"]

    return {
        "route": result["route"],
        "total_distance": result["total_distance"],
        "t_best": result["t_best"],
        "time_limit": time_limit,
        "hyperparameters": hyperparameters,
    }


def write_phase1_outputs(results: list[dict[str, Any]], output_dir: str, time_limit: float) -> None:
    """Write one JSON file per solver, overwriting current phase1 outputs."""
    os.makedirs(output_dir, exist_ok=True)

    for result in results:
        output_path = os.path.join(output_dir, f"{result['solver']}.json")
        payload = build_phase1_payload(result, time_limit)
        with open(output_path, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=4)


def main() -> None:
    args = parse_args()
    ensure_external_binaries()

    with open(args.input, encoding="utf-8") as stream:
        input_text = stream.read()

    dataset = read_input(io.StringIO(input_text))
    solver_specs = build_solver_specs(args.time_limit)

    results = []
    for solver_name, solver_fn, solver_kwargs in solver_specs:
        results.append(
            run_solver_with_stdin(
                solver_name=solver_name,
                solver_fn=solver_fn,
                input_text=input_text,
                dataset=dataset,
                solver_kwargs=solver_kwargs,
            )
        )

    write_phase1_outputs(results, args.output_dir, args.time_limit)
    print_summary(results)
    print(f"\nWrote per-solver JSON files to {args.output_dir}")


if __name__ == "__main__":
    main()
