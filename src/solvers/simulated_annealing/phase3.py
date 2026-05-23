"""
Phase 3 tuner for Adaptive Simulated Annealing.

Workflow:
1. Run the full ASA hyperparameter grid on the 3 small val_set testcases using
   TIME_LIMITS["small"] and all configured SEEDS.
2. Use the small-case CP-SAT results from Phase 2 as the cost reference to
   compute RFD and pick the best small configuration.
3. Reuse Phase 2 ASA results plus the aggregate reference file to select the
   best configuration for medium and large groups.
4. Save the best configuration per available group to results/phase3/asa.csv.
"""
from __future__ import annotations
import csv
import os
import sys


# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from config.settings import SEEDS, TIME_LIMITS
from src.solvers.simulated_annealing.adaptive_simulated_annealing import asa_solver
from src.solvers.simulated_annealing.phase2 import iter_hyperparameter_grid


PHASE2_ROOT = os.path.join(project_root, "results", "phase2")
PHASE3_ROOT = os.path.join(project_root, "results", "phase3")
VAL_SET_ROOT = os.path.join(project_root, "data", "val_set")

PHASE2_ASA_PATH = os.path.join(PHASE2_ROOT, "asa.csv")
PHASE2_AGGREGATE_PATH = os.path.join(PHASE2_ROOT, "aggregate_result.csv")
DEFAULT_OUTPUT_PATH = os.path.join(PHASE3_ROOT, "asa.csv")

OUTPUT_FIELDNAMES = [
    "alpha",
    "max_no_improve",
    "reheat_ratio",
    "avg_RFD",
    "group",
]

GROUP_PRIORITY = {"small": 0, "medium": 1, "large": 2}


def load_small_references() -> dict[str, int]:
    """Load small-testcase cost references from the Phase 2 aggregate CSV."""
    if not os.path.isfile(PHASE2_AGGREGATE_PATH):
        raise FileNotFoundError(f"Missing Phase 2 aggregate file: {PHASE2_AGGREGATE_PATH}")

    references = {}
    with open(PHASE2_AGGREGATE_PATH, encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            testcase = row["testcase"]
            if row["group"] == "small":
                references[testcase] = int(float(row["cost_reference"]))

    if len(references) != 3:
        raise RuntimeError(
            f"Expected 3 small references in {PHASE2_AGGREGATE_PATH}, found {len(references)}."
        )
    return references


def run_single_small_seed(
    input_path: str,
    time_limit: float,
    alpha: float,
    max_no_improve: int,
    reheat_ratio: float,
    seed: int,
) -> int:
    """Run one ASA configuration on one small testcase and one seed."""
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


def select_best_seed_cost(run_results: list[int]) -> int:
    """Return the minimum feasible run cost, or -1 if all runs are infeasible."""
    feasible_results = [cost for cost in run_results if cost >= 0]
    if not feasible_results:
        return -1
    return min(feasible_results)


def compute_small_avg_rfd() -> dict[tuple[float, int, float, str], float]:
    """Run the small-case tuning loop and compute avg_RFD per configuration for group=small."""
    references = load_small_references()
    time_limit = TIME_LIMITS["small"]
    hyperparameter_grid = iter_hyperparameter_grid()

    avg_rfd_by_key = {}
    total_configs = len(hyperparameter_grid)
    for config_idx, (alpha, max_no_improve, reheat_ratio) in enumerate(hyperparameter_grid, start=1):
        print(
            f"[small {config_idx}/{total_configs}] "
            f"alpha={alpha}, max_no_improve={max_no_improve}, reheat_ratio={reheat_ratio}"
        )
        rfd_values = []
        for testcase, cost_reference in sorted(references.items()):
            input_path = os.path.join(VAL_SET_ROOT, f"{testcase}.in")
            run_costs = []
            for seed in SEEDS:
                run_costs.append(
                    run_single_small_seed(
                        input_path=input_path,
                        time_limit=time_limit,
                        alpha=alpha,
                        max_no_improve=max_no_improve,
                        reheat_ratio=reheat_ratio,
                        seed=seed,
                    )
                )

            cost_min = select_best_seed_cost(run_costs)
            if cost_min <= 0 or cost_reference <= 0:
                rfd_values.append(0.0)
            else:
                rfd_values.append(((cost_min - cost_reference) / cost_reference) * 100.0)

        key = (alpha, max_no_improve, reheat_ratio, "small")
        avg_rfd_by_key[key] = sum(rfd_values) / len(rfd_values)

    return avg_rfd_by_key


def load_phase2_references() -> dict[str, tuple[int, str]]:
    """Load testcase -> (cost_reference, group) from the Phase 2 aggregate CSV."""
    if not os.path.isfile(PHASE2_AGGREGATE_PATH):
        raise FileNotFoundError(f"Missing Phase 2 aggregate file: {PHASE2_AGGREGATE_PATH}")

    references = {}
    with open(PHASE2_AGGREGATE_PATH, encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            references[row["testcase"]] = (int(float(row["cost_reference"])), row["group"])

    if not references:
        raise RuntimeError("Phase 2 aggregate file is empty.")
    return references


def compute_phase2_grouped_avg_rfd(
    references: dict[str, tuple[int, str]],
) -> dict[tuple[float, int, float, str], float]:
    """
    Compute avg_RFD per (configuration, group) from the existing Phase 2 ASA output.

    Only non-small groups are used here because small is re-tuned directly in this script.
    If either cost_min or cost_reference is non-positive, RFD is treated as 0.
    This matches the current dataset convention where the infeasible testcase
    yields -1 for all algorithms and should not penalize any configuration.
    """
    if not os.path.isfile(PHASE2_ASA_PATH):
        raise FileNotFoundError(f"Missing Phase 2 ASA file: {PHASE2_ASA_PATH}")

    sums: dict[tuple[float, int, float, str], float] = {}
    counts: dict[tuple[float, int, float, str], int] = {}

    with open(PHASE2_ASA_PATH, encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            testcase = row["testcase"]
            if testcase not in references:
                continue

            cost_reference, group = references[testcase]
            if group == "small":
                continue

            alpha = float(row["alpha"])
            max_no_improve = int(row["max_no_improve"])
            reheat_ratio = float(row["reheat_ratio"])
            cost_min = int(float(row["cost_min"]))
            key = (alpha, max_no_improve, reheat_ratio, group)

            if cost_min <= 0 or cost_reference <= 0:
                rfd_value = 0.0
            else:
                rfd_value = ((cost_min - cost_reference) / cost_reference) * 100.0

            sums[key] = sums.get(key, 0.0) + rfd_value
            counts[key] = counts.get(key, 0) + 1

    if not sums:
        raise RuntimeError("No valid ASA Phase 2 rows were found for medium/large Phase 3 aggregation.")

    avg_rfd_by_key = {}
    for key, total_rfd in sums.items():
        avg_rfd_by_key[key] = total_rfd / counts[key]

    return avg_rfd_by_key


def select_best_config_per_group(
    avg_rfd_by_key: dict[tuple[float, int, float, str], float]
) -> list[dict[str, object]]:
    """Select the minimum avg_RFD configuration for each available group."""
    best_rows_by_group: dict[str, dict[str, object]] = {}

    for (alpha, max_no_improve, reheat_ratio, group), avg_rfd in avg_rfd_by_key.items():
        candidate = {
            "alpha": alpha,
            "max_no_improve": max_no_improve,
            "reheat_ratio": reheat_ratio,
            "avg_RFD": round(avg_rfd, 6),
            "group": group,
        }

        current_best = best_rows_by_group.get(group)
        if current_best is None:
            best_rows_by_group[group] = candidate
            continue

        candidate_key = (avg_rfd, alpha, max_no_improve, reheat_ratio)
        current_key = (
            float(current_best["avg_RFD"]),
            float(current_best["alpha"]),
            int(current_best["max_no_improve"]),
            float(current_best["reheat_ratio"]),
        )
        if candidate_key < current_key:
            best_rows_by_group[group] = candidate

    return sorted(best_rows_by_group.values(), key=lambda row: GROUP_PRIORITY.get(row["group"], 99))


def write_phase3_csv(rows: list[dict[str, object]], output_path: str = DEFAULT_OUTPUT_PATH) -> None:
    """Write the best ASA configuration per group to Phase 3 CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    small_avg_rfd = compute_small_avg_rfd()
    phase2_references = load_phase2_references()
    medium_large_avg_rfd = compute_phase2_grouped_avg_rfd(phase2_references)

    merged_avg_rfd = {}
    merged_avg_rfd.update(small_avg_rfd)
    merged_avg_rfd.update(medium_large_avg_rfd)

    rows = select_best_config_per_group(merged_avg_rfd)
    write_phase3_csv(rows, DEFAULT_OUTPUT_PATH)
    print(f"Wrote {len(rows)} rows to {DEFAULT_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
