"""Aggregate Phase 4 algorithm CSV files into one cost reference CSV."""
import os
from result_aggregator_common import (
    PROJECT_ROOT,
    build_cost_reference_dataframe,
    collect_cost_rows,
)


PHASE4_DIR = os.path.join(PROJECT_ROOT, "results", "phase4")
OUTPUT_CSV = os.path.join(PHASE4_DIR, "aggregate_result.csv")


def main() -> None:
    print(f"[*] Scanning Phase 4 results at: {PHASE4_DIR}")

    if not os.path.isdir(PHASE4_DIR):
        raise FileNotFoundError(f"Phase 4 directory not found: {PHASE4_DIR}")

    all_dfs = collect_cost_rows(PHASE4_DIR, aggregate_filename="aggregate_result.csv")
    if not all_dfs:
        raise RuntimeError("No valid algorithm CSV files found in results/phase4.")

    final_df = build_cost_reference_dataframe(all_dfs)
    os.makedirs(PHASE4_DIR, exist_ok=True)
    final_df.to_csv(OUTPUT_CSV, index=False)

    print(f"[SUCCESS] Saved aggregate CSV to: {OUTPUT_CSV}")
    print(f"[INFO] Total aggregated testcases: {len(final_df)}")


if __name__ == "__main__":
    main()
