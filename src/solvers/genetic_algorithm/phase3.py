"""
Phase 3 tuner for Genetic Algorithm.

Workflow:
1. Re-run the full GA hyperparameter grid on the small val_set testcases,
   because Phase 2 GA skips small instances.
2. Use the Phase 2 aggregate cost references as testcase-level min-cost baselines.
3. For each testcase/configuration, compute:
   RPD% = ((cost_avg - cost_reference) / cost_reference) * 100
4. Average testcase-level RPD% values within each size group.
5. Select the minimum-RPD% configuration per group and save it to
   results/phase3/ga.csv.
"""
from __future__ import annotations

import csv
import os
import sys

# Add project root to sys.path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.settings import SEEDS, TIME_LIMITS
from src.solvers.genetic_algorithm.ga import ga_solver
from src.solvers.genetic_algorithm.phase2 import iter_hyperparameter_grid


PHASE2_ROOT = os.path.join(project_root, "results", "phase2")
PHASE3_ROOT = os.path.join(project_root, "results", "phase3")
VAL_SET_ROOT = os.path.join(project_root, "data", "val_set")

PHASE2_GA_PATH = os.path.join(PHASE2_ROOT, "ga.csv")
PHASE2_AGGREGATE_PATH = os.path.join(PHASE2_ROOT, "aggregate_result.csv")
DEFAULT_OUTPUT_PATH = os.path.join(PHASE3_ROOT, "ga.csv")

OUTPUT_FIELDNAMES = [
    "pop_size",
    "crossover_rate",
    "mutation_rate",
    "avg_RPD",
    "group",
]

GROUP_PRIORITY = {"small": 0, "medium": 1, "large": 2}


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


def load_small_references(references: dict[str, tuple[int, str]]) -> dict[str, int]:
    """Extract small-testcase references from the Phase 2 aggregate mapping."""
    small_references = {
        testcase: cost_reference
        for testcase, (cost_reference, group) in references.items()
        if group == "small"
    }
    if len(small_references) != 3:
        raise RuntimeError(
            f"Expected 3 small references in {PHASE2_AGGREGATE_PATH}, found {len(small_references)}."
        )
    return small_references


def run_single_small_seed(
    input_path: str,
    time_limit: float,
    pop_size: int,
    crossover_rate: float,
    mutation_rate: float,
    seed: int,
) -> int:
    """Run one GA configuration on one small testcase and one seed."""
    with open(input_path, encoding="utf-8") as stream:
        original_stdin = sys.stdin
        try:
            sys.stdin = stream
            _, total_distance, _ = ga_solver(
                time_limit=time_limit,
                pop_size=pop_size,
                crossover_rate=crossover_rate,
                mutation_rate=mutation_rate,
                seed=seed,
            )
        finally:
            sys.stdin = original_stdin

    return total_distance


def compute_feasible_average_cost(run_costs: list[int]) -> float:
    """Return the average feasible cost, or -1 if all runs are infeasible."""
    feasible_costs = [cost for cost in run_costs if cost >= 0]
    if not feasible_costs:
        return -1
    return sum(feasible_costs) / len(feasible_costs)


def compute_rpd_percent(cost_avg: float, cost_reference: int) -> float:
    """Compute RPD in percent."""
    return ((cost_avg - cost_reference) / cost_reference) * 100.0


def compute_small_avg_rpd(
    references: dict[str, tuple[int, str]]
) -> dict[tuple[int, float, float, str], float]:
    """Run the small-case tuning loop and compute group-mean RPD% for small."""
    small_references = load_small_references(references)
    time_limit = TIME_LIMITS["small"]
    avg_rpd_by_key = {}
    hyperparameter_grid = iter_hyperparameter_grid()
    total_configs = len(hyperparameter_grid)

    for config_idx, (pop_size, crossover_rate, mutation_rate) in enumerate(hyperparameter_grid, start=1):
        print(
            f"[GA small {config_idx}/{total_configs}] "
            f"pop_size={pop_size}, crossover_rate={crossover_rate}, mutation_rate={mutation_rate}"
        )
        rpd_values = []
        for testcase, cost_reference in sorted(small_references.items()):
            if cost_reference <= 0:
                continue

            input_path = os.path.join(VAL_SET_ROOT, f"{testcase}.in")
            run_costs = [
                run_single_small_seed(
                    input_path=input_path,
                    time_limit=time_limit,
                    pop_size=pop_size,
                    crossover_rate=crossover_rate,
                    mutation_rate=mutation_rate,
                    seed=seed,
                )
                for seed in SEEDS
            ]

            cost_avg = compute_feasible_average_cost(run_costs)
            rpd_values.append(float("inf") if cost_avg <= 0 else compute_rpd_percent(cost_avg, cost_reference))

        if not rpd_values:
            continue

        avg_rpd_by_key[(pop_size, crossover_rate, mutation_rate, "small")] = sum(rpd_values) / len(rpd_values)

    return avg_rpd_by_key


def compute_phase2_grouped_avg_rpd(
    references: dict[str, tuple[int, str]],
) -> dict[tuple[int, float, float, str], float]:
    """Compute avg_RPD% per (configuration, group) from the Phase 2 GA summary CSV."""
    if not os.path.isfile(PHASE2_GA_PATH):
        raise FileNotFoundError(f"Missing Phase 2 GA file: {PHASE2_GA_PATH}")

    sums: dict[tuple[int, float, float, str], float] = {}
    counts: dict[tuple[int, float, float, str], int] = {}

    with open(PHASE2_GA_PATH, encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            testcase = row["testcase"]
            reference_entry = references.get(testcase)
            if reference_entry is None:
                continue

            cost_reference, group = reference_entry
            if group == "small" or cost_reference <= 0:
                continue

            pop_size = int(row["pop_size"])
            crossover_rate = float(row["crossover_rate"])
            mutation_rate = float(row["mutation_rate"])
            cost_avg = float(row["cost_avg"])
            key = (pop_size, crossover_rate, mutation_rate, group)

            rpd_value = float("inf") if cost_avg <= 0 else compute_rpd_percent(cost_avg, cost_reference)
            sums[key] = sums.get(key, 0.0) + rpd_value
            counts[key] = counts.get(key, 0) + 1

    if not sums:
        raise RuntimeError("No valid GA Phase 2 rows were found for medium/large Phase 3 aggregation.")

    return {key: sums[key] / counts[key] for key in sums}


def select_best_config_per_group(
    avg_rpd_by_key: dict[tuple[int, float, float, str], float]
) -> list[dict[str, object]]:
    """Select the minimum avg_RPD configuration for each available group."""
    best_rows_by_group: dict[str, dict[str, object]] = {}

    for (pop_size, crossover_rate, mutation_rate, group), avg_rpd in avg_rpd_by_key.items():
        candidate = {
            "pop_size": pop_size,
            "crossover_rate": crossover_rate,
            "mutation_rate": mutation_rate,
            "avg_RPD": round(avg_rpd, 2),
            "group": group,
        }

        current_best = best_rows_by_group.get(group)
        if current_best is None:
            best_rows_by_group[group] = candidate
            continue

        candidate_key = (avg_rpd, pop_size, crossover_rate, mutation_rate)
        current_key = (
            float(current_best["avg_RPD"]),
            int(current_best["pop_size"]),
            float(current_best["crossover_rate"]),
            float(current_best["mutation_rate"]),
        )
        if candidate_key < current_key:
            best_rows_by_group[group] = candidate

    return sorted(best_rows_by_group.values(), key=lambda row: GROUP_PRIORITY.get(row["group"], 99))


def write_phase3_csv(rows: list[dict[str, object]], output_path: str = DEFAULT_OUTPUT_PATH) -> None:
    """Write the best GA configuration per group to Phase 3 CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    references = load_phase2_references()
    small_avg_rpd = compute_small_avg_rpd(references)
    medium_large_avg_rpd = compute_phase2_grouped_avg_rpd(references)

    merged_avg_rpd = {}
    merged_avg_rpd.update(small_avg_rpd)
    merged_avg_rpd.update(medium_large_avg_rpd)

    rows = select_best_config_per_group(merged_avg_rpd)
    write_phase3_csv(rows, DEFAULT_OUTPUT_PATH)
    print(f"Wrote {len(rows)} rows to {DEFAULT_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
