"""
Build Phase 4 ACO summary CSV from the per-seed detail CSV.
"""
from __future__ import annotations

import csv
import os
import statistics
import sys

# Add project root to sys.path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


PHASE4_ROOT = os.path.join(project_root, "results", "phase4")
DETAIL_PATH = os.path.join(PHASE4_ROOT, "aco_detail.csv")
OUTPUT_PATH = os.path.join(PHASE4_ROOT, "aco.csv")
FIELDNAMES = [
    "testcase",
    "cost_min",
    "cost_max",
    "cost_avg",
    "cost_std",
    "t_best_avg",
]


def sort_key(row: dict[str, object]) -> tuple[str]:
    """Provide stable sorting for the output CSV."""
    return (str(row["testcase"]),)


def main() -> None:
    if not os.path.isfile(DETAIL_PATH):
        raise FileNotFoundError(f"Missing ACO detail file: {DETAIL_PATH}")

    grouped_runs: dict[str, list[tuple[int, float]]] = {}

    with open(DETAIL_PATH, encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fieldnames = reader.fieldnames or []
        if "t_best" not in fieldnames:
            raise RuntimeError(
                f"{DETAIL_PATH} is missing t_best. Re-run src/solvers/ant_colony/phase4.py first."
            )
        for row in reader:
            testcase = row["testcase"]
            cost = int(float(row["cost"]))
            t_best = float(row["t_best"])
            grouped_runs.setdefault(testcase, []).append((cost, t_best))

    rows = []
    for testcase, runs in grouped_runs.items():
        feasible_runs = [(cost, t_best) for cost, t_best in runs if cost >= 0]
        feasible_costs = [cost for cost, _ in feasible_runs]
        feasible_t_bests = [t_best for _, t_best in feasible_runs if t_best >= 0]

        cost_min = min(feasible_costs) if feasible_costs else -1
        cost_max = max(feasible_costs) if feasible_costs else -1
        cost_avg = (sum(feasible_costs) / len(feasible_costs)) if feasible_costs else -1
        cost_std = statistics.pstdev(feasible_costs) if feasible_costs else -1
        t_best_avg = (sum(feasible_t_bests) / len(feasible_t_bests)) if feasible_t_bests else -1
        rows.append(
            {
                "testcase": testcase,
                "cost_min": cost_min,
                "cost_max": cost_max,
                "cost_avg": round(cost_avg, 6),
                "cost_std": round(cost_std, 6),
                "t_best_avg": round(t_best_avg, 6),
            }
        )

    rows.sort(key=sort_key)
    os.makedirs(PHASE4_ROOT, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} summary rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
