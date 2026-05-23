"""
Build Phase 2 ASA summary CSV from the per-seed detail CSV.
"""
from __future__ import annotations

import csv
import os
import sys

# Add project root to sys.path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


PHASE2_ROOT = os.path.join(project_root, "results", "phase2")
DETAIL_PATH = os.path.join(PHASE2_ROOT, "asa_detail.csv")
OUTPUT_PATH = os.path.join(PHASE2_ROOT, "asa.csv")
FIELDNAMES = [
    "testcase",
    "alpha",
    "max_no_improve",
    "reheat_ratio",
    "cost_min",
    "cost_avg",
]


def sort_key(row: dict[str, object]) -> tuple[str, float, int, float]:
    """Provide stable sorting for the output CSV."""
    return (
        str(row["testcase"]),
        float(row["alpha"]),
        int(row["max_no_improve"]),
        float(row["reheat_ratio"]),
    )


def main() -> None:
    if not os.path.isfile(DETAIL_PATH):
        raise FileNotFoundError(f"Missing ASA detail file: {DETAIL_PATH}")

    grouped_costs: dict[tuple[str, float, int, float], list[int]] = {}

    with open(DETAIL_PATH, encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            key = (
                row["testcase"],
                float(row["alpha"]),
                int(row["max_no_improve"]),
                float(row["reheat_ratio"]),
            )
            grouped_costs.setdefault(key, []).append(int(float(row["cost"])))

    rows = []
    for (testcase, alpha, max_no_improve, reheat_ratio), costs in grouped_costs.items():
        feasible_costs = [cost for cost in costs if cost >= 0]
        cost_min = min(feasible_costs) if feasible_costs else -1
        cost_avg = (sum(feasible_costs) / len(feasible_costs)) if feasible_costs else -1
        rows.append(
            {
                "testcase": testcase,
                "alpha": alpha,
                "max_no_improve": max_no_improve,
                "reheat_ratio": reheat_ratio,
                "cost_min": cost_min,
                "cost_avg": round(cost_avg, 6),
            }
        )

    rows.sort(key=sort_key)
    os.makedirs(PHASE2_ROOT, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} summary rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
