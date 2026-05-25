"""Aggregate Phase 2 algorithm CSV files into one cost reference CSV."""
import os

from result_aggregator_common import (
    PROJECT_ROOT,
    build_cost_reference_dataframe,
    collect_cost_rows,
)


PHASE2_DIR = os.path.join(PROJECT_ROOT, "results", "phase2")
OUTPUT_CSV = os.path.join(PHASE2_DIR, "cost_reference.csv")
EXCLUDED_FILENAMES = {"cost_reference.csv", "aggregate_result.csv"}


def main() -> None:
    print(f"[*] Scanning Phase 2 results at: {PHASE2_DIR}")

    if not os.path.isdir(PHASE2_DIR):
        raise FileNotFoundError(f"Phase 2 directory not found: {PHASE2_DIR}")

    all_dfs = collect_cost_rows(PHASE2_DIR, excluded_filenames=EXCLUDED_FILENAMES)
    if not all_dfs:
        raise RuntimeError("No valid algorithm CSV files found in results/phase2.")

    final_df = build_cost_reference_dataframe(all_dfs)
    os.makedirs(PHASE2_DIR, exist_ok=True)
    final_df.to_csv(OUTPUT_CSV, index=False)

    print(f"[SUCCESS] Saved cost reference CSV to: {OUTPUT_CSV}")
    print(f"[INFO] Total aggregated testcases: {len(final_df)}")


if __name__ == "__main__":
    main()
